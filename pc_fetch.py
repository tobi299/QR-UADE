#!/usr/bin/env python3
"""GET codigoHash: token desde Supabase (--supabase) o pc.main (step_2 + refresh)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src.supabase_store import load_access_token

PC_MAIN = Path(__file__).resolve().parent / "pc.main"
CODIGO_URL = "https://qrolvidocredencial.uade.edu.ar/api/codigoqr"
WEB_ORIGIN = "https://www.webcampus.uade.edu.ar"


def _codigo_headers(access: str) -> dict:
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {access}",
        "referer": f"{WEB_ORIGIN}/",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Obtiene codigoHash desde API UADE.")
    p.add_argument(
        "--supabase",
        action="store_true",
        help="Bearer desde public.token (VPS lo actualiza con main.py --vps).",
    )
    args = p.parse_args()

    data: dict | None = None
    if args.supabase:
        access = load_access_token()
        url = CODIGO_URL
        headers = _codigo_headers(access)
    else:
        if not PC_MAIN.is_file():
            print(
                f"No existe {PC_MAIN}. Corré: python main.py --pc-main "
                "o python pc_fetch.py --supabase",
                file=sys.stderr,
            )
            sys.exit(1)
        data = json.loads(PC_MAIN.read_text(encoding="utf-8"))
        step2 = data["step_2_get_codigo_hash"]
        url = step2["url"]
        headers = dict(step2["headers"])

    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 401 and data:
        step1 = data["step_1_refresh_access_token"]
        print("Access token vencido; refrescando…", file=sys.stderr)
        rr = requests.post(
            step1["url"],
            headers=step1["headers"],
            data=step1["body_form_urlencoded"],
            timeout=30,
        )
        rr.raise_for_status()
        access = rr.json().get("access_token")
        if not access:
            raise SystemExit(f"Refresh sin access_token: {rr.text[:300]}")
        headers["authorization"] = f"Bearer {access}"
        r = requests.get(url, headers=headers, timeout=30)
    elif r.status_code == 401:
        print(
            "401: token vencido. Corré python main.py --vps en el VPS o usá pc.main.",
            file=sys.stderr,
        )
        sys.exit(1)

    r.raise_for_status()
    body = r.json()
    codigo = body.get("codigoHash")
    if not codigo:
        raise SystemExit(f"Respuesta sin codigoHash: {body}")
    print(codigo)


if __name__ == "__main__":
    main()
