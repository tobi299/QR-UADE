# GET del código QR desde Atajos (iPhone / Apple Watch)

Proyecto Supabase: **QR UADE**  
Base: `https://yrinbpyqaqnkrytaaetf.supabase.co`

Copiá la **anon key** desde tu `.env` → `SUPABASE_ANON_KEY` (Dashboard → Project Settings → API → **anon** / legacy anon).  
**No** uses la `service_role` en el Atajo.

---

## Request HTTP (referencia)

| Campo | Valor |
|--------|--------|
| **Método** | `GET` |
| **URL** | `https://yrinbpyqaqnkrytaaetf.supabase.co/rest/v1/uade_qr_codigo?id=eq.1&select=codigo_hash` |

### Headers (obligatorios)

| Header | Valor |
|--------|--------|
| `apikey` | *(pegar `SUPABASE_ANON_KEY` completa)* |
| `Authorization` | `Bearer *(misma SUPABASE_ANON_KEY)*` |
| `Accept` | `application/json` |

Ejemplo de `Authorization` (una sola línea):

```text
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Probar con curl (PC)

Reemplazá `TU_ANON_KEY`:

```bash
curl -s "https://yrinbpyqaqnkrytaaetf.supabase.co/rest/v1/uade_qr_codigo?id=eq.1&select=codigo_hash" \
  -H "apikey: TU_ANON_KEY" \
  -H "Authorization: Bearer TU_ANON_KEY" \
  -H "Accept: application/json"
```

Respuesta esperada:

```json
[{"codigo_hash":"6D9A17400"}]
```

Si ves `SIN_CODIGO`, ejecutá `python main.py` en la PC.

---

## Atajo en iOS — pasos

1. **Texto**  
   Pegá la URL:
   `https://yrinbpyqaqnkrytaaetf.supabase.co/rest/v1/uade_qr_codigo?id=eq.1&select=codigo_hash`

2. **Obtener contenido de URL**  
   - URL: salida del paso **Texto**  
   - Método: **GET**  
   - Expandí **Headers** y agregá tres filas:

   | Clave | Valor |
   |-------|--------|
   | `apikey` | tu anon key |
   | `Authorization` | `Bearer tu anon key` |
   | `Accept` | `application/json` |

3. **Obtener elemento de lista** → **Primer elemento**  
   (el JSON es un array `[{...}]`)

4. **Obtener valor del diccionario** → clave: `codigo_hash`

5. **Generar código QR** → entrada: valor del paso 4

6. **Vista rápida**

Opcional: activá **Mostrar en Apple Watch** en los detalles del atajo y usá una complicación de Atajos.

---

## Errores frecuentes

| Síntoma | Causa |
|---------|--------|
| `401` / JWT | Key mal copiada o usaste `service_role` donde no corresponde |
| `[]` vacío | No existe fila `id=1`; aplicá la migración en `supabase/migrations/` |
| `SIN_CODIGO` | Supabase OK pero aún no corriste `python main.py` en la PC |
| JSON no parsea | Falta header `Accept: application/json` |

---

## URL alternativa (más campos)

```text
https://yrinbpyqaqnkrytaaetf.supabase.co/rest/v1/uade_qr_codigo?id=eq.1&select=codigo_hash,updated_at
```

Mismos headers. Sirve para ver cuándo se actualizó el código.
