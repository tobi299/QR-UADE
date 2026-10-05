# Supabase — proyecto **QR UADE**

URL: `https://yrinbpyqaqnkrytaaetf.supabase.co`

Tabla: **`token`** (`id=1`, columnas `token` + `refresh_token`).

GitHub Actions y `python main.py` **leen y escriben** ahí. No se sube `codigo_hash` a Supabase.

## Sembrado (una vez en la PC)

```powershell
python main.py --login
python main.py
```

## GitHub Actions

Secrets: **`SUPABASE_URL`**, **`SUPABASE_SERVICE_ROLE_KEY`**.

Workflow: `.github/workflows/uade-vps-sync.yml` → `python main.py` ~cada hora (cron `:17` UTC).

Opcional si el refresh en Supabase expiró: `UADE_USERNAME`, `UADE_PASSWORD`.

### Si el schedule no corre cada hora

GitHub **no garantiza** crons; a veces solo ves 1 run y nada más.

1. **Actions** → workflow **UADE token → Supabase** → menú **⋯** → **Enable workflow** (si aparece deshabilitado).
2. **Settings** → **Actions** → **General** → Actions **Allowed**; permisos del workflow OK.
3. Hacé **push** del YAML actualizado (cron en minuto 17, no en `:00`).
4. **Plan B (fiable):** en tu PC, Programador de tareas cada hora:  
   `python "P:\QR UADE\QR-UADE\main.py"` (mismo efecto que Actions).
5. **Plan C:** [cron-job.org](https://cron-job.org) u otro cron externo que dispare **Run workflow** vía API (PAT con scope `actions:write`).

## Peticiones HTTP (QR)

Ver **`README.md`** (access Microsoft + GET codigoHash UADE).
