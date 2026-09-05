import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from .config import get_settings


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    if not init_data:
        raise ValueError("Empty initData")
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing hash")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    auth_date = int(data.get("auth_date", "0"))
    if max_age_seconds > 0 and abs(int(time.time()) - auth_date) > max_age_seconds:
        raise ValueError("Expired initData")

    user_raw = data.get("user")
    if not user_raw:
        raise ValueError("User is missing")
    return json.loads(user_raw)


def telegram_user(x_telegram_init_data: str = Header(default="")) -> dict:
    settings = get_settings()
    if settings.dev_mode and not x_telegram_init_data:
        return {"id": 777000, "first_name": "Demo", "username": "demo_user"}
    if not settings.bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")
    try:
        return validate_init_data(
            x_telegram_init_data,
            settings.bot_token,
            settings.auth_max_age_seconds,
        )
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid Telegram authorization")
