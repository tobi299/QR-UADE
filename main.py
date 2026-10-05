#!/usr/bin/env python3
"""Refresca tokens Microsoft y los sube a Supabase (public.token)."""
from __future__ import annotations

import argparse
import os
import sys
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src import ms_auth
from src.supabase_store import save_ms_tokens
from src.uade_codigo import ensure_tokens, fetch_codigo_from_supabase, save_refresh_token


def cmd_login() -> None:
    user, pwd = ms_auth.load_credentials()
    tokens = ms_auth.acquire_tokens_with_password(user, pwd)
    refresh = tokens.get("refresh_token")
    if not refresh:
        raise RuntimeError("Login sin refresh_token")
    save_refresh_token(refresh)
    access = tokens.get("access_token")
    if access:
        try:
            save_ms_tokens(access, refresh)
            print("refresh + access sincronizados a Supabase public.token", file=sys.stderr)
        except RuntimeError as exc:
            print(f"Aviso Supabase: {exc}", file=sys.stderr)
    print("refresh_token guardado en src/token/refresh_token.local", file=sys.stderr)


def run_token_sync(*, force_login: bool = False) -> None:
    access, refresh = ensure_tokens(force_login=force_login)
    save_ms_tokens(access, refresh)
    print("Supabase public.token actualizado", file=sys.stderr)


def main() -> None:
    default_interval = int(os.environ.get("UADE_INTERVAL_SECONDS", "0"))
    p = argparse.ArgumentParser(
        description="Refresh Microsoft → Supabase public.token (access + refresh)."
    )
    p.add_argument(
        "--login",
        action="store_true",
        help="Forzar login Microsoft (.env) antes del sync.",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=default_interval,
        metavar="SEC",
        help="Repetir sync cada SEC segundos (0 = una vez). También UADE_INTERVAL_SECONDS.",
    )
    p.add_argument(
        "--fetch",
        action="store_true",
        help="Solo prueba: codigoHash con access de Supabase (ver README.md).",
    )
    args = p.parse_args()

    if args.login:
        cmd_login()

    interval = max(0, args.interval)

    while True:
        try:
            if args.fetch:
                print(fetch_codigo_from_supabase())
            else:
                run_token_sync(force_login=args.login)
                print("ok", file=sys.stderr)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            if interval <= 0:
                sys.exit(1)

        if interval <= 0:
            break
        args.login = False
        time.sleep(interval)


if __name__ == "__main__":
    main()
