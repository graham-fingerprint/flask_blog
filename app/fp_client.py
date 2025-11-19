# app/fp_client.py
import os
from flask import current_app
import fingerprint_pro_server_api_sdk
from fingerprint_pro_server_api_sdk.rest import ApiException, KnownApiException

def fetch_fp_event_by_request_id(request_id: str):
   
    secret = current_app.config.get("FINGERPRINT_SECRET_KEY")
    region = current_app.config.get("FINGERPRINT_REGION")
    if not secret or not request_id:
        return None

    # Build configuration
    if region:
        config = fingerprint_pro_server_api_sdk.Configuration(api_key=secret, region=region)
    else:
        config = fingerprint_pro_server_api_sdk.Configuration(api_key=secret)

    api = fingerprint_pro_server_api_sdk.FingerprintApi(config)

    try:
        event_model = api.get_event(request_id)  # GET /events/{request_id}
        try:
            return event_model.to_dict()
        except AttributeError:
            return event_model
    except KnownApiException as e:
        # Structured API error from SDK (bad key, bad request_id, etc.)
        current_app.logger.warning("Fingerprint API known error: %s", getattr(e, "structured_error", e))
        return None
    except ApiException as e:
        current_app.logger.exception("Fingerprint API exception: %s", e)
        return None
