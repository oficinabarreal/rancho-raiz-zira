"""
facturas/models.py — Modelos de datos para facturas programadas y pagos.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from typing import Optional


@dataclass
class FacturaProgramada:
    """Una factura recurrente que el CRM debe recordar pagar."""
    id: str                                  # identificador único (ej: "luz_epre", "starlink")
    nombre: str                              # nombre visible (ej: "Luz EPE")
    proveedor: str                           # nombre del proveedor
    dia_vencimiento: int                     # día del mes (1-31)
    periodicidad: str = "mensual"            # "mensual" | "bimestral"
    monto_estimado: Optional[float] = None   # monto estimado en ARS
    responsable: str = "Ventas"              # quién recibe el recordatorio
    notificar_dias_antes: int = 3            # días antes del vencimiento
    activo: bool = True                      # si está activo
    categoria: str = "servicio"              # "servicio" | "internet" | "impuesto"
    notas: str = ""

    def dias_para_vencimiento(self, hoy: Optional[date] = None) -> int:
        """Días restantes hasta el próximo vencimiento."""
        hoy = hoy or date.today()
        mes = hoy.month
        año = hoy.year
        
        # Determinar próximo vencimiento
        try:
            prox = date(año, mes, self.dia_vencimiento)
        except ValueError:
            prox = date(año, mes, 28)  # fin de mes
        if prox <= hoy:
            # Pasar al mes siguiente
            mes += 1
            if mes > 12:
                mes = 1
                año += 1
            try:
                prox = date(año, mes, self.dia_vencimiento)
            except ValueError:
                prox = date(año, mes, 28)
        
        return (prox - hoy).days

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FacturaProgramada":
        return cls(**d)


@dataclass
class Pago:
    """Registro de un pago realizado."""
    factura_id: str
    monto: float
    fecha_pago: date
    periodo: str              # ej: "2026-05"
    comprobante: str = ""      # path o descripción del comprobante
    pagado_por: str = ""
    notas: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fecha_pago"] = self.fecha_pago.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Pago":
        d["fecha_pago"] = date.fromisoformat(d["fecha_pago"])
        return cls(**d)
