# app/fp_client.py
from flask import current_app
from fingerprint_pro_server_api_sdk import Configuration, ApiClient
from fingerprint_pro_server_api_sdk.api.events_api import EventsApi

def fetch_fp_event_by_request_id(request_id: str):
    """
    Calls Fingerprint Server API to fetch event details for a given request_id.
    Returns a plain dict (SDK model converted) or None on error/missing key.
    """
    secret = current_app.config.get("FINGERPRINT_SECRET_KEY")
    if not secret or not request_id:
        return None

    cfg = Configuration()
    # SDK expects header name 'ApiKeyHeader'
    cfg.api_key['ApiKeyHeader'] = secret

    with ApiClient(cfg) as client:
        api = EventsApi(client)
        event_model = api.get_event(request_id)  # raises on 404/401
        # convert to dict for JSON storage
        try:
            return event_model.to_dict()
        except AttributeError:
            # Fallback if SDK version differs
            return event_model
