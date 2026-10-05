# QR UADE — tokens en Supabase

Este repo **solo mantiene tokens Microsoft** en Supabase (`public.token`, fila `id=1`).  
El **código QR** lo obtenés vos con HTTP desde PC/celular/Atajos (abajo).

## Comandos

| Comando | Qué hace |
|---------|----------|
| `python main.py --login` | Login UADE (`.env`) → guarda refresh local + Supabase |
| `python main.py` | Refresh Microsoft → actualiza `token` y `refresh_token` en Supabase |
| `python main.py --fetch` | Prueba: lee access de Supabase y pide `codigoHash` a UADE |

`.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, y para login `UADE_USERNAME` / `UADE_PASSWORD`.

GitHub Actions (`.github/workflows/uade-vps-sync.yml`) corre `python main.py` **una vez por hora**.

---

## Flujo HTTP para el QR

Orden: **(A) access token** → **(B) codigoHash**.

El access dura ~1 h. Si (B) responde **401**, repetí (A) o esperá que corra `main.py` / Actions.

---

### A) Obtener `access_token` (Microsoft)

#### A.1 — Leer access ya guardado (rápido)

Si `main.py` o Actions corrieron recientemente:

| Campo | Valor |
|--------|--------|
| **Método** | `GET` |
| **URL** | `{SUPABASE_URL}/rest/v1/token?id=eq.1&select=token` |
| **Headers** | `apikey`: tu `SUPABASE_ANON_KEY` o `SERVICE_ROLE` |
| | `Authorization`: `Bearer` + la misma key |
| | `Accept`: `application/json` |

Respuesta:

```json
[{"token":"eyJ0eXAiOiJKV1QiLCJhbG..."}]
```

Usá el valor de `token` como JWT (sin prefijo `Bearer` en el JSON; en el paso B va como `Bearer …`).

#### A.2 — Renovar access con `refresh_token` (si venció)

Necesitás el `refresh_token` (columna `refresh_token` en la misma fila, lectura con **service_role**, o el que guardó `main.py`).

| Campo | Valor |
|--------|--------|
| **Método** | `POST` |
| **URL** | `https://login.microsoftonline.com/344979d0-d31d-4c57-8ba0-491aff4acaed/oauth2/v2.0/token` |
| **Headers** | `content-type`: `application/x-www-form-urlencoded;charset=utf-8` |
| | `origin`: `https://www.webcampus.uade.edu.ar` |
| | `referer`: `https://www.webcampus.uade.edu.ar/` |

**Body** (`application/x-www-form-urlencoded`):

| Campo | Valor |
|--------|--------|
| `client_id` | `e900edf3-1ad1-41fa-801f-5db6dd5e0f44` |
| `grant_type` | `refresh_token` |
| `refresh_token` | *(tu refresh)* |
| `scope` | `openid profile offline_access api://2068d61c-4840-42a3-be3c-d4fe74a9e986/access_as_user openid profile` |

Respuesta (JSON): tomá `"access_token"`. Si viene `"refresh_token"` nuevo, conviene volver a subir ambos con `python main.py` en PC.

**curl (ejemplo):**

```bash
curl -s -X POST "https://login.microsoftonline.com/344979d0-d31d-4c57-8ba0-491aff4acaed/oauth2/v2.0/token" \
  -H "content-type: application/x-www-form-urlencoded;charset=utf-8" \
  -H "origin: https://www.webcampus.uade.edu.ar" \
  -H "referer: https://www.webcampus.uade.edu.ar/" \
  --data-urlencode "client_id=e900edf3-1ad1-41fa-801f-5db6dd5e0f44" \
  --data-urlencode "grant_type=refresh_token" \
  --data-urlencode "refresh_token=TU_REFRESH" \
  --data-urlencode "scope=openid profile offline_access api://2068d61c-4840-42a3-be3c-d4fe74a9e986/access_as_user openid profile"
```

---

### B) Obtener `codigoHash` (UADE)

Solo desde red que **llegue** a `qrolvidocredencial.uade.edu.ar` (tu PC/celular; muchos VPS no).

| Campo | Valor |
|--------|--------|
| **Método** | `GET` |
| **URL** | `https://qrolvidocredencial.uade.edu.ar/api/codigoqr` |
| **Headers** | `accept`: `application/json, text/plain, */*` |
| | `authorization`: `Bearer TU_ACCESS_TOKEN` |
| | `referer`: `https://www.webcampus.uade.edu.ar/` |

Respuesta esperada:

```json
{"codigoHash":"1E916024D", ...}
```

Ese string es el contenido del QR.

**curl (ejemplo):**

```bash
curl -s "https://qrolvidocredencial.uade.edu.ar/api/codigoqr" \
  -H "accept: application/json, text/plain, */*" \
  -H "authorization: Bearer TU_ACCESS_TOKEN" \
  -H "referer: https://www.webcampus.uade.edu.ar/"
```

---

## Atajo iOS (resumen)

1. **GET** Supabase → campo `token` (paso A.1), o refresh manual (A.2).
2. **GET** UADE (paso B) con header `authorization`.
3. Parsear JSON → `codigoHash` → **Generar código QR**.

Más detalle operativo de Supabase: `docs/SUPABASE.md`.
