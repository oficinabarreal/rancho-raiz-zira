#!/usr/bin/env python3
"""
facturas_check.py — Verifica facturas próximas a vencer y envía recordatorios.

Uso:
  python3 scripts/facturas_check.py          # check + notificar
  python3 scripts/facturas_check.py --list   # solo listar
  python3 scripts/facturas_check.py --add    # modo interactivo para agregar factura

Los datos se guardan en crm_state/facturas/ (excluido del repo GitHub).
"""
import argparse
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm.facturas.store import FacturaStore
from crm.facturas.models import FacturaProgramada, Pago


TELEGRAM_TOKEN = os.environ.get("CRM_TG_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("CRM_TG_CHAT_ID", "8272684219")


def enviar_telegram(mensaje: str) -> bool:
    """Envía un mensaje por Telegram."""
    if not TELEGRAM_TOKEN:
        print("  ⚠ CRM_TG_TOKEN no configurado, omitiendo Telegram")
        print(f"  Mensaje: {mensaje}")
        return False

    import urllib.request
    import json

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  ⚠ Error Telegram: {e}")
        return False


def cmd_check(args):
    """Verifica facturas próximas a vencer y notifica."""
    store = FacturaStore()
    hoy = date.today()

    print(f"📅 {hoy.isoformat()} — Verificando facturas...\n")

    # Facturas próximas a vencer
    proximas = store.proximos_vencimientos(dias=args.dias or 5)
    if proximas:
        print(f"🔔 {len(proximas)} factura(s) próxima(s) a vencer:\n")
        for factura, dias in proximas:
            print(f"  ⏰ {factura.nombre} — vence en {dias} día(s)")
            print(f"     Responsable: {factura.responsable}")
            if factura.monto_estimado:
                print(f"     Monto estimado: ${factura.monto_estimado:,.0f}")
            print()

        # Notificar por Telegram
        msg_lines = ["🔔 <b>Recordatorio de Facturas</b>\n"]
        for factura, dias in proximas:
            emoji = "🔴" if dias <= 1 else "🟡" if dias <= 3 else "🔵"
            msg_lines.append(f"{emoji} <b>{factura.nombre}</b> — vence en {dias} día(s)")
            msg_lines.append(f"   👤 {factura.responsable}")
            if factura.monto_estimado:
                msg_lines.append(f"   💰 ${factura.monto_estimado:,.0f}")
            msg_lines.append("")

        enviar_telegram("\n".join(msg_lines))
    else:
        print("✅ No hay facturas próximas a vencer")

    # Últimos pagos registrados
    pagos = store.listar_pagos()
    if pagos:
        ultimo = pagos[0]
        print(f"\n📋 Último pago registrado: {ultimo.factura_id} — ${ultimo.monto:,.0f} ({ultimo.fecha_pago})")

    return 0


def cmd_list(args):
    """Lista todas las facturas registradas."""
    store = FacturaStore()
    facturas = store.listar()
    hoy = date.today()

    if not facturas:
        print("📭 No hay facturas registradas")
        return 0

    print(f"📋 {len(facturas)} factura(s) registrada(s):\n")
    for f in facturas:
        estado = "✅" if f.activo else "⏸"
        d = f.dias_para_vencimiento(hoy)
        print(f"  {estado} {f.nombre} ({f.id})")
        print(f"     Vence día {f.dia_vencimiento} — {d} días")
        print(f"     Responsable: {f.responsable}")
        print()

    # Próximos vencimientos
    proximas = store.proximos_vencimientos(dias=7)
    if proximas:
        print(f"🔔 Próximos vencimientos (7 días):")
        for f, d in proximas:
            print(f"  • {f.nombre} — {d} día(s)")

    return 0


def cmd_add(args):
    """Agrega una factura nueva (interactivo o por args)."""
    store = FacturaStore()

    if args.nombre and args.id:
        factura = FacturaProgramada(
            id=args.id,
            nombre=args.nombre,
            proveedor=args.proveedor or args.nombre,
            dia_vencimiento=args.dia or 15,
            responsable=args.responsable or "Ventas",
            monto_estimado=args.monto,
            notas=args.notas or "",
        )
        store.agregar(factura)
        print(f"✅ Factura '{factura.nombre}' agregada")
    else:
        print("Modo interactivo no implementado. Usá flags:")
        print("  --id starlink --nombre \"Starlink\" --dia 10 --responsable Ventas")
        return 1
    return 0


def cmd_pagar(args):
    """Registra un pago."""
    store = FacturaStore()
    pago = Pago(
        factura_id=args.id,
        monto=args.monto,
        fecha_pago=date.today(),
        periodo=args.periodo or date.today().strftime("%Y-%m"),
        pagado_por=args.pagado_por or "",
    )
    store.registrar_pago(pago)
    print(f"✅ Pago registrado: {pago.factura_id} — ${pago.monto:,.0f} ({pago.periodo})")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Gestión de facturas CRM")
    parser.add_argument("--dias", type=int, default=5, help="Días de anticipación para alertas")

    sub = parser.add_subparsers(dest="cmd")
    
    check_p = sub.add_parser("check", help="Verificar y notificar vencimientos")
    check_p.add_argument("--dias", type=int, default=5, help="Días de anticipación para alertas")
    
    sub.add_parser("list", help="Listar facturas registradas")
    
    add_p = sub.add_parser("add", help="Agregar nueva factura")
    add_p.add_argument("--id", required=True)
    add_p.add_argument("--nombre", required=True)
    add_p.add_argument("--proveedor")
    add_p.add_argument("--dia", type=int, default=15)
    add_p.add_argument("--responsable", default="Ventas")
    add_p.add_argument("--monto", type=float)
    add_p.add_argument("--notas")
    
    pagar_p = sub.add_parser("pagar", help="Registrar pago")
    pagar_p.add_argument("--id", required=True)
    pagar_p.add_argument("--monto", type=float, required=True)
    pagar_p.add_argument("--periodo")
    pagar_p.add_argument("--pagado-por")

    args = parser.parse_args()
    
    commands = {
        "check": cmd_check,
        "list": cmd_list,
        "add": cmd_add,
        "pagar": cmd_pagar,
    }
    
    fn = commands.get(args.cmd)
    if not fn:
        parser.print_help()
        return 1
    
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
