"""
Integraciones con plataformas externas.
Cada conector sigue el patron BaseConnector/ConnectorResult.
"""
from flows.third_party.kommo_connector import KommoConnector
from flows.third_party.webhook_ingress import webhook_ingress_handler
