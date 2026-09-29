# Supabase — proyecto **QR UADE**

URL: `https://yrinbpyqaqnkrytaaetf.supabase.co`

Tabla: **`uade_qr_codigo`** (`id=1`, campo `codigo_hash`).

## Subir código desde la PC

```powershell
python main.py
```

Re-login automático si el refresh venció (usa `UADE_USERNAME` / `UADE_PASSWORD`).

Loop cada 15 min: `python main.py --interval 900`

`.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (Dashboard → API → service_role).

## Atajo iPhone / Watch

Ver **`SHORTCUTS_GET.md`** (GET con `SUPABASE_ANON_KEY`).
