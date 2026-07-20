import secrets
import hashlib
import json
import time
import logging
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self):
        self.redis = get_redis_client()
        self.otp_expiry = 300  # 5 minutes
        self.max_attempts = 5
        self.cooldown = 60  # 60 seconds

    def _hash_otp(self, otp: str) -> str:
        """Hash the OTP code using SHA-256."""
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    async def generate_otp(self, user_id: int) -> dict:
        """
        Generate a cryptographically secure 6-digit OTP and store it in Redis.
        Returns challenge metadata and the raw OTP code (to be emailed).
        """
        # Generate 6-digit code
        otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
        challenge_id = secrets.token_urlsafe(32)
        hashed_otp = self._hash_otp(otp_code)

        data = {
            "user_id": user_id,
            "hashed_otp": hashed_otp,
            "expires_at": time.time() + self.otp_expiry,
            "attempt_count": 0,
            "last_sent_at": time.time(),
        }

        # Store in Redis with 5-minute TTL
        key = f"auth:otp:{challenge_id}"
        await self.redis.setex(key, self.otp_expiry, json.dumps(data))

        return {
            "challenge_id": challenge_id,
            "otp_code": otp_code,
            "expires_in": self.otp_expiry,
        }

    async def verify_otp(self, challenge_id: str, raw_otp: str) -> int | None:
        """
        Verify the OTP code.
        Returns user_id if valid, or None if invalid/expired/blocked.
        """
        key = f"auth:otp:{challenge_id}"
        raw_data = await self.redis.get(key)
        if not raw_data:
            logger.warning(f"OTP verification failed: challenge {challenge_id} not found or expired.")
            return None

        data = json.loads(raw_data)
        
        # Check attempts limit
        if data["attempt_count"] >= self.max_attempts:
            logger.warning(f"OTP verification failed: maximum attempts reached for challenge {challenge_id}.")
            await self.redis.delete(key)
            return None

        # Check expiry
        if time.time() > data["expires_at"]:
            logger.warning(f"OTP verification failed: challenge {challenge_id} is expired.")
            await self.redis.delete(key)
            return None

        # Compare hashed OTP
        input_hash = self._hash_otp(raw_otp)
        if input_hash == data["hashed_otp"]:
            # Success: delete challenge immediately (single-use)
            await self.redis.delete(key)
            return data["user_id"]
        else:
            # Failure: increment attempts and save back to Redis
            data["attempt_count"] += 1
            remaining_ttl = int(max(1, data["expires_at"] - time.time()))
            await self.redis.setex(key, remaining_ttl, json.dumps(data))
            logger.info(f"OTP mismatch for challenge {challenge_id}. Attempt {data['attempt_count']}/{self.max_attempts}.")
            return None

    async def resend_otp(self, challenge_id: str) -> dict | None:
        """
        Resend a new OTP code for the existing challenge, enforcing a 60-second cooldown.
        Returns the new raw OTP code and user_id, or None if challenge not found.
        """
        key = f"auth:otp:{challenge_id}"
        raw_data = await self.redis.get(key)
        if not raw_data:
            return None

        data = json.loads(raw_data)
        
        # Enforce resend cooldown
        elapsed = time.time() - data["last_sent_at"]
        if elapsed < self.cooldown:
            # Raise exception indicating cooldown remaining
            cooldown_left = int(self.cooldown - elapsed)
            raise ValueError(f"Please wait {cooldown_left} seconds before requesting a new code.")

        # Generate a new OTP code
        new_otp = "".join(secrets.choice("0123456789") for _ in range(6))
        data["hashed_otp"] = self._hash_otp(new_otp)
        data["last_sent_at"] = time.time()
        data["expires_at"] = time.time() + self.otp_expiry
        data["attempt_count"] = 0  # Reset attempts on resend

        # Save back to Redis with fresh 5-minute TTL
        await self.redis.setex(key, self.otp_expiry, json.dumps(data))

        return {
            "otp_code": new_otp,
            "user_id": data["user_id"],
            "expires_in": self.otp_expiry,
        }
