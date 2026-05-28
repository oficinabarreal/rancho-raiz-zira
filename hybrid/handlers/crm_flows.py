"""
Puente de compatibilidad: re-exporta todos los handlers desde flows/.
Nuevo codigo debe importar directamente desde flows.{central_crm,arte}.
"""
from flows.central_crm.engine import (
    init_parser, nueva_reserva, procesar_incidente,
    procesar_pago, generar_informe,
)
from flows.arte.banner_flows import generar_banner
from flows.arte.reel_pipeline import generar_reel as generar_reel_handler
