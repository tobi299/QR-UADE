# Supabase — proyecto **QR UADE**

URL: `https://yrinbpyqaqnkrytaaetf.supabase.co`

Tabla: **`uade_qr_codigo`** (`id=1`, campo `codigo_hash`).

Tabla: **`token`** (`id=1`, columnas `token` + `refresh_token`) — access y refresh Microsoft. GitHub Actions **lee y escribe** acá; no hace falta rotar secrets en GitHub.

**Sembrado (una vez en la PC):**

```powershell
python main.py --login
python main.py --vps
```

## VPS (solo refresh + Supabase)

El VPS **no** puede llegar a `qrolvidocredencial.uade.edu.ar`; sí a Microsoft y Supabase.

`.env`: solo `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (el refresh se lee de Supabase).

```bash
python main.py --vps
```

Cada ~45–50 min (cron):

```bash
*/45 * * * * cd /ruta/QR-UADE && ./venv/bin/python main.py --vps
```

## GitHub Actions (en lugar del VPS)

Workflow: **`.github/workflows/uade-vps-sync.yml`** (cron + ejecución manual).

1. Sembrá Supabase desde la PC (arriba).
2. Secrets en GitHub: **`SUPABASE_URL`** y **`SUPABASE_SERVICE_ROLE_KEY`** (no guardes el refresh en GitHub).
3. Opcional: `UADE_USERNAME` / `UADE_PASSWORD` si el refresh en Supabase expiró por completo.
4. **Actions → Run workflow** o esperá el cron.

Cada ejecución renueva el access en Microsoft y, si rota, guarda el **nuevo refresh** otra vez en Supabase.

## PC — código con token del VPS

```powershell
python pc_fetch.py --supabase
```

(Lee `public.token`, GET a UADE, imprime `codigoHash`.)

## Subir código desde la PC

```powershell
python main.py
```

Re-login automático si el refresh venció (usa `UADE_USERNAME` / `UADE_PASSWORD`).

Loop cada 15 min: `python main.py --interval 900`

`.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (Dashboard → API → service_role).

## Atajo iPhone / Watch

Ver **`SHORTCUTS_GET.md`** (GET con `SUPABASE_ANON_KEY`).
