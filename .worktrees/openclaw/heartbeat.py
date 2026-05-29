#!/usr/bin/env python3
"""
Heartbeat — Persistencia de estado entre agentes.
Registra latidos y verificaciones de Hermes y OpenClaw en archivo compartido.

Uso:
  python3 heartbeat.py --beat AGENT [--task TASK]
  python3 heartbeat.py --status
  python3 heartbeat.py --prune
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent  / "hola-3" if HERE.parent.name == "Codex" else HERE.parent
HEARTBEAT_FILE = HERE / "heartbeats.json"


def load() -> dict:
    if HEARTBEAT_FILE.exists():
        return json.loads(HEARTBEAT_FILE.read_text())
    return {"beats": [], "tasks": {}}


def save(data: dict):
    HEARTBEAT_FILE.write_text(json.dumps(data, indent=2))


def beat(agent: str, task: str = ""):
    data = load()
    entry = {
        "agent": agent,
        "ts": datetime.now().isoformat(),
        "unix": int(time.time()),
        "task": task or "heartbeat",
    }
    data["beats"].append(entry)
    # Mantener solo los ultimos 100 beats
    data["beats"] = data["beats"][-100:]
    save(data)
    print(f"Heartbeat {agent}: {entry['task']} ✅")


def status() -> str:
    data = load()
    if not data["beats"]:
        return "No heartbeats registrados"

    beats = data["beats"]
    agents = {}
    for b in beats:
        a = b["agent"]
        if a not in agents or b["unix"] > agents[a]["unix"]:
            agents[a] = b

    now = int(time.time())
    lines = []
    for agent, last in sorted(agents.items()):
        ago = now - last["unix"]
        ago_s = f"{ago}s" if ago < 60 else f"{ago // 60}m{ago % 60}s"
        status_icon = "✅" if ago < 600 else "⚠️" if ago < 3600 else "❌"
        lines.append(f"  {status_icon} {agent}: hace {ago_s} — {last['task']}")

    lines.append(f"\n  Total beats: {len(beats)}")
    tasks = data.get("tasks", {})
    if tasks:
        lines.append(f"  Tareas activas: {len(tasks)}")

    return "\n".join(lines)


def prune(hours: int = 24):
    data = load()
    cutoff = int(time.time()) - hours * 3600
    before = len(data["beats"])
    data["beats"] = [b for b in data["beats"] if b["unix"] > cutoff]
    after = len(data["beats"])
    print(f"Prune: {before - after} beats eliminados (>{hours}h)")
    save(data)


def register_task(task_id: str, description: str):
    data = load()
    data["tasks"][task_id] = {
        "description": description,
        "created": datetime.now().isoformat(),
        "status": "running",
    }
    save(data)
    print(f"Tarea registrada: {task_id}")


def complete_task(task_id: str):
    data = load()
    if task_id in data["tasks"]:
        data["tasks"][task_id]["status"] = "completed"
        data["tasks"][task_id]["completed_at"] = datetime.now().isoformat()
        save(data)
        print(f"Tarea completada: {task_id}")
    else:
        print(f"Tarea no encontrada: {task_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "--beat":
        agent = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        task = sys.argv[3] if len(sys.argv) > 3 else ""
        beat(agent, task)
    elif cmd == "--status":
        print(status())
    elif cmd == "--prune":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        prune(hours)
    elif cmd == "--register":
        register_task(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "--complete":
        complete_task(sys.argv[2])
    else:
        print(f"Comando desconocido: {cmd}")
