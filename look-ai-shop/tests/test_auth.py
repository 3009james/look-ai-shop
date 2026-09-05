import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from app.auth import validate_init_data


def signed_init_data(token: str) -> str:
    data = {
        "auth_date": str(int(time.time())),
        "query_id": "AAEAAAE",
        "user": json.dumps({"id": 42, "first_name": "Test"}, separators=(",", ":")),
    }
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_validate_init_data():
    token = "123456:ABCDEF"
    user = validate_init_data(signed_init_data(token), token)
    assert user["id"] == 42
