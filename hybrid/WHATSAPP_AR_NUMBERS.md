# WhatsApp Argentina — Formato E.164 para OpenClaw

## Regla: `+54 9 [cod_area_sin_0] [numero_sin_15]`

| Componente | Regla | Ejemplo |
|------------|-------|---------|
| +54 | Código país Argentina | +54 |
| 9 | Obligatorio para móvil | 9 |
| Código área | Sin el 0 inicial | 264 (no 0264) |
| Número | Sin el 15 | 4123456 (no 15-4123456) |

**Total: 13 dígitos** (sin contar el `+`)

## Ejemplos

- `0264 15-412-3456` → `+5492644123456`
- `011 15-5555-0101` → `+5491155550101`
- `0351 15-400-0000` → `+5493514000000`

## Configuración en OpenClaw

```json
{
  "channels": {
    "whatsapp": {
      "allowFrom": ["+5492644123456"],
      "groupPolicy": "open"
    }
  }
}
```

## Troubleshooting

1. **Business WhatsApp puede fallar** — Baileys a veces conflictúa con cuentas Business. Probar con cuenta normal primero.
2. **Cerrar sesiones viejas** — WhatsApp → Dispositivos vinculados → limpiar sessions activas.
3. **QR expira en ~20 seg** — regenerar con `openclaw channels whatsapp reconnect`
