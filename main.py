#!/usr/bin/env python3
"""Obtiene codigoHash UADE y lo sube a Supabase (re-login automático si hace falta)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src import ms_auth
from src.supabase_store import save_access_token, save_codigo
from src.uade_codigo import fetch_codigo_hash, save_refresh_token, write_pc_main


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


def run_vps(*, force_login: bool = False) -> str:
    """Refresca en Microsoft (sin UADE) y sube access_token → Supabase public.token."""
    path = write_pc_main(force_login=force_login, codigo_hash=None)
    access = json.loads(path.read_text(encoding="utf-8"))["access_token"]
    save_access_token(access)
    print(f"Supabase public.token actualizado ({path})", file=sys.stderr)
    return access


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
    p.add_argument(
        "--pc-main",
        action="store_true",
        help="Escribir pc.main (peticiones completas) en la raíz del proyecto.",
    )
    p.add_argument(
        "--vps",
        action="store_true",
        help=(
            "Modo VPS: refresh Microsoft, pc.main local y subir access_token "
            "a Supabase (public.token id=1). No llama a qrolvidocredencial."
        ),
    )
    args = p.parse_args()

    if args.vps and args.pc_main:
        p.error("Usá solo uno: --vps o --pc-main")

    if args.login:
        cmd_login()

    interval = max(0, args.interval)

    while True:
        codigo: str | None = None
        try:
            if args.vps:
                run_vps(force_login=args.login)
                print("ok", file=sys.stderr)
            elif args.pc_main:
                try:
                    codigo = fetch_codigo_hash(force_login=args.login)
                except (requests.RequestException, OSError) as exc:
                    print(
                        f"Aviso: no se pudo llamar a UADE ({exc}); "
                        "pc.main igual incluye tokens y curl.",
                        file=sys.stderr,
                    )
                path = write_pc_main(force_login=args.login, codigo_hash=codigo)
                print(f"pc.main escrito en {path}", file=sys.stderr)
                if codigo:
                    save_codigo(codigo)
                    print(codigo)
                elif interval <= 0:
                    sys.exit(0)
            else:
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
