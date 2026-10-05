# Supabase — proyecto **QR UADE**

URL: `https://yrinbpyqaqnkrytaaetf.supabase.co`

Tabla: **`uade_qr_codigo`** (`id=1`, campo `codigo_hash`).

Tabla: **`token`** (`id=1`, columna `token`) — JWT Microsoft (`access_token`) para que la PC/celular llame a UADE sin pasar por el VPS.

## VPS (solo refresh + Supabase)

El VPS **no** puede llegar a `qrolvidocredencial.uade.edu.ar`; sí a Microsoft y Supabase.

En el VPS, `.env` con `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y el refresh (`UADE_REFRESH_TOKEN` o `src/token/refresh_token.local` tras un `--login` en la PC y copiar el archivo).

```bash
python main.py --vps
```

Cada ~45–50 min (cron):

```bash
*/45 * * * * cd /ruta/QR-UADE && ./venv/bin/python main.py --vps
```

## GitHub Actions (en lugar del VPS)

Workflow: **`.github/workflows/uade-vps-sync.yml`** (cron + ejecución manual).

1. Subí el repo a GitHub.
2. **Settings → Secrets and variables → Actions → New repository secret:**
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `UADE_REFRESH_TOKEN` (contenido de `src/token/refresh_token.local` desde tu PC)
   - Opcional: `UADE_USERNAME`, `UADE_PASSWORD` si el refresh vence.
3. **Actions → UADE token → Supabase → Run workflow**, o esperá el cron.

El runner de GitHub es efímero: si Microsoft rota el refresh, actualizá el secret `UADE_REFRESH_TOKEN` desde la PC (`python main.py --login` y copiá el archivo local).

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
