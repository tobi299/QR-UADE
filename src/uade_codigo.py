"""Obtiene codigoHash desde la API UADE (olvido credencial)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

from src import ms_auth

TOKEN_URL = ms_auth.TOKEN_URL
CODIGO_URL = "https://qrolvidocredencial.uade.edu.ar/api/codigoqr"
REFRESH_CACHE = Path(__file__).resolve().parent / "token" / "refresh_token.local"
WEB_ORIGIN = ms_auth.WEB_ORIGIN
REFRESH_SCOPE = f"{ms_auth.SCOPE} openid profile"


def save_refresh_token(token: str) -> None:
    REFRESH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_CACHE.write_text(token.strip(), encoding="utf-8")


def load_refresh_token() -> str | None:
    env_token = os.environ.get("UADE_REFRESH_TOKEN", "").strip()
    if env_token:
        return env_token
    if REFRESH_CACHE.is_file():
        token = REFRESH_CACHE.read_text(encoding="utf-8").strip()
        if token:
            return token
    try:
        from src.supabase_store import load_refresh_token as load_refresh_supabase

        return load_refresh_supabase()
    except RuntimeError:
        return None


def _sync_ms_tokens_to_supabase(access: str, refresh: str) -> None:
    try:
        from src.supabase_store import save_ms_tokens

        save_ms_tokens(access, refresh)
    except RuntimeError:
        pass


def _refresh_access_token(refresh_token: str) -> tuple[str, str | None]:
    data = {
        "client_id": ms_auth.CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": REFRESH_SCOPE,
    }
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded;charset=utf-8",
        "origin": WEB_ORIGIN,
        "referer": f"{WEB_ORIGIN}/",
    }
    response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    if not response.ok:
        detail = response.text
        try:
            detail = response.json()
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"Error al refrescar token ({response.status_code}): {detail}")

    payload = response.json()
    access = payload.get("access_token")
    if not access:
        raise RuntimeError(f"Respuesta sin access_token: {payload}")
    return access, payload.get("refresh_token")


def _login_with_password() -> tuple[str, str | None]:
    username, password = ms_auth.load_credentials()
    tokens = ms_auth.acquire_tokens_with_password(username, password)
    access = tokens.get("access_token")
    if not access:
        raise RuntimeError(f"Login sin access_token: {tokens}")
    return access, tokens.get("refresh_token")


def _login_and_save(reason: str) -> tuple[str, str]:
    print(reason, file=sys.stderr)
    access, new_refresh = _login_with_password()
    if not new_refresh:
        raise RuntimeError("Login sin refresh_token")
    save_refresh_token(new_refresh)
    return access, new_refresh


def ensure_tokens(*, force_login: bool = False) -> tuple[str, str]:
    if force_login:
        access, refresh = _login_and_save("Login forzado (user/pass .env)…")
        _sync_ms_tokens_to_supabase(access, refresh)
        return access, refresh

    refresh = load_refresh_token()
    if not refresh:
        access, refresh = _login_and_save(
            "No hay refresh_token guardado; iniciando sesión con .env…"
        )
        _sync_ms_tokens_to_supabase(access, refresh)
        return access, refresh

    try:
        access, new_refresh = _refresh_access_token(refresh)
        if new_refresh:
            save_refresh_token(new_refresh)
            refresh = new_refresh
        _sync_ms_tokens_to_supabase(access, refresh)
        return access, refresh
    except requests.RequestException as exc:
        raise RuntimeError(
            "No hay conexión con login.microsoftonline.com. "
            "Revisá internet, VPN o DNS."
        ) from exc
    except RuntimeError:
        access, refresh = _login_and_save(
            "Refresh vencido o inválido; iniciando sesión con .env…"
        )
        _sync_ms_tokens_to_supabase(access, refresh)
        return access, refresh


def ensure_access_token(*, force_login: bool = False) -> str:
    access, _ = ensure_tokens(force_login=force_login)
    return access


def fetch_codigo_from_supabase() -> str:
    """GET codigoHash usando access en Supabase (public.token)."""
    from src.supabase_store import load_access_token

    access = load_access_token()
    try:
        data = _fetch_codigo_api(access)
    except PermissionError as exc:
        raise RuntimeError(
            "Access en Supabase vencido (401). Esperá GitHub Actions o corré "
            "python main.py --vps."
        ) from exc
    code = data.get("codigoHash")
    if not code:
        raise RuntimeError(f"Respuesta inesperada: {data}")
    return str(code)


def fetch_codigo_with_access(access: str) -> str:
    data = _fetch_codigo_api(access)
    code = data.get("codigoHash")
    if not code:
        raise RuntimeError(f"Respuesta inesperada: {data}")
    return str(code)


def fetch_codigo_hash(*, force_login: bool = False) -> str:
    access, _ = ensure_tokens(force_login=force_login)
    try:
        return fetch_codigo_with_access(access)
    except PermissionError:
        access, _ = ensure_tokens(force_login=True)
        return fetch_codigo_with_access(access)


def _fetch_codigo_api(access_token: str) -> dict:
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {access_token}",
        "referer": f"{WEB_ORIGIN}/",
    }
    response = requests.get(CODIGO_URL, headers=headers, timeout=30)
    if response.status_code == 401:
        raise PermissionError("Access token rechazado por la API.")
    response.raise_for_status()
    return response.json()
