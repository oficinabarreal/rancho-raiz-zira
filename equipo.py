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
    # Los datos de huéspedes reales se cargan desde crm_state/huespedes.json
    # (excluido del repositorio via .gitignore). Esta lista es solo para
    # desarrollo local y nunca debe contener datos personales en GitHub.
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
