import asyncio
import os

import redis.asyncio as redis
from dotenv import load_dotenv

# Load variables from backend/.env
load_dotenv()


async def test_redis():
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        raise ValueError(
            "REDIS_URL is not set. Add it to your .env file."
        )

    print("REDIS_URL found. Testing connection...")

    client = redis.from_url(
        redis_url,
        decode_responses=True,
    )

    try:
        # Test connection
        pong = await client.ping()
        print("PING:", pong)

        # Test SET with 60-second expiry
        await client.set(
            "ksp:test",
            "Railway Redis Working",
            ex=60,
        )

        # Test GET
        value = await client.get("ksp:test")
        print("Redis value:", value)

        # Test TTL
        ttl = await client.ttl("ksp:test")
        print("TTL:", ttl)

        # Clean up
        await client.delete("ksp:test")

        print("\nSUCCESS: Railway Redis is working correctly!")

    except Exception as exc:
        print("\nRedis connection failed:")
        print(type(exc).__name__, str(exc))
        raise

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_redis())