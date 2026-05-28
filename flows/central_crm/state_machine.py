"""
Maquina de estados finitos del pipeline CRM.
Cada cliente avanza linealmente a traves de estos estados.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional


class PipelineState(str, Enum):
    CAPTACION_TELEGRAM = "CAPTACION_TELEGRAM"
    CREACION_CONTENIDO = "CREACION_CONTENIDO"
    ESPERA_APROBACION = "ESPERA_APROBACION"
    POSTEO_ACTIVO = "POSTEO_ACTIVO"
    INTERACCION_INSTAGRAM = "INTERACCION_INSTAGRAM"
    CALENTAMIENTO_LEAD = "CALENTAMIENTO_LEAD"
    DERIVACION_WHATSAPP = "DERIVACION_WHATSAPP"
    ACOMPANAMIENTO_VIAJE = "ACOMPANAMIENTO_VIAJE"
    HISTORIAL_ARCHIVADO = "HISTORIAL_ARCHIVADO"


PIPELINE_ORDER = [
    PipelineState.CAPTACION_TELEGRAM,
    PipelineState.CREACION_CONTENIDO,
    PipelineState.ESPERA_APROBACION,
    PipelineState.POSTEO_ACTIVO,
    PipelineState.INTERACCION_INSTAGRAM,
    PipelineState.CALENTAMIENTO_LEAD,
    PipelineState.DERIVACION_WHATSAPP,
    PipelineState.ACOMPANAMIENTO_VIAJE,
    PipelineState.HISTORIAL_ARCHIVADO,
]


class PipelineFSM:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.current_state: PipelineState = PipelineState.CAPTACION_TELEGRAM
        self.context: Dict[str, Any] = {}

    def advance(self) -> Optional[PipelineState]:
        idx = PIPELINE_ORDER.index(self.current_state)
        if idx + 1 < len(PIPELINE_ORDER):
            self.current_state = PIPELINE_ORDER[idx + 1]
            return self.current_state
        return None

    def can_advance_to(self, target: PipelineState) -> bool:
        idx_cur = PIPELINE_ORDER.index(self.current_state)
        idx_tgt = PIPELINE_ORDER.index(target)
        return idx_tgt == idx_cur + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "current_state": self.current_state.value,
            "context": self.context,
        }
