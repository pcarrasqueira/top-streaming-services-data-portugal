#!/usr/bin/env python3
"""Authorize the project with Trakt's device-code OAuth flow."""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv, set_key

TRAKT_API_BASE_URL = "https://api.trakt.tv"
REQUEST_TIMEOUT = 30


def _headers(client_id: str, access_token: Optional[str] = None) -> Dict[str, str]:
    """Build the headers required by Trakt API requests."""
    headers = {
        "Content-Type": "application/json",
        "trakt-api-key": client_id,
        "trakt-api-version": "2",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _response_error(response: requests.Response) -> Optional[str]:
    """Return an OAuth error name without exposing response contents."""
    try:
        payload = response.json()
    except ValueError:
        return None
    error = payload.get("error") if isinstance(payload, dict) else None
    return error if isinstance(error, str) else None


def _token_string(payload: Dict[str, Any], key: str) -> str:
    """Read a required non-empty string from a Trakt token response."""
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Trakt token response did not contain {key}.")
    return value


def request_device_code(client_id: str) -> Dict[str, Any]:
    """Request the short-lived code shown to the user for authorization."""
    response = requests.post(
        f"{TRAKT_API_BASE_URL}/oauth/device/code",
        headers=_headers(client_id),
        json={"client_id": client_id},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Trakt returned an invalid device-code response.")
    for key in ("device_code", "user_code", "verification_url", "expires_in", "interval"):
        if key not in payload:
            raise RuntimeError(f"Trakt device-code response did not contain {key}.")
    return payload


def poll_for_token(client_id: str, device_code: str, expires_in: int, interval: float) -> Dict[str, Any]:
    """Poll until the user authorizes the app or the device code expires."""
    deadline = time.monotonic() + expires_in
    poll_interval = max(interval, 1.0)

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("The Trakt device code expired before authorization completed.")

        time.sleep(min(poll_interval, remaining))
        if time.monotonic() >= deadline:
            raise TimeoutError("The Trakt device code expired before authorization completed.")

        response = requests.post(
            f"{TRAKT_API_BASE_URL}/oauth/device/token",
            headers=_headers(client_id),
            json={"code": device_code, "client_id": client_id},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("Trakt returned an invalid token response.")
            _token_string(payload, "access_token")
            _token_string(payload, "refresh_token")
            return payload

        error = _response_error(response)
        if response.status_code == 400 and error in (None, "authorization_pending"):
            continue
        if error == "slow_down" or response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "0")
            try:
                retry_after_seconds = float(retry_after)
            except ValueError:
                retry_after_seconds = 0
            poll_interval = max(poll_interval + 5, retry_after_seconds)
            continue

        detail = f": {error}" if error else ""
        raise RuntimeError(f"Trakt device authorization failed (HTTP {response.status_code}){detail}.")


def verify_access_token(client_id: str, access_token: str) -> None:
    """Verify the new token before saving it."""
    response = requests.get(
        f"{TRAKT_API_BASE_URL}/users/me",
        headers=_headers(client_id, access_token),
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Trakt token validation failed (HTTP {response.status_code}).")


def save_tokens(env_file: Path, client_id: str, access_token: str, refresh_token: str) -> None:
    """Store credentials in the local dotenv file without printing them."""
    for key, value in (
        ("CLIENT_ID", client_id),
        ("ACCESS_TOKEN", access_token),
        ("REFRESH_TOKEN", refresh_token),
    ):
        set_key(str(env_file), key, value, quote_mode="always")

    os.chmod(env_file, 0o600)


def main() -> int:
    """Run the interactive Trakt device authorization flow."""
    parser = argparse.ArgumentParser(description="Connect this project to a Trakt account.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="dotenv file to read CLIENT_ID from and save tokens to (default: .env)",
    )
    parser.add_argument("--client-id", help="Trakt app Client ID; defaults to CLIENT_ID from the environment")
    args = parser.parse_args()

    load_dotenv(args.env_file)
    client_id = args.client_id or os.getenv("CLIENT_ID")
    if not client_id:
        print("Set CLIENT_ID in .env or pass --client-id.", file=sys.stderr)
        return 2

    tokens_saved = False
    try:
        device = request_device_code(client_id)
        print("\nTo authorize this project with Trakt:")
        print(f"1. Open: {device['verification_url']}")
        print(f"2. Enter this code: {device['user_code']}")
        print(f"Waiting for approval (expires in {int(device['expires_in']) // 60} minutes)...\n")

        tokens = poll_for_token(
            client_id,
            _token_string(device, "device_code"),
            int(device["expires_in"]),
            float(device["interval"]),
        )
        access_token = _token_string(tokens, "access_token")
        refresh_token = _token_string(tokens, "refresh_token")
        save_tokens(args.env_file, client_id, access_token, refresh_token)
        tokens_saved = True
        verify_access_token(client_id, access_token)
    except (OSError, requests.RequestException, RuntimeError, TimeoutError, ValueError) as error:
        saved_note = f"Tokens were saved to {args.env_file}. " if tokens_saved else ""
        print(f"Trakt authorization failed: {saved_note}{error}", file=sys.stderr)
        return 1

    print(f"Trakt is connected. Tokens were saved to {args.env_file}.")
    print("Update the GitHub Actions CLIENT_ID, ACCESS_TOKEN, and REFRESH_TOKEN secrets to enable scheduled updates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
