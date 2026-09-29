import hashlib
import base64
import json
import os
import re
import secrets
from urllib.parse import parse_qs, urlparse

import requests

TENANT_ID = "344979d0-d31d-4c57-8ba0-491aff4acaed"
CLIENT_ID = "e900edf3-1ad1-41fa-801f-5db6dd5e0f44"
REDIRECT_URI = "https://www.webcampus.uade.edu.ar/olvidocredencial"
SCOPE = (
    "openid profile offline_access "
    "api://2068d61c-4840-42a3-be3c-d4fe74a9e986/access_as_user"
)
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
AUTHORIZE_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
WEB_ORIGIN = "https://www.webcampus.uade.edu.ar"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(32)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def parse_config(html: str) -> dict:
    marker = html.find("$Config=")
    if marker == -1:
        raise RuntimeError("No se encontró la página de login de Microsoft.")
    start = html.find("{", marker)
    end_tag = html.find("//]]>", start)
    if start == -1 or end_tag == -1:
        raise RuntimeError("No se pudo leer la configuración de login.")
    last_brace = html.rfind("}", start, end_tag)
    return json.loads(html[start : last_brace + 1])


def normalize_username(raw: str) -> str:
    user = raw.strip()
    if "@" not in user:
        user = f"{user}@uade.edu.ar"
    return user


def load_credentials() -> tuple[str, str]:
    user = (os.getenv("UADE_USERNAME") or os.getenv("USERNAME") or "").strip()
    password = (os.getenv("UADE_PASSWORD") or os.getenv("PASSWORD") or "").strip()
    if not user or not password:
        raise RuntimeError(
            "Configurá UADE_USERNAME y UADE_PASSWORD (o USERNAME/PASSWORD) en .env"
        )
    return normalize_username(user), password


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        }
    )
    return session


def authorize_params(code_challenge: str, username: str) -> dict:
    return {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": secrets.token_urlsafe(16),
        "response_mode": "query",
        "prompt": "login",
    }


def fetch_login_page(session: requests.Session, username: str, challenge: str) -> requests.Response:
    response = session.get(
        AUTHORIZE_URL,
        params=authorize_params(challenge, username),
        timeout=30,
    )
    response.raise_for_status()
    cfg = parse_config(response.text)
    if cfg.get("sCtx") and cfg.get("sFT"):
        return response

    post_path = cfg.get("urlPost", "")
    if post_path.startswith("/"):
        follow = session.get("https://login.microsoftonline.com" + post_path, timeout=30)
        follow.raise_for_status()
        return follow

    return response


def extract_code(url: str) -> str | None:
    parsed = urlparse(url)
    target = urlparse(REDIRECT_URI)
    if parsed.scheme != target.scheme or parsed.netloc != target.netloc:
        return None
    if parsed.path.rstrip("/") != target.path.rstrip("/"):
        return None
    values = parse_qs(parsed.query).get("code")
    return values[0] if values else None


def absolute_login_url(path: str) -> str:
    if path.startswith("http"):
        return path
    return "https://login.microsoftonline.com" + path


def submit_kmsi(session: requests.Session, cfg: dict, username: str) -> requests.Response:
    body = {
        "LoginOptions": "1",
        "type": "28",
        "ctx": cfg["sCtx"],
        "flowToken": cfg["sFT"],
        "canary": cfg["canary"],
        "hpgrequestid": cfg.get("correlationId", ""),
        "login": cfg.get("sPOST_Username") or username,
        "loginfmt": cfg.get("sPOST_Username") or username,
    }
    return session.post(
        absolute_login_url(cfg.get("urlPost") or "/kmsi"),
        data=body,
        allow_redirects=False,
        timeout=30,
    )


def follow_redirects_for_code(
    session: requests.Session, response: requests.Response, *, username: str = ""
) -> str:
    current = response
    for _ in range(30):
        location = current.headers.get("Location", "")
        if location:
            location = absolute_login_url(location)
            code = extract_code(location)
            if code:
                return code
            current = session.get(location, allow_redirects=False, timeout=30)
            continue

        code = extract_code(current.url)
        if code:
            return code

        if current.status_code == 200 and current.text:
            cfg = parse_config(current.text)
            post_params = cfg.get("oPostParams")
            post_path = cfg.get("urlPost")
            if post_params and post_path:
                current = session.post(
                    absolute_login_url(post_path),
                    data=post_params,
                    allow_redirects=False,
                    timeout=30,
                )
                continue
            if post_path == "/kmsi" or "KmsiInterrupt" in current.text:
                current = submit_kmsi(session, cfg, username)
                continue

        if current.status_code == 200 and (
            "sErrTxt" in current.text or "strServiceException" in current.text
        ):
            try:
                cfg = parse_config(current.text)
                msg = (
                    cfg.get("strServiceException")
                    or cfg.get("sErrTxt")
                    or cfg.get("sErrorCode")
                )
                if msg:
                    text = str(msg)
                    if text == "50034":
                        text = (
                            "Cuenta no encontrada en el tenant UADE (50034). "
                            "Usá el mail completo @uade.edu.ar en .env."
                        )
                    elif text == "50126":
                        text = "Usuario o contraseña incorrectos (50126)."
                    raise RuntimeError(text)
            except json.JSONDecodeError:
                pass
            match = re.search(r"sErrTxt\s*:\s*'([^']*)'", current.text)
            raise RuntimeError(match.group(1) if match else "Microsoft rechazó el login.")

        break

    raise RuntimeError(
        "No se obtuvo el código de autorización. "
        f"HTTP {getattr(current, 'status_code', '?')} url={getattr(current, 'url', '?')[:120]}. "
        "¿MFA activo o credenciales incorrectas?"
    )


def login_form_body(cfg: dict, username: str, password: str) -> dict:
    return {
        "i13": "0",
        "login": username,
        "loginfmt": username,
        "type": "11",
        "LoginOptions": "3",
        "lrt": "",
        "lrtPartition": "",
        "hisRegion": "",
        "hisScaleUnit": "",
        "passwd": password,
        "ps": "2" if password else "1",
        "psRNGCDefaultType": "",
        "psRNGCEntropy": "",
        "psRNGCSLK": "",
        "canary": cfg["canary"],
        "ctx": cfg["sCtx"],
        "hpgrequestid": cfg.get("correlationId", ""),
        "flowToken": cfg["sFT"],
        "PPSX": "",
        "NewUser": "1",
        "FoundMSAs": "",
        "fspost": "0",
        "i21": "0",
        "CookieDisclosure": "0",
        "IsFidoSupported": "1",
        "isSignupPost": "0",
        "i19": "4840",
    }


def resolve_html_step(session: requests.Session, response: requests.Response) -> requests.Response:
    current = response
    for _ in range(15):
        if current.status_code in (301, 302, 303, 307, 308):
            location = absolute_login_url(current.headers.get("Location", ""))
            current = session.get(location, allow_redirects=False, timeout=30)
            continue
        if current.status_code != 200 or not current.text:
            break
        if 'name="passwd"' in current.text:
            return current
        try:
            cfg = parse_config(current.text)
        except RuntimeError:
            break
        if cfg.get("sCtx") and cfg.get("sFT"):
            return current
        post_params = cfg.get("oPostParams")
        post_path = cfg.get("urlPost")
        if post_params and post_path:
            current = session.post(
                absolute_login_url(post_path),
                data=post_params,
                allow_redirects=False,
                timeout=30,
            )
            continue
        break
    return current


def post_login_step(
    session: requests.Session, cfg: dict, username: str, password: str
) -> requests.Response:
    post_url = absolute_login_url(cfg["urlPost"])
    return session.post(
        post_url,
        data=login_form_body(cfg, username, password),
        allow_redirects=False,
        timeout=30,
    )


def login_for_code(session: requests.Session, username: str, password: str, challenge: str) -> str:
    page = fetch_login_page(session, username, challenge)
    cfg = parse_config(page.text)

    if 'name="passwd"' not in page.text:
        user_step = post_login_step(session, cfg, username, "")
        user_step = resolve_html_step(session, user_step)
        cfg = parse_config(user_step.text)

    posted = post_login_step(session, cfg, username, password)
    return follow_redirects_for_code(session, posted, username=username)


def exchange_code(session: requests.Session, code: str, verifier: str) -> dict:
    data = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "code": code,
        "code_verifier": verifier,
        "grant_type": "authorization_code",
    }
    headers = {
        "content-type": "application/x-www-form-urlencoded;charset=utf-8",
        "origin": WEB_ORIGIN,
        "referer": f"{WEB_ORIGIN}/",
    }
    response = session.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    if not response.ok:
        raise RuntimeError(f"Canje de código falló ({response.status_code}): {response.text[:400]}")
    return response.json()


def acquire_tokens_with_password(username: str, password: str) -> dict:
    session = new_session()
    verifier, challenge = pkce_pair()
    code = login_for_code(session, username, password, challenge)
    return exchange_code(session, code, verifier)
