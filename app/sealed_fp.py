# app/sealed_fp.py
import base64
from flask import current_app

from fingerprint_pro_server_api_sdk.sealed import (
    unseal_events_response,
    DecryptionKey,
    DecryptionAlgorithm,
)

def unseal_fp_events_response(sealed_b64: str):
   
    # Take base64 sealedResult string from the JS agent,
    # return EventResponse object (same as /events payload).
    
    if not sealed_b64:
        return None

    key_b64 = current_app.config.get("FINGERPRINT_ENCRYPTION_KEY_BASE64")
    if not key_b64:
        raise RuntimeError("FINGERPRINT_ENCRYPTION_KEY_BASE64 is not configured")

    sealed_bytes = base64.b64decode(sealed_b64)
    key_bytes = base64.b64decode(key_b64)

    keys = [DecryptionKey(key_bytes, DecryptionAlgorithm["Aes256Gcm"])]

    events_response = unseal_events_response(sealed_bytes, keys)
    return events_response
