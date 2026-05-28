from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SHIZUKU_BIN = os.environ.get("SHIZUKU_BIN", "shizuku")


def _sh(command: str, timeout: int = 20) -> Tuple[str, str, int]:
    """Ejecuta comando via Shizuku. Extrae output real limpiando marcadores AnyClaw."""
    for attempt in range(2):
        try:
            r = subprocess.run(
                [SHIZUKU_BIN, "-c", command],
                capture_output=True, text=True, timeout=timeout
            )
            raw = r.stderr + r.stdout
            # Buscar contenido XML: extraer desde <?xml hasta </hierarchy>
            xml_match = re.search(r'(<\?xml\s+[^>]+>.*?</hierarchy>)', raw, re.DOTALL)
            if xml_match:
                return xml_match.group(1).strip(), "", r.returncode
            # Si no es XML, buscar texto significativo entre marcadores
            clean = re.sub(
                r'__?[A-Z_]+_\d+__?\s*|_*ANYCLAW_SHIZUKU_EXIT_\d+_*\s*|^\d+\s*',
                '', raw
            ).strip()
            if clean:
                return clean, "", r.returncode
            if attempt == 0:
                time.sleep(2)
                continue
            return "", "", r.returncode
        except (subprocess.TimeoutExpired, OSError) as e:
            if attempt == 0:
                time.sleep(2)
                continue
            return "", f"shizuku error: {e}", -1
    return "", "shizuku unavailable", -1


def _sh_available() -> bool:
    """Verifica si Shizuku está respondiendo."""
    out, _, _ = _sh("echo ping", timeout=5)
    return bool(out) and "ping" in out


@dataclass
class UIElement:
    text: str
    resource_id: str
    class_name: str
    package: str
    content_desc: str
    bounds: str
    clickable: bool
    checkable: bool
    checked: bool
    enabled: bool
    focusable: bool
    focused: bool
    scrollable: bool
    long_clickable: bool
    password: bool
    selected: bool
    index: int

    @property
    def center(self) -> Tuple[int, int]:
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', self.bounds)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        return (0, 0)

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', self.bounds)
        if m:
            return tuple(map(int, m.groups()))
        return (0, 0, 0, 0)


class CuaManager:
    """CUA (Computer Use Agent) para Android via Shizuku.

    Permite al LLM inspeccionar y controlar la interfaz gráfica del dispositivo
    usando comandos nativos de Android (uiautomator, input, screencap) a través de Shizuku.
    """

    SCREENSHOT_DIR = "/sdcard/cua_screenshots"

    def __init__(self):
        self._device_w: int = 0
        self._device_h: int = 0
        self._detect_resolution()

    def _detect_resolution(self):
        out, _, _ = _sh("wm size")
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            self._device_w, self._device_h = int(m.group(1)), int(m.group(2))
        else:
            self._device_w, self._device_h = 720, 1600

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self._device_w, self._device_h)

    # ── UI Hierarchy ──────────────────────────────────────────────

    def dump_ui(self, compressed: bool = True) -> List[UIElement]:
        path = "/sdcard/cua_ui_dump.xml"
        flag = "--compressed " if compressed else ""
        out, err, code = _sh(f"uiautomator dump {flag}{path}", timeout=25)
        if code != 0:
            if "shizuku" in err.lower():
                return []
            logger.warning(f"uiautomator dump failed: {err}")
            return []
        xml_str, _, _ = _sh(f"cat {path}", timeout=10)
        if not xml_str or not xml_str.startswith("<"):
            return []
        return self._parse_ui_xml(xml_str)

    def dump_ui_raw(self, compressed: bool = True) -> str:
        path = "/sdcard/cua_ui_dump.xml"
        flag = "--compressed " if compressed else ""
        out, err, code = _sh(f"uiautomator dump {flag}{path}")
        if code != 0:
            return f"<!-- dump failed: {err} -->"
        xml_str, _, _ = _sh(f"cat {path}")
        return xml_str

    def _parse_ui_xml(self, xml_str: str) -> List[UIElement]:
        elements = []
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return elements

        def walk(node):
            attrs = node.attrib
            elem = UIElement(
                text=attrs.get("text", ""),
                resource_id=attrs.get("resource-id", ""),
                class_name=attrs.get("class", ""),
                package=attrs.get("package", ""),
                content_desc=attrs.get("content-desc", ""),
                bounds=attrs.get("bounds", ""),
                clickable=attrs.get("clickable", "false") == "true",
                checkable=attrs.get("checkable", "false") == "true",
                checked=attrs.get("checked", "false") == "true",
                enabled=attrs.get("enabled", "true") == "true",
                focusable=attrs.get("focusable", "false") == "true",
                focused=attrs.get("focused", "false") == "true",
                scrollable=attrs.get("scrollable", "false") == "true",
                long_clickable=attrs.get("long-clickable", "false") == "true",
                password=attrs.get("password", "false") == "true",
                selected=attrs.get("selected", "false") == "true",
                index=int(attrs.get("index", "0")),
            )
            elements.append(elem)
            for child in node:
                walk(child)

        walk(root)
        return elements

    def ui_text_summary(self, max_elements: int = 80) -> str:
        """Resumen legible de la UI actual para mostrar al LLM."""
        elements = self.dump_ui()
        lines = []
        clickable = [e for e in elements if e.clickable and e.enabled]
        shown = 0
        for e in clickable:
            if shown >= max_elements:
                break
            label = e.text or e.content_desc or e.resource_id or f"<{e.class_name}>"
            cx, cy = e.center
            lines.append(f"  [{shown}] {label} @ ({cx},{cy}) bounds={e.bounds}")
            shown += 1
        header = f"Pantalla: {self._device_w}x{self._device_h} | {len(elements)} nodos | {len(clickable)} elementos cliqueables"
        return header + "\n" + "\n".join(lines)

    # ── Screenshot ────────────────────────────────────────────────

    def screenshot(self, filename: str = "") -> str:
        if not filename:
            filename = f"screen_{int(time.time())}.png"
        path = f"{self.SCREENSHOT_DIR}/{filename}"
        out, err, code = _sh(f"screencap -p {path}")
        if code != 0:
            logger.warning(f"screenshot failed: {err}")
            return ""
        return path

    # ── Actions ───────────────────────────────────────────────────

    def tap(self, x: int, y: int) -> bool:
        out, err, code = _sh(f"input tap {x} {y}")
        if code != 0:
            logger.warning(f"tap({x},{y}) failed: {err}")
            return False
        return True

    def tap_element(self, ui_element: UIElement) -> bool:
        cx, cy = ui_element.center
        return self.tap(cx, cy)

    def tap_by_text(self, text: str, exact: bool = True) -> bool:
        elements = self.dump_ui()
        for e in elements:
            if not e.clickable or not e.enabled:
                continue
            if exact and e.text == text:
                return self.tap_element(e)
            if not exact and text.lower() in e.text.lower():
                return self.tap_element(e)
        return False

    def tap_by_resource_id(self, resource_id: str) -> bool:
        elements = self.dump_ui()
        for e in elements:
            if e.resource_id == resource_id and e.clickable and e.enabled:
                return self.tap_element(e)
        return False

    def input_text(self, text: str) -> bool:
        safe = text.replace("'", "'\\''").replace(" ", "%s")
        out, err, code = _sh(f"input text {shlex_quote(text)}")
        if code != 0:
            # try alternative: send keys via uiautomator
            logger.warning(f"input_text failed: {err}")
            return False
        return True

    def press_key(self, keycode: str) -> bool:
        key_map = {
            "home": "KEYCODE_HOME",
            "back": "KEYCODE_BACK",
            "enter": "KEYCODE_ENTER",
            "menu": "KEYCODE_MENU",
            "search": "KEYCODE_SEARCH",
            "power": "KEYCODE_POWER",
            "volume_up": "KEYCODE_VOLUME_UP",
            "volume_down": "KEYCODE_VOLUME_DOWN",
            "del": "KEYCODE_DEL",
            "tab": "KEYCODE_TAB",
            "space": "KEYCODE_SPACE",
            "escape": "KEYCODE_ESCAPE",
            "app_switch": "KEYCODE_APP_SWITCH",
            "clear": "KEYCODE_CLEAR",
            "camera": "KEYCODE_CAMERA",
            "notification": "KEYCODE_NOTIFICATION",
            "settings": "KEYCODE_SETTINGS",
        }
        key = key_map.get(keycode.lower(), keycode)
        out, err, code = _sh(f"input keyevent {key}")
        if code != 0:
            logger.warning(f"press_key({keycode}) failed: {err}")
            return False
        return True

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        out, err, code = _sh(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
        if code != 0:
            logger.warning(f"swipe failed: {err}")
            return False
        return True

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        return self.swipe(x, y, x, y, duration_ms)

    def scroll_down(self) -> bool:
        h = self._device_h
        w = self._device_w
        return self.swipe(w // 2, int(h * 0.7), w // 2, int(h * 0.3))

    def scroll_up(self) -> bool:
        h = self._device_h
        w = self._device_w
        return self.swipe(w // 2, int(h * 0.3), w // 2, int(h * 0.7))

    def open_app(self, package_name: str) -> bool:
        out, err, code = _sh(f"monkey -p {package_name} 1")
        if code != 0:
            logger.warning(f"open_app({package_name}) failed: {err}")
            return False
        return True

    def go_home(self) -> bool:
        return self.press_key("home")

    def go_back(self) -> bool:
        return self.press_key("back")

    def wait(self, seconds: float):
        time.sleep(seconds)

    # ── High Level ────────────────────────────────────────────────

    def find_elements(self, text: str = "", resource_id: str = "", class_name: str = "") -> List[UIElement]:
        elements = self.dump_ui()
        results = []
        for e in elements:
            if text and text.lower() not in e.text.lower() and text.lower() not in e.content_desc.lower():
                continue
            if resource_id and e.resource_id != resource_id:
                continue
            if class_name and e.class_name != class_name:
                continue
            results.append(e)
        return results

    def get_screen_state(self) -> Dict[str, Any]:
        """Snapshot completo del estado actual de la pantalla."""
        elements = self.dump_ui()
        clickable = [e for e in elements if e.clickable]
        return {
            "resolution": f"{self._device_w}x{self._device_h}",
            "total_nodes": len(elements),
            "clickable_count": len(clickable),
            "elements": [
                {
                    "text": e.text,
                    "resource_id": e.resource_id,
                    "class": e.class_name,
                    "bounds": e.bounds,
                    "center": list(e.center),
                    "clickable": e.clickable,
                    "enabled": e.enabled,
                    "focused": e.focused,
                    "scrollable": e.scrollable,
                    "content_desc": e.content_desc,
                }
                for e in clickable[:60]
            ],
            "screenshot": self.screenshot(),
        }
