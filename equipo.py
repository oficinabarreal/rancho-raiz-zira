from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

BASE = Path(__file__).resolve().parent / "crm_state"

EQUIPO = {
    "leo": {
        "nombre": "Leo Tello",
        "rol": "Dueño / Finanzas",
        "email": "ltelloraiz@gmail.com",
        "telefono": "+54 9 264 548-0313",
        "responsabilidades": [
            "Aprobar reservas mayores",
            "Manejar finanzas y pagos",
            "Decisiones de reposición y stock",
            "Visto bueno en contratos",
        ],
        "tono": "directivo, paternal, confía en Diego para operaciones",
        "alias": ["Leo", "Tello", "ltelloraiz"],
    },
    "ayelen": {
        "nombre": "Ayelen Juricevic",
        "rol": "Booking / Ventas",
        "email": "ayelenjuricevic@gmail.com",
        "telefono": "+54 9 11 5959-5869",
        "responsabilidades": [
            "Recibir y confirmar reservas",
            "Pasar contratos a huéspedes",
            "Comunicar datos de reserva al equipo",
            "Cobrar señas",
        ],
        "tono": "organizada, detallista, pasa la info y delega seguimiento",
        "alias": ["Aye", "Ayelen", "Ayelen Juricevic"],
    },
    "diego": {
        "nombre": "Diego",
        "rol": "Operaciones (vos)",
        "email": "oficinabarreal@gmail.com",
        "telefono": "",
        "responsabilidades": [
            "Recibir e instalar huéspedes",
            "Coordinar limpieza con Chiqui",
            "Resolver problemas en la casa",
            "Cobrar pagos en efectivo",
            "Mantener inventario y reposiciones",
            "Gestionar el gimnasio (pesas, etc.)",
        ],
        "tono": "resolutivo, reporta en el grupo, atento a detalles",
        "alias": ["Diego", "Dieguito", "diegui"],
    },
    "chiqui": {
        "nombre": "Chiqui",
        "rol": "Limpieza",
        "email": "",
        "telefono": "",
        "responsabilidades": [
            "Limpieza post-checkout",
            "Preparar la casa para nuevos huéspedes",
        ],
        "alias": ["Chiqui"],
    },
}


HUESPEDES_REGISTRADOS = [
    {
        "nombre": "José Miguel",
        "pax": 4,
        "check_in": "2026-01-31",
        "check_out": "2026-02-05",
        "monto": 345000,
        "origen": "Booking",
        "notas": "Pagó en efectivo. Había tormenta el día de llegada.",
    },
    {
        "nombre": "Anónimo (21-mar)",
        "pax": 1,
        "check_in": "2026-03-21",
        "check_out": "2026-03-22",
        "notas": "Estadía corta, 1 noche.",
    },
    {
        "nombre": "Alejandro Beltrán",
        "pax": 4,
        "check_in": "2026-05-15",
        "check_out": "2026-05-18",
        "monto": 0,
        "origen": "WhatsApp directo",
        "notas": "2 adultos + 2 menores. Tel: +57 321 811 4358. Email: alejandro.beltran@foraco.com",
        "preferencias": [],
    },
    {
        "nombre": "Anónimo (finde mayo)",
        "pax": 2,
        "check_in": "2026-05-01",
        "check_out": "2026-05-03",
        "notas": "Finde de mayo.",
    },
    {
        "nombre": "Andrés Chouhy",
        "pax": 2,
        "check_in": "2026-02-08",
        "check_out": "2026-02-11",
        "notas": "",
    },
    {
        "nombre": "Tomás Scala",
        "pax": 3,
        "check_in": "2026-02-16",
        "check_out": "2026-02-26",
        "notas": "Estadía larga (10 noches).",
    },
    {
        "nombre": "Alvaro Martinez",
        "pax": 0,
        "check_in": "",
        "check_out": "",
        "notas": "Reserva mencionada en chats.",
    },
    {
        "nombre": "Santiago Ruiz",
        "pax": 0,
        "check_in": "",
        "check_out": "",
        "notas": "Reserva mencionada en chats.",
    },
]


def guardar():
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "equipo.json").write_text(json.dumps(EQUIPO, indent=2, ensure_ascii=False))
    (BASE / "huespedes.json").write_text(
        json.dumps(
            {"registrados": HUESPEDES_REGISTRADOS}, indent=2, ensure_ascii=False
        )
    )
    print(f"✅ Perfiles guardados en {BASE}/")


def mostrar():
    print("=" * 60)
    print("EQUIPO RANCHO RAÍZ")
    print("=" * 60)
    for key, m in EQUIPO.items():
        print(f"\n👤 {m['nombre']} — {m['rol']}")
        print(f"   📧 {m['email']}")
        print(f"   📱 {m.get('telefono', '—')}")
        print(f"   Responsabilidades:")
        for r in m["responsabilidades"]:
            print(f"     • {r}")

    print(f"\n{'='*60}")
    print(f"HUÉSPEDES REGISTRADOS: {len(HUESPEDES_REGISTRADOS)}")
    print("=" * 60)
    for h in HUESPEDES_REGISTRADOS:
        fechas = f"{h['check_in']} → {h['check_out']}" if h["check_in"] else "Fechas pendientes"
        print(f"  🧑 {h['nombre']} ({h.get('pax', '?')}pax) {fechas}")
        if h.get("notas"):
            print(f"     {h['notas']}")


if __name__ == "__main__":
    mostrar()
    guardar()
