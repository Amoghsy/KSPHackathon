import { useEffect, useState, useRef, useCallback } from "react";
import { ENV } from "../config/environment";

export type SpeechLanguage = "en-IN" | "kn-IN";

// Mock voice structure to keep the UI's voice dropdown functional and system-independent
export const GTTS_VOICES = [
  { name: "Google Translate English (en-IN)", lang: "en-IN", default: true, voiceURI: "gtts-en-in", localService: false },
  { name: "Google Translate Kannada (kn-IN)", lang: "kn-IN", default: false, voiceURI: "gtts-kn-in", localService: false }
] as unknown as SpeechSynthesisVoice[];

export function useSpeechSynthesis() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [lastText, setLastText] = useState("");

  // Persisted settings
  const [rate, setRateState] = useState<number>(() => {
    const saved = localStorage.getItem("scrb-tts-rate");
    return saved ? parseFloat(saved) : 1.0;
  });
  const [pitch, setPitchState] = useState<number>(() => {
    const saved = localStorage.getItem("scrb-tts-pitch");
    return saved ? parseFloat(saved) : 1.0;
  });
  const [volume, setVolumeState] = useState<number>(() => {
    const saved = localStorage.getItem("scrb-tts-volume");
    return saved ? parseFloat(saved) : 1.0;
  });
  const [language, setLanguageState] = useState<SpeechLanguage>(() => {
    const saved = localStorage.getItem("scrb-tts-language") as SpeechLanguage;
    return saved && ["en-IN", "kn-IN"].includes(saved) ? saved : "en-IN";
  });
  const [autoSpeak, setAutoSpeakState] = useState<boolean>(() => {
    const saved = localStorage.getItem("scrb-tts-autospeak");
    return saved ? saved === "true" : true;
  });

  const [selectedVoice, setSelectedVoiceState] = useState<SpeechSynthesisVoice | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Sync selected voice on language or initial load
  useEffect(() => {
    const langCode = language.split("-")[0].toLowerCase();
    const voice = GTTS_VOICES.find(v => v.lang.toLowerCase().startsWith(langCode)) || GTTS_VOICES[0];
    setSelectedVoiceState(voice);
  }, [language]);

  // Persist handlers
  const updateRate = (newRate: number) => {
    setRateState(newRate);
    localStorage.setItem("scrb-tts-rate", newRate.toString());
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate;
    }
  };

  const updatePitch = (newPitch: number) => {
    setPitchState(newPitch);
    localStorage.setItem("scrb-tts-pitch", newPitch.toString());
    // Note: pitch shifting is not natively supported by HTML5 Audio directly without Web Audio API,
    // so we keep the slider in UI, but ignore active effect.
  };

  const updateVolume = (newVolume: number) => {
    setVolumeState(newVolume);
    localStorage.setItem("scrb-tts-volume", newVolume.toString());
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const updateLanguage = (newLang: SpeechLanguage) => {
    setLanguageState(newLang);
    localStorage.setItem("scrb-tts-language", newLang);
  };

  const updateAutoSpeak = (val: boolean) => {
    setAutoSpeakState(val);
    localStorage.setItem("scrb-tts-autospeak", val.toString());
  };

  const updateVoice = (voice: SpeechSynthesisVoice | null) => {
    setSelectedVoiceState(voice);
    if (voice) {
      const newLang = voice.lang as SpeechLanguage;
      updateLanguage(newLang);
    }
  };

  // Clean up playback on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlaying(false);
    setIsPaused(false);
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPaused(true);
    }
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play().catch(err => {
        console.error("Failed to resume playback:", err);
      });
      setIsPaused(false);
      setIsPlaying(true);
    }
  }, []);

  const speak = useCallback((text: string, forceLang?: SpeechLanguage) => {
    if (!text) return;

    // 1. Stop active audio
    stop();
    setLastText(text);

    // 2. Clean text: strip markdown formatting ONLY — preserve digits, letters and natural punctuation.
    // Numbers, IPC sections, accused IDs etc. must reach the backend intact so they can be
    // converted to Kannada words or spoken in English by the mixed-language TTS pipeline.
    const cleanText = text
      .replace(/[*#`_[\]()\->+!]/g, "")  // markdown syntax only
      .replace(/\s+/g, " ")
      .trim();

    if (!cleanText) return;

    // 3. Detect Kannada characters
    const hasKannada = /[\u0C80-\u0CFF]/.test(cleanText);
    const detectedLang: SpeechLanguage = forceLang || (hasKannada ? "kn-IN" : "en-IN");

    // Sync selected language state
    updateLanguage(detectedLang);

    // 4. Construct Backend TTS URL
    const langCode = detectedLang.split("-")[0].toLowerCase();
    const backendUrl = `${ENV.API_BASE_URL}/chat/tts?text=${encodeURIComponent(cleanText)}&lang=${langCode}`;

    // 5. Initialize Audio element
    const audio = new Audio(backendUrl);
    audioRef.current = audio;

    // Apply speed and volume parameters
    audio.volume = volume;
    audio.playbackRate = rate;

    // Wire up events
    audio.onplay = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    audio.onpause = () => {
      setIsPaused(true);
    };

    audio.onended = () => {
      setIsPlaying(false);
      setIsPaused(false);
      audioRef.current = null;
    };

    audio.onerror = (e) => {
      console.error("Audio streaming error:", e);
      setIsPlaying(false);
      setIsPaused(false);
      audioRef.current = null;
    };

    audio.play().catch(err => {
      console.error("Audio playback execution failed:", err);
      setIsPlaying(false);
      setIsPaused(false);
      audioRef.current = null;
    });
  }, [volume, rate, stop]);

  const replay = useCallback(() => {
    if (lastText) {
      speak(lastText);
    }
  }, [lastText, speak]);

  const filteredVoices = GTTS_VOICES.filter(v => {
    const langCode = language.split("-")[0].toLowerCase();
    return v.lang.toLowerCase().startsWith(langCode);
  });

  return {
    voices: GTTS_VOICES,
    filteredVoices,
    selectedVoice,
    isPlaying,
    isPaused,
    rate,
    pitch,
    volume,
    language,
    autoSpeak,
    speak,
    pause,
    resume,
    stop,
    replay,
    setRate: updateRate,
    setPitch: updatePitch,
    setVolume: updateVolume,
    setLanguage: updateLanguage,
    setAutoSpeak: updateAutoSpeak,
    setSelectedVoice: updateVoice,
  };
}
