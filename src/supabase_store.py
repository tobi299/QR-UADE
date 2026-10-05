"""Lectura/escritura de tokens Microsoft en Supabase (public.token)."""
from __future__ import annotations

import os

import requests

TOKEN_TABLE = "token"
ROW_ID = 1


def _supabase_config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env")
    return url, key


def load_access_token() -> str:
    """Lee JWT desde public.token id=1 (anon o service_role en .env)."""
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_ANON_KEY", "").strip()
    )
    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL y SUPABASE_ANON_KEY (o SERVICE_ROLE) en .env"
        )
    get_url = f"{url}/rest/v1/{TOKEN_TABLE}?id=eq.{ROW_ID}&select=token"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    response = requests.get(get_url, headers=headers, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Supabase GET token falló ({response.status_code}): {response.text[:400]}"
        )
    rows = response.json()
    if not rows or not rows[0].get("token"):
        raise RuntimeError("No hay token en public.token id=1")
    return str(rows[0]["token"]).strip()


def load_refresh_token() -> str:
    """Lee refresh Microsoft desde public.token id=1 (solo service_role)."""
    url, key = _supabase_config()
    get_url = f"{url}/rest/v1/{TOKEN_TABLE}?id=eq.{ROW_ID}&select=refresh_token"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    response = requests.get(get_url, headers=headers, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Supabase GET refresh_token falló ({response.status_code}): {response.text[:400]}"
        )
    rows = response.json()
    if not rows or not rows[0].get("refresh_token"):
        raise RuntimeError("No hay refresh_token en public.token id=1")
    return str(rows[0]["refresh_token"]).strip()


def _normalize_access(access_token: str) -> str:
    token = access_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise RuntimeError("access_token vacío")
    return token


def save_ms_tokens(access_token: str, refresh_token: str) -> None:
    """UPSERT access + refresh en public.token id=1."""
    access = _normalize_access(access_token)
    refresh = refresh_token.strip()
    if not refresh:
        raise RuntimeError("refresh_token vacío")
    url, key = _supabase_config()
    upsert_url = f"{url}/rest/v1/{TOKEN_TABLE}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    response = requests.post(
        upsert_url,
        json={"id": ROW_ID, "token": access, "refresh_token": refresh},
        headers=headers,
        timeout=30,
    )
    if response.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"Supabase UPSERT token falló ({response.status_code}): {response.text[:400]}"
        )
