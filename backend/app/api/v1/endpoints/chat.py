"""
app/api/v1/endpoints/chat.py — POST /api/v1/chat endpoint.

Thin HTTP adapter — all business logic lives in chat_service.

Architecture:
    FastAPI Route → Chat Service → Orchestrator → Query Agent → Response
"""

from __future__ import annotations

import logging
import re
import uuid

from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
try:
    from gtts import gTTS
except ImportError:
    gTTS = None  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, oauth2_scheme
from app.db.session import get_db
from app.schemas.chat import ChatErrorResponse, ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Number-to-Kannada-word mapping ──────────────────────────────────────────
# gTTS with lang=kn skips English digits entirely. We convert numbers to
# their Kannada spoken equivalents before sending to the TTS engine.

_KN_ONES = [
    "", "ಒಂದು", "ಎರಡು", "ಮೂರು", "ನಾಲ್ಕು", "ಐದು",
    "ಆರು", "ಏಳು", "ಎಂಟು", "ಒಂಬತ್ತು",
]
_KN_TENS = [
    "", "ಹತ್ತು", "ಇಪ್ಪತ್ತು", "ಮೂವತ್ತು", "ನಲವತ್ತು",
    "ಐವತ್ತು", "ಅರವತ್ತು", "ಎಪ್ಪತ್ತು", "ಎಂಬತ್ತು", "ತೊಂಬತ್ತು",
]


def _int_to_kn(n: int) -> str:
    """Convert a non-negative integer to its Kannada spoken form."""
    if n == 0:
        return "ಸೊನ್ನೆ"
    if n < 0:
        return "ಋಣ " + _int_to_kn(-n)

    parts: list[str] = []

    if n >= 10_000_000:
        parts.append(_int_to_kn(n // 10_000_000) + " ಕೋಟಿ")
        n %= 10_000_000
    if n >= 100_000:
        parts.append(_int_to_kn(n // 100_000) + " ಲಕ್ಷ")
        n %= 100_000
    if n >= 1_000:
        parts.append(_int_to_kn(n // 1_000) + " ಸಾವಿರ")
        n %= 1_000
    if n >= 100:
        parts.append(_KN_ONES[n // 100] + " ನೂರು")
        n %= 100
    if n >= 10:
        word = _KN_TENS[n // 10]
        if n % 10:
            word += " " + _KN_ONES[n % 10]
        parts.append(word)
    elif n > 0:
        parts.append(_KN_ONES[n])

    return " ".join(parts)


def _number_token_to_kn(token: str) -> str:
    """
    Convert a numeric token to Kannada words.

    Handles:
      - Plain integers:  '302'  → 'ಮೂರು ನೂರು ಎರಡು'
      - Decimals:       '12.5'  → 'ಹನ್ನೆರಡು ಪಾಯಿಂಟ್ ಐದು'
      - Percentages:    '45%'   → 'ನಲವತ್ತು ಐದು ಪ್ರತಿಶತ'
      - Mixed IDs:      'A12'   → 'ಎ ಹನ್ನೆರಡು'
    """
    token = token.strip()

    # Percentage
    if token.endswith("%"):
        inner = token[:-1]
        try:
            return _int_to_kn(int(inner)) + " ಪ್ರತಿಶತ"
        except ValueError:
            pass

    # Decimal
    if "." in token:
        parts = token.split(".", 1)
        try:
            int_kn = _int_to_kn(int(parts[0]))
            frac_kn = " ".join(
                _KN_ONES[int(d)] if d.isdigit() and int(d) < 10 else d
                for d in parts[1]
            )
            return int_kn + " ಪಾಯಿಂಟ್ " + frac_kn
        except (ValueError, IndexError):
            pass

    # Plain integer
    try:
        return _int_to_kn(int(token.replace(",", "")))
    except ValueError:
        pass

    # Mixed alphanumeric (e.g. "A12", "IPC302") — spell out char by char
    result: list[str] = []
    for ch in token:
        if ch.isdigit():
            result.append(_KN_ONES[int(ch)] if int(ch) < 10 else _int_to_kn(int(ch)))
        elif ch.isalpha():
            result.append(ch.upper())   # keep English letter — spoken by en-TTS later
        # Skip commas, dashes, etc.
    return " ".join(result)


# ─── Text segmentation for mixed Kannada + English ────────────────────────────

# Matches one "run" of text that should be handled as a unit
_SEGMENT_RE = re.compile(
    r"([\u0C80-\u0CFF\u200C\u200D][^\x00-\x7F]*)"   # Kannada (non-ASCII run)
    r"|([A-Za-z][A-Za-z\s',;:!?]*)"                 # English word run
    r"|(\d[\d,._%-]*%?)"                             # Numeric token
    r"|([^\x00-\x7F]+)"                              # Other non-ASCII (treat as Kannada)
)


def _segment_mixed_text(text: str) -> list[tuple[str, str]]:
    """
    Split *text* into ordered segments, each tagged with a language hint:
      "kn"  — Kannada script → gTTS(lang="kn")
      "en"  — English words  → gTTS(lang="en")
      "num" — Numeric token  → convert to Kannada words, then gTTS(lang="kn")
    """
    segments: list[tuple[str, str]] = []
    pos = 0

    for m in _SEGMENT_RE.finditer(text):
        # Attach any gap (punctuation / spaces) to the previous segment
        gap = text[pos : m.start()].strip()
        if gap and segments:
            segments[-1] = (segments[-1][0] + " " + gap, segments[-1][1])

        kn_run, en_run, num_run, other_run = m.groups()

        if kn_run:
            segments.append((kn_run.strip(), "kn"))
        elif en_run:
            segments.append((en_run.strip(), "en"))
        elif num_run:
            segments.append((num_run.strip(), "num"))
        elif other_run:
            segments.append((other_run.strip(), "kn"))

        pos = m.end()

    # Trailing text
    trailing = text[pos:].strip()
    if trailing:
        if segments:
            segments[-1] = (segments[-1][0] + " " + trailing, segments[-1][1])
        else:
            segments.append((trailing, "kn"))

    # Merge adjacent same-language segments to minimise gTTS calls
    merged: list[tuple[str, str]] = []
    for content, lang in segments:
        if not content.strip():
            continue
        if merged and merged[-1][1] == lang:
            merged[-1] = (merged[-1][0] + " " + content, lang)
        else:
            merged.append((content, lang))

    return merged


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_markdown(text: str) -> str:
    """
    Strip markdown syntax characters while preserving digits, letters and
    natural punctuation.

    The previous regex stripped \\d+ which caused numbers to vanish from
    speech. This version only removes formatting tokens.
    """
    # Remove markdown formatting characters only
    text = re.sub(r"[*#`_\[\]()\->+!]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _synthesize_segment(content: str, lang: str) -> bytes:
    """Synthesize one text segment and return raw MP3 bytes."""
    if gTTS is None:
        raise RuntimeError(
            "gTTS (Google Text-to-Speech) library is not installed or failed to load. "
            "Please verify that the backend is running inside the virtual environment (.venv) "
            "where dependencies are installed, or install the gtts library: pip install gtts"
        )
    tts = gTTS(text=content, lang=lang, slow=False)
    buf = BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()


def _concat_mp3(chunks: list[bytes]) -> BytesIO:
    """
    Naively concatenate MP3 frames.
    gTTS output consists of valid MPEG frames so simple byte-concatenation
    plays correctly in all browsers / HTML <audio> elements.
    """
    out = BytesIO()
    for chunk in chunks:
        out.write(chunk)
    out.seek(0)
    return out


# ─── API Routes ───────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse | ChatErrorResponse,
    summary="Ask a natural-language question",
    description=(
        "Converts a natural-language question into SQL, executes it against "
        "the SCRB database, and returns a structured response with a "
        "natural-language summary."
    ),
    responses={
        200: {
            "description": "Successful query — may also contain structured errors in the body.",
            "model": ChatResponse,
        },
        422: {"description": "Validation error — invalid request body."},
        500: {"description": "Internal server error."},
    },
)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Accept a natural-language question and return AI-powered analytics.

    Pipeline:
    1. Generate SQL from the question (Gemini)
    2. Validate the SQL (safety + schema)
    3. Execute against PostgreSQL
    4. Summarise results (Gemini)
    5. Return structured response with confidence score
    """
    request_id = str(uuid.uuid4())

    logger.info(
        "Chat request  request_id=%s  question=%.200s",
        request_id,
        request.question,
    )

    user_id = current_user.get("id")

    try:
        response = await handle_chat(
            question=request.question,
            session=db,
            conversation_id=request.conversation_id,
            request_id=request_id,
            user_id=user_id,
            current_user=current_user,
            response_language=request.response_language,
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat endpoint unhandled error: %s", exc)
        return {
            "status": "error",
            "request_id": request_id,
            "error": "An unexpected error occurred. Please try again.",
            "error_type": "internal_error",
            "retryable": True,
        }

    return response


@router.get(
    "/tts",
    summary="Text-to-speech engine",
    description=(
        "Synthesizes text into MP3 audio and streams it. "
        "For Kannada (lang=kn), mixed English words and numbers are automatically "
        "handled — numbers become Kannada words, English segments are spoken "
        "in English and stitched into the same audio stream."
    ),
)
async def tts_endpoint(text: str, lang: str = "en"):
    """
    Synthesize natural-language text into speech.

    Mixed Kannada+English text (lang=kn):
    ┌─────────────────┬──────────────────────────────────────────────┐
    │ Segment type    │ Handling                                     │
    ├─────────────────┼──────────────────────────────────────────────┤
    │ Kannada script  │ gTTS(lang="kn")                              │
    │ English words   │ gTTS(lang="en") — natural English accent     │
    │ Numbers/digits  │ Converted to Kannada words → gTTS(lang="kn")│
    └─────────────────┴──────────────────────────────────────────────┘
    All segments are concatenated into a single MP3 stream.
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text parameter is required.")

    lang = lang.lower().strip()
    if lang not in ("en", "kn"):
        lang = "en"

    clean = _clean_markdown(text)
    if not clean:
        clean = text.strip()

    logger.debug("TTS request  lang=%s  len=%d  preview=%.80s", lang, len(clean), clean)

    try:
        from fastapi.concurrency import run_in_threadpool

        def generate_audio() -> BytesIO:
            # ── Pure English ─────────────────────────────────────────────────
            if lang == "en":
                return BytesIO(_synthesize_segment(clean, "en"))

            # ── Kannada: segment → per-segment TTS → stitch ──────────────────
            segments = _segment_mixed_text(clean)
            logger.debug("TTS segments (%d): %s", len(segments), segments)

            chunks: list[bytes] = []

            for content, hint in segments:
                content = content.strip()
                if not content:
                    continue

                if hint == "num":
                    # Convert to Kannada words, speak as Kannada
                    kn_words = _number_token_to_kn(content)
                    logger.debug("  num '%s' → '%s'", content, kn_words)
                    if kn_words.strip():
                        chunks.append(_synthesize_segment(kn_words, "kn"))

                elif hint == "en":
                    # English segment — speak in English
                    logger.debug("  en  '%s'", content)
                    chunks.append(_synthesize_segment(content, "en"))

                else:
                    # Kannada segment — replace any stray inline digits
                    processed = re.sub(
                        r"\d[\d,._%-]*%?",
                        lambda m: _number_token_to_kn(m.group()),
                        content,
                    )
                    logger.debug("  kn  '%s'", processed)
                    if processed.strip():
                        chunks.append(_synthesize_segment(processed, "kn"))

            if not chunks:
                chunks.append(_synthesize_segment(clean, "kn"))

            return _concat_mp3(chunks)

        audio_file = await run_in_threadpool(generate_audio)

        return StreamingResponse(
            audio_file,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )

    except Exception as exc:
        logger.exception("TTS generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {exc}")
