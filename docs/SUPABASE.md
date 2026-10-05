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

Workflow: `.github/workflows/uade-vps-sync.yml` → `python main.py` cada hora.

Opcional si el refresh en Supabase expiró: `UADE_USERNAME`, `UADE_PASSWORD`.

## Peticiones HTTP (QR)

Ver **`README.md`** (access Microsoft + GET codigoHash UADE).
