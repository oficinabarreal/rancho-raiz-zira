"""Parser unificado con IA + regex fallback."""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ParseResult:
    ok: bool
    data: Dict[str, Any]
    method: str = ""
    confidence: float = 0.0
    error: str = ""


IA_ENDPOINT = os.environ.get("CRM_IA_ENDPOINT", "")
IA_API_KEY = os.environ.get("CRM_IA_API_KEY", "")
IA_MODEL = os.environ.get("CRM_IA_MODEL", "")
IA_LAST_RATE_LIMIT: Optional[str] = None


def configurar_ia(endpoint: str, api_key: str, model: str):
    global IA_ENDPOINT, IA_API_KEY, IA_MODEL
    IA_ENDPOINT = endpoint
    IA_API_KEY = api_key
    IA_MODEL = model


def _llm_parse(text: str) -> ParseResult:
    if not IA_ENDPOINT:
        return ParseResult(ok=False, data={}, method="none", error="IA no configurada")
    try:
        body = json.dumps({
            "model": IA_MODEL,
            "messages": [
                {"role": "system", "content": "Extrae datos de reserva hotelera en JSON. Devuelve SOLO JSON."},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        }).encode("utf-8")
        req = urllib.request.Request(
            IA_ENDPOINT,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {IA_API_KEY}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.DOTALL)
            parsed = json.loads(content)
            return ParseResult(
                ok=True,
                data=parsed,
                method="ia",
                confidence=0.85,
            )
    except urllib.error.HTTPError as e:
        if e.code == 429:
            global IA_LAST_RATE_LIMIT
            IA_LAST_RATE_LIMIT = e.headers.get("Retry-After", "?")
        return ParseResult(ok=False, data={}, method="ia", error=str(e))
    except Exception as e:
        return ParseResult(ok=False, data={}, method="ia", error=str(e))


def _regex_parse(text: str) -> ParseResult:
    data: Dict[str, Any] = {}
    methods_used: list[str] = []

    patterns = {
        "name": [
            (r"(?:para|de|soy|del\s+Sr\.?|del\s+Sra\.?|nombre\s+del\s+huésped\s+es)\s+([A-ZÁÉÍÓÚÜÑa-záéíóúüñ\s]+?)(?:\s+para|\s+$|\s+\d)", 1),
            (r"(?:reserva|habitación|habitacion)\s+(?:a\s+)?(?:nombre\s+de\s+)?([A-ZÁÉÍÓÚÜÑa-záéíóúüñ\s]+?)(?:\s+para|\s+$|\s+el\s+\d+)", 1),
            (r"^([A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+\s+[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+)", 1),
        ],
        "pax": [
            (r"(\d+)\s*(?:pax|personas|adultos|huéspedes|huespedes|invitados)", 1),
            (r"(?:para|son)\s*(\d+)\s*(?:personas|adultos)", 1),
        ],
        "check_in": [
            (r"(?:check[- ]?in|entrada|llegada|desde\s+el|ingreso)\s*(?:\s*[:\s]*)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})", 1),
            (r"(?:check[- ]?in|entrada|llegada|desde\s+el|ingreso)\s*(?:\s*[:\s]*)?(\d{1,2}\s+de\s+[a-záéíóúüñ]+\s+de\s+\d{2,4})", 1),
        ],
        "check_out": [
            (r"(?:check[- ]?out|salida|hasta\s+el|egreso)\s*(?:\s*[:\s]*)?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})", 1),
            (r"(?:check[- ]?out|salida|hasta\s+el|egreso)\s*(?:\s*[:\s]*)?(\d{1,2}\s+de\s+[a-záéíóúüñ]+\s+de\s+\d{2,4})", 1),
        ],
        "amount": [
            (r"(?:monto|presupuesto|total|costo|precio|valor|pag[oó]|abon[oó])\s*(?:\$|usd|ars)?\s*([\d.,]+)\s*(?:\$|usd|ars|pesos|dólares|dolares)?", 1),
            (r"\$?\s*([\d.,]+)\s*(?:usd|ars|dólares|dolares|pesos)", 1),
            (r"(?:abon[oó]|pag[oó]|deposit[oó]|transferencia)\s*(?:\$|usd|ars)?\s*([\d.,]+)", 1),
        ],
        "phone": [
            (r"(?:teléfono|telefono|celular|whatsapp|contacto|cel|tel)\s*(?::|:)\s*(\+?\d[\d\s\-\(\)]{6,20})", 1),
            (r"(\+?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4})", 1),
        ],
        "nights": [
            (r"(\d+)\s*(?:noches|d[ií]as|dias)", 1),
            (r"(?:por|durante)\s*(\d+)\s*(?:noches|d[ií]as|dias)", 1),
        ],
    }

    for key, pattern_list in patterns.items():
        for pat, group in pattern_list:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(group).strip()
                if key == "pax" or key == "nights":
                    try:
                        data[key] = int(re.sub(r"[^\d]", "", val))
                    except ValueError:
                        data[key] = val
                elif key == "amount":
                    val_clean = re.sub(r"[^\d.,]", "", val)
                    val_clean = val_clean.replace(",", ".")
                    try:
                        data[key] = float(re.sub(r"[^\d.]", "", val_clean))
                    except ValueError:
                        data[key] = val
                elif key in ("check_in", "check_out"):
                    data[key] = val
                else:
                    data[key] = val
                methods_used.append(key)
                break

    confidence = min(0.5 + 0.1 * len(methods_used), 0.9)
    return ParseResult(
        ok=bool(methods_used),
        data=data,
        method="regex+" if len(methods_used) >= 2 else "regex",
        confidence=confidence,
    )


def parsear(text: str) -> ParseResult:
    text = text.strip()
    if not text:
        return ParseResult(ok=False, data={}, method="none", error="texto vacio")

    ia_result = _llm_parse(text)
    if ia_result.ok:
        return ia_result

    return _regex_parse(text)
