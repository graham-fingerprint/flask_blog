# app/sealed_fp.py
import base64
from flask import current_app

# ✅ Import from the top-level package (works with the SDK version on Render)
from fingerprint_pro_server_api_sdk import (
    unseal_event_response,
    DecryptionKey,
    DecryptionAlgorithm,
)

def unseal_fp_event_response(sealed_b64: str):
    if not sealed_b64:
        return None

    key_b64 = current_app.config.get("FINGERPRINT_ENCRYPTION_KEY_BASE64")
    if not key_b64:
        raise RuntimeError("FINGERPRINT_ENCRYPTION_KEY_BASE64 is not configured")

    sealed_bytes = base64.b64decode(sealed_b64)
    key_bytes = base64.b64decode(key_b64)

    keys = [DecryptionKey(key_bytes, DecryptionAlgorithm["Aes256Gcm"])]

    # ✅ Call the singular function
    event_response = unseal_event_response(sealed_bytes, keys)
    return event_response
