from __future__ import annotations
import json, os, re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParseResult:
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    method: str = ""
    error: str = ""


# ── Regex parser (fallback) ─────────────────────────────

def _normalizar_fecha(val: str) -> str:
    val = val.strip()
    for sep in ["/", "-"]:
        parts = val.split(sep)
        if len(parts) == 3:
            y = parts[2]
            if len(y) == 2:
                y = "20" + y if int(y) < 50 else "19" + y
            return f"{parts[0]}{sep}{parts[1]}{sep}{y}"
    return val

def _es_fecha(val: str) -> bool:
    return bool(re.match(r"\d{2,4}[-/]\d{1,2}[-/]\d{1,2}", val.strip()))

def parsear_regex(texto: str) -> ParseResult:
    data = {}

    for p in ["huésped", "huesped", "nombre", "cliente", "guest", "name", "pasajero"]:
        m = re.search(rf"{p}\s*:?\s*([A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+)+)", texto, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().split("\n")[0].strip()
            if len(candidate.split()) <= 4:
                data["name"] = candidate
                break

    if "name" not in data:
        m = re.search(r"(?:reserva|para)\s+(?:de\s+)?([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{2,}(?:\s+[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]{2,}){1,2})", texto, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            forbidden = ["hacer", "quiero", "una", "con", "del", "por", "los", "las", "mi", "este", "esta"]
            if len(candidate.split()) <= 3 and not any(w in candidate.lower() for w in forbidden):
                data["name"] = candidate

    if "name" not in data:
        lines = [l.strip() for l in texto.split("\n") if l.strip()]
        for l in lines:
            words = l.split()
            forbidden = ["pax","check","$","http","tel","email","paga","total","hola","quiero","reserva",
                         "para","somos","llegamos","presupuesto","origen","mi","nombre","personas","entrada",
                         "salida","abonado","datos","teléfono","telefono","total","directo","booking"]
            if 2 <= len(words) <= 3:
                if not any(k in l.lower() for k in forbidden):
                    if re.match(r"^[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑa-záéíóúüñ]+){1,2}$", l):
                        data["name"] = l
                        break

    m = re.search(r"(?:personas|pax|adultos|hu[ée]spedes|invitados)\s*:?\s*(\d+)|(\d+)\s*(?:pax|personas|adultos|hu[ée]spedes|invitados)", texto, re.IGNORECASE)
    if m:
        val = m.group(1) or m.group(2)
        if val:
            data["pax"] = int(val)

    fecha_pat = r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
    fechas = re.findall(fecha_pat, texto)
    if len(fechas) >= 2:
        data["check_in"] = _normalizar_fecha(fechas[0])
        data["check_out"] = _normalizar_fecha(fechas[1])
    elif len(fechas) == 1:
        data["check_in"] = _normalizar_fecha(fechas[0])
        m = re.search(r"(hasta|al|a\s*partir\s*del?)\s*" + fecha_pat, texto)
        if m:
            extra = re.search(fecha_pat, m.group())
            if extra:
                data["check_out"] = _normalizar_fecha(extra.group())

    meses = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06",
             "julio":"07","agosto":"08","septiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}
    if "check_in" not in data:
        for m_nombre, m_num in meses.items():
            pat = rf"(\d{{1,2}})\s*de?\s*{m_nombre}"
            m = re.search(pat, texto, re.IGNORECASE)
            if m:
                dia = m.group(1).zfill(2)
                data["check_in"] = f"{dia}/{m_num}/2026"
                break

    m = re.search(r"\$[\s]*([\d.,]+)", texto)
    if m:
        data["amount"] = m.group(1)
    m = re.search(r"([\d.,]+)\s*(usd|dólares|dolares|ars)", texto, re.IGNORECASE)
    if m and "amount" not in data:
        data["amount"] = m.group(1)

    m = re.search(r"(\+?\d{2,3}[\s-]?\d{2,4}[\s-]?\d{2,4}[\s-]?\d{2,4})", texto)
    if m:
        candidate = m.group(1).strip()
        if not _es_fecha(candidate) and len(candidate) >= 7:
            data["phone"] = candidate

    for src in ["booking", "airbnb", "whatsapp", "instagram", "facebook", "web", "directo", "recomendación"]:
        if src in texto.lower():
            data["source"] = src.capitalize()
            break

    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", texto)
    if m:
        data["email"] = m.group(0)

    m = re.search(r"(\d+)\s*(noches|días|dias)", texto, re.IGNORECASE)
    if m:
        data["nights"] = int(m.group(1))

    score = 0.0
    for c in ["name", "pax", "check_in", "check_out", "amount", "phone"]:
        if c in data:
            score += 1.0 / 6

    if "name" not in data:
        return ParseResult(ok=False, data=data, confidence=0.0, method="regex")
    return ParseResult(ok=True, data=data, confidence=score, method="regex")


# ── IA parser (OpenCode Zen) ────────────────────────────

IA_ENDPOINT = ""
IA_API_KEY = ""
IA_MODEL = ""
IA_FALLBACK_MODELS = [
    "nemotron-3-super-free",
    "minimax-m2.5-free",
    "deepseek-v4-flash-free",
    "big-pickle",
]
IA_LAST_RATE_LIMIT: str | None = None


def configurar_ia(endpoint: str, api_key: str, model: str):
    global IA_ENDPOINT, IA_API_KEY, IA_MODEL
    IA_ENDPOINT = endpoint
    IA_API_KEY = api_key
    IA_MODEL = model


def parsear_con_ia(texto: str, model: str | None = None) -> ParseResult:
    if not IA_ENDPOINT:
        return ParseResult(ok=False, method="ia", error="no IA endpoint configured")

    m = model or IA_MODEL
    if not m:
        return ParseResult(ok=False, method="ia", error="no model configured")

    import requests
    prompt = f"""Extraé los datos de esta reserva y respondé SOLO un JSON sin explicaciones:
{{
  "name": "Nombre completo del huésped",
  "pax": número de personas,
  "check_in": "fecha check-in DD/MM/AAAA",
  "check_out": "fecha check-out DD/MM/AAAA",
  "amount": "monto en string",
  "phone": "teléfono",
  "email": "email",
  "source": "origen (Booking/Airbnb/Directo/etc)",
  "nights": número de noches
}}

Texto:
{texto}"""

    try:
        resp = requests.post(
            IA_ENDPOINT,
            headers={"Authorization": f"Bearer {IA_API_KEY}", "Content-Type": "application/json"},
            json={"model": m, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
            timeout=30
        )
        if resp.status_code == 429:
            return ParseResult(ok=False, method="ia", error="RATE_LIMIT")
        if resp.status_code == 402:
            return ParseResult(ok=False, method="ia", error="NO_CREDITS")
        if not resp.ok:
            return ParseResult(ok=False, method="ia", error=f"API error {resp.status_code}")

        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return ParseResult(ok=True, data=data, confidence=0.9, method=f"ia/{m}")

    except Exception as e:
        return ParseResult(ok=False, method="ia", error=str(e))


# ── Unified parser: IA → rotation → regex → raw ────────

def parsear(texto: str) -> ParseResult:
    global IA_LAST_RATE_LIMIT

    if IA_ENDPOINT and IA_MODEL:
        modelos = [IA_MODEL] + [m for m in IA_FALLBACK_MODELS if m != IA_MODEL]
        for m in modelos:
            r = parsear_con_ia(texto, model=m)
            if r.error == "RATE_LIMIT":
                IA_LAST_RATE_LIMIT = m
                continue
            if r.ok and r.confidence > 0.5:
                return r

    r = parsear_regex(texto)
    if r.ok:
        r.method = "regex"
        return r

    r.error = "RAW_FALLBACK"
    return r
