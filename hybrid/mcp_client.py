from __future__ import annotations
import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

MCP_SERVER_PATH = os.environ.get(
    "MCP_SERVER_PATH",
    str(Path.home() / "Documents/proyectos/test-mcp-render/server.py")
)
CHROMIUM_PATH = os.environ.get(
    "CHROMIUM_PATH",
    "/data/data/com.termux/files/usr/bin/chromium-browser"
)
MCP_RENDER_OUTPUT = os.environ.get(
    "MCP_RENDER_OUTPUT",
    str(Path(__file__).resolve().parent / "crm_state" / "media")
)


async def _call_mcp_tool(tool_name: str, arguments: dict, timeout: int = 30) -> dict:
    """Lanza el servidor MCP como subproceso, envía un tool call y devuelve el resultado."""
    env = os.environ.copy()
    env["CHROMIUM_PATH"] = CHROMIUM_PATH
    env["MCP_RENDER_OUTPUT"] = MCP_RENDER_OUTPUT

    proc = await asyncio.create_subprocess_exec(
        sys.executable, MCP_SERVER_PATH,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    msg_id = 0

    async def send(method: str, params: dict) -> None:
        nonlocal msg_id
        msg_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params,
        }
        line = json.dumps(req) + "\n"
        proc.stdin.write(line.encode())
        await proc.stdin.drain()

    async def notify(method: str, params: dict) -> None:
        req = {"jsonrpc": "2.0", "method": method, "params": params}
        line = json.dumps(req) + "\n"
        proc.stdin.write(line.encode())
        await proc.stdin.drain()

    async def recv(expected_id: int) -> dict:
        buf = b""
        while True:
            chunk = await asyncio.wait_for(proc.stdout.read(65536), timeout=timeout)
            if not chunk:
                raise RuntimeError("MCP server closed connection unexpectedly")
            buf += chunk
            try:
                resp = json.loads(buf.decode("utf-8"))
                if resp.get("id") == expected_id:
                    return resp
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    try:
        await send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "hybrid-server", "version": "2.0.0"},
        })
        init_resp = await recv(1)
        if "error" in init_resp:
            raise RuntimeError(f"MCP init error: {init_resp['error']}")

        await notify("notifications/initialized", {})

        await send("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        call_resp = await recv(2)

        if "error" in call_resp:
            raise RuntimeError(f"MCP tool error: {call_resp['error']}")

        content = call_resp.get("result", {}).get("content", [])
        return {"content": content, "meta": call_resp.get("result", {}).get("meta", {})}

    except asyncio.TimeoutError:
        raise RuntimeError(f"MCP server timeout after {timeout}s")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"MCP response parse error: {e}")
    except Exception as e:
        raise RuntimeError(f"MCP communication error: {e}")
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()


async def html_a_imagen(
    html: str,
    width: int = 1080,
    height: int = 1080,
    fmt: str = "png",
    quality: int = 90,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Convierte HTML a imagen usando el servidor MCP local.

    Args:
        html: Código HTML completo con CSS inline.
        width: Ancho en píxeles (default 1080).
        height: Alto en píxeles (default 1080).
        fmt: Formato 'png' o 'jpeg' (default 'png').
        quality: Calidad JPEG 1-100 (default 90).
        output_path: Ruta opcional de salida.

    Returns:
        Dict con keys: path, size, width, height, format.
        Si no se especificó output_path, el archivo está en MCP_RENDER_OUTPUT.
    """
    arguments = {
        "html": html,
        "width": width,
        "height": height,
        "format": fmt,
        "quality": quality,
    }
    if output_path:
        arguments["output_path"] = output_path

    result = await _call_mcp_tool("html_a_imagen", arguments)
    text = result["content"][0]["text"]
    return json.loads(text)


async def html_a_imagen_bytes(
    html: str,
    width: int = 1080,
    height: int = 1080,
    fmt: str = "png",
    quality: int = 90,
) -> bytes:
    """Convierte HTML a imagen y devuelve los bytes directamente."""
    arguments = {
        "html": html,
        "width": width,
        "height": height,
        "format": fmt,
        "quality": quality,
    }
    result = await _call_mcp_tool("html_a_imagen_bytes", arguments)
    content = result["content"][0]
    raw = base64.b64decode(content["data"])
    return raw
