"""
facturas/store.py — Persistencia JSON para facturas en crm_state/.
"""

import json
from datetime import date
from pathlib import Path
from typing import List, Optional

from crm.facturas.models import FacturaProgramada, Pago

# Los datos se guardan en crm_state/ (excluido del repo por .gitignore)
STATE_DIR = Path(__file__).resolve().parent.parent.parent / "crm_state" / "facturas"


class FacturaStore:
    """Store para facturas programadas y pagos."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.dir = state_dir or STATE_DIR
        self.dir.mkdir(parents=True, exist_ok=True)
        self._facturas_file = self.dir / "facturas.json"
        self._pagos_file = self.dir / "pagos.json"

    # ─── Facturas Programadas ──────────────────────────────────────

    def listar(self) -> List[FacturaProgramada]:
        """Retorna todas las facturas programadas activas."""
        if not self._facturas_file.exists():
            return self._defaults()
        data = json.loads(self._facturas_file.read_text())
        return [FacturaProgramada.from_dict(d) for d in data]

    def _defaults(self) -> List[FacturaProgramada]:
        """Crea facturas por defecto si no existe el archivo."""
        defaults = [
            FacturaProgramada(
                id="luz_epre",
                nombre="Luz EPE",
                proveedor="EPE",
                dia_vencimiento=15,
                responsable="Ventas",
                categoria="servicio",
                notas="Factura de luz del hospedaje. Llega por mail."
            ),
            FacturaProgramada(
                id="starlink",
                nombre="Starlink Internet",
                proveedor="Starlink",
                dia_vencimiento=10,
                responsable="Ventas",
                categoria="internet",
                notas="Internet satelital Starlink. Pago mensual."
            ),
        ]
        self.guardar(defaults)
        return defaults

    def guardar(self, facturas: List[FacturaProgramada]) -> None:
        """Guarda la lista de facturas."""
        self._facturas_file.write_text(
            json.dumps([f.to_dict() for f in facturas], indent=2, ensure_ascii=False)
        )

    def obtener(self, factura_id: str) -> Optional[FacturaProgramada]:
        """Busca una factura por ID."""
        for f in self.listar():
            if f.id == factura_id:
                return f
        return None

    def agregar(self, factura: FacturaProgramada) -> None:
        """Agrega una nueva factura."""
        facturas = self.listar()
        facturas.append(factura)
        self.guardar(facturas)

    # ─── Pagos ─────────────────────────────────────────────────────

    def listar_pagos(self, factura_id: Optional[str] = None) -> List[Pago]:
        """Retorna pagos, opcionalmente filtrados por factura."""
        if not self._pagos_file.exists():
            return []
        data = json.loads(self._pagos_file.read_text())
        pagos = [Pago.from_dict(d) for d in data]
        if factura_id:
            pagos = [p for p in pagos if p.factura_id == factura_id]
        return sorted(pagos, key=lambda p: p.fecha_pago, reverse=True)

    def registrar_pago(self, pago: Pago) -> None:
        """Registra un pago realizado."""
        pagos = self.listar_pagos()
        pagos.append(pago)
        self._pagos_file.write_text(
            json.dumps([p.to_dict() for p in pagos], indent=2, ensure_ascii=False)
        )

    # ─── Utilidad ──────────────────────────────────────────────────

    def proximos_vencimientos(self, dias: int = 5) -> List[tuple]:
        """Retorna facturas que vencen en los próximos N días.
        Retorna [(factura, dias_restantes), ...]
        """
        hoy = date.today()
        result = []
        for f in self.listar():
            if not f.activo:
                continue
            d = f.dias_para_vencimiento(hoy)
            if 0 <= d <= dias:
                result.append((f, d))
        return sorted(result, key=lambda x: x[1])
