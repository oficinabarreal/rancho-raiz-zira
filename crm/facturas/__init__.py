"""
facturas/__init__.py — Módulo de gestión de facturas y recordatorios de pago.

Uso:
  from crm.facturas.store import FacturaStore
  store = FacturaStore()
  store.listar()
  
Arquitectura:
  - Los datos de facturas se guardan en crm_state/facturas/ (excluido del repo)
  - Las notificaciones van por Telegram al responsable
  - Los recordatorios se disparan desde el cron diario de Hermes
"""

from crm.facturas.models import FacturaProgramada, Pago
from crm.facturas.store import FacturaStore

__all__ = ["FacturaProgramada", "Pago", "FacturaStore"]
