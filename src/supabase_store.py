"""Escritura de codigo_hash en Supabase (uade_qr_codigo)."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

TABLE = "uade_qr_codigo"
ROW_ID = 1


def save_codigo(codigo_hash: str) -> None:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env")

    patch_url = f"{url}/rest/v1/{TABLE}?id=eq.{ROW_ID}"
    body = {
        "codigo_hash": codigo_hash,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    response = requests.patch(patch_url, json=body, headers=headers, timeout=30)
    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Supabase PATCH falló ({response.status_code}): {response.text[:400]}"
        )
