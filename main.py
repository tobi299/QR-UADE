#!/usr/bin/env python3
"""Obtiene codigoHash UADE y lo sube a Supabase (re-login automático si hace falta)."""
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
from src.supabase_store import save_codigo
from src.uade_codigo import fetch_codigo_hash, save_refresh_token


def cmd_login() -> None:
    user, pwd = ms_auth.load_credentials()
    tokens = ms_auth.acquire_tokens_with_password(user, pwd)
    refresh = tokens.get("refresh_token")
    if not refresh:
        raise RuntimeError("Login sin refresh_token")
    save_refresh_token(refresh)
    print("refresh_token guardado en src/token/refresh_token.local", file=sys.stderr)


def run_sync(*, force_login: bool = False) -> str:
    codigo = fetch_codigo_hash(force_login=force_login)
    save_codigo(codigo)
    return codigo


def main() -> None:
    default_interval = int(os.environ.get("UADE_INTERVAL_SECONDS", "0"))
    p = argparse.ArgumentParser(
        description=(
            "Sync codigoHash → Supabase. Sin flags: un sync con re-login automático "
            "si el refresh_token venció."
        )
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
    args = p.parse_args()

    if args.login:
        cmd_login()

    interval = max(0, args.interval)

    while True:
        try:
            codigo = run_sync(force_login=args.login)
            print(codigo)
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
