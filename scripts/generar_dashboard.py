#!/usr/bin/env python3
"""
generar_dashboard.py — Genera el dashboard HTML para GitHub Pages.

Usa datos de:
  - Estado local (git, tests, facturas) si está disponible
  - GitHub API (workflow runs, simulación, tests)
  - Facturas (solo si existe crm_state/ local)

Uso:
  python3 scripts/generar_dashboard.py          # genera index.html
  python3 scripts/generar_dashboard.py --push    # genera + pushea a gh-pages

Requiere GITHUB_TOKEN en entorno para consultar API (opcional si solo data local).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
GH_REPO = "oficinabarreal/rancho-raiz-zira"
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")


# ─── Recolectores de datos ─────────────────────────────────────────

def get_git_info():
    """Rama, último commit, estado."""
    info = {"branch": "?", "last_commit": "?", "status": "clean"}
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=10
        ).stdout.strip()
        if branch:
            info["branch"] = branch
    except: pass

    try:
        commit = subprocess.run(
            ["git", "log", "-1", "--format=%h %s (%ar)"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=10
        ).stdout.strip()
        if commit:
            info["last_commit"] = commit
    except: pass

    try:
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=10
        ).stdout.strip()
        if st:
            info["status"] = f"{len(st.splitlines())} archivo(s) modificado(s)"
    except: pass

    return info


def get_test_status():
    """Resultado de unittest discover."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=30
        )
        output = result.stdout.strip() + " " + result.stderr.strip()
        # Extraer el resumen final (última línea no vacía)
        lines = [l for l in output.split("\n") if l.strip()]
        summary = lines[-1] if lines else "?"
        failed = result.returncode != 0
        return {"summary": summary, "ok": not failed, "exit_code": result.returncode}
    except Exception as e:
        return {"summary": f"Error: {e}", "ok": False, "exit_code": -1}


def get_gh_workflow_runs():
    """Últimos runs de GH Actions via API."""
    if not GH_TOKEN:
        return []
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{GH_REPO}/actions/runs?per_page=5&branch=main",
            headers={"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            runs = []
            for run in data.get("workflow_runs", []):
                runs.append({
                    "name": run["name"],
                    "number": run["run_number"],
                    "conclusion": run.get("conclusion", "?"),
                    "status": run["status"],
                    "created": run["created_at"][:16].replace("T", " "),
                    "url": run["html_url"],
                })
            return runs
    except Exception as e:
        return [{"name": f"Error API: {e}", "number": 0, "conclusion": "error",
                 "status": "error", "created": "", "url": "#"}]


def get_facturas():
    """Facturas próximas a vencer (solo si hay store local)."""
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from crm.facturas.store import FacturaStore
        from datetime import date
        store = FacturaStore()
        hoy = date.today()
        facturas = store.listar()
        result = []
        for f in facturas:
            d = f.dias_para_vencimiento(hoy)
            result.append({
                "nombre": f.nombre,
                "dias": d,
                "responsable": f.responsable,
                "activo": f.activo,
            })
        return result
    except Exception:
        return None  # No disponible


def get_timestamp():
    """ISO timestamp formateado."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ─── Generación HTML ───────────────────────────────────────────────

def generar_html(git, tests, runs, facturas, ts):
    """Genera el HTML completo del dashboard."""
    
    # Sección de runs
    runs_html = ""
    for r in runs:
        icon = {"success": "🟢", "failure": "🔴", "cancelled": "⚪", "in_progress": "🟡"}
        i = icon.get(r["conclusion"], "⚪")
        branch_part = f" <a href='{r['url']}' class='text-slate-400 hover:text-white transition-colors'>#{r['number']}</a>" if r.get('url') and r['url'] != '#' else f" #{r['number']}"
        runs_html += f"""
        <div class="flex items-center justify-between py-1.5">
          <span>{i} {r['name']}{branch_part}</span>
          <span class="text-xs text-slate-500">{r['created']}</span>
        </div>"""

    # Sección de facturas
    facturas_html = ""
    if facturas is not None:
        for f in facturas:
            if not f["activo"]:
                continue
            emoji = "🔴" if f["dias"] <= 1 else "🟡" if f["dias"] <= 5 else "🔵"
            facturas_html += f"""
        <div class="flex items-center justify-between py-1.5">
          <span>{emoji} {f['nombre']}</span>
          <span class="text-xs">{f['dias']} día(s) · {f['responsable']}</span>
        </div>"""
    else:
        facturas_html = """
        <div class="text-slate-500 text-xs py-1.5">No disponible (entorno cloud)</div>"""

    # Estado general
    estado = "🟢 Operativo"
    estado_color = "text-emerald-400"
    if tests and not tests.get("ok", True):
        estado = "🔴 Tests fallando"
        estado_color = "text-red-400"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zira CRM · Dashboard</title>
  <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ background: #0f172a; }}
    .glass {{ background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }}
    .accent {{ color: #10b981; }}
    @keyframes blink-d {{ 0%,95%,100%{{transform:scaleY(1)}} 97%{{transform:scaleY(0.05)}} }}
    @keyframes wave-d {{ 0%,100%{{transform:rotate(0)}} 25%{{transform:rotate(-5deg)}} 75%{{transform:rotate(5deg)}} }}
    .eye-d{{animation:blink-d 4.5s ease-in-out infinite;transform-origin:20px 19px}}
    .arm-d{{animation:wave-d 2.5s ease-in-out infinite;transform-origin:32px 24px}}
  </style>
</head>
<body class="text-slate-100 font-sans antialiased min-h-screen">
  <div class="max-w-lg mx-auto px-4 py-6">

    <!-- Header -->
    <header class="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
      <div class="flex items-center gap-3">
        <a href="assets/zira/" class="shrink-0 relative group" title="Galería Zira">
          <svg viewBox="0 0 40 40" class="w-8 h-8">
            <rect width="40" height="40" rx="8" fill="#1e293b"/>
            <polygon points="20,6 34,34 6,34" fill="#334155"/>
            <path d="M 17,12 Q 20,9 23,12 Q 24,10 23,14 Q 22,14 20,14 Q 18,14 17,13 Q 16,11 17,12 Z" fill="#e2e8f0"/>
            <g class="eye-d">
              <ellipse cx="14" cy="19" rx="3" ry="3.5" fill="#0f172a"/>
              <ellipse cx="14" cy="19" rx="2" ry="2.5" fill="#fff"/>
              <circle cx="13.5" cy="18.5" r="1" fill="#0f172a"/>
              <ellipse cx="26" cy="19" rx="3" ry="3.5" fill="#0f172a"/>
              <ellipse cx="26" cy="19" rx="2" ry="2.5" fill="#fff"/>
              <circle cx="25.5" cy="18.5" r="1" fill="#0f172a"/>
            </g>
            <path d="M 16,23 Q 20,26 24,23" fill="none" stroke="#0f172a" stroke-width="0.8"/>
            <g class="arm-d">
              <line x1="32" y1="24" x2="35" y2="21" stroke="#475569" stroke-width="1.5" stroke-linecap="round"/>
            </g>
          </svg>
          <span class="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-900 group-hover:animate-pulse"></span>
        </a>
        <div>
          <h1 class="text-lg font-bold tracking-tight">Zira CRM</h1>
          <p class="text-[10px] text-slate-400 font-mono">Rancho Raíz · Barreal</p>
        </div>
      </div>
      <span class="text-[10px] text-slate-500 font-mono">{ts}</span>
    </header>

    <!-- Estado general -->
    <div class="glass rounded-2xl p-4 mb-4 flex items-center justify-between">
      <div>
        <div class="text-xs text-slate-400 uppercase tracking-wider mb-0.5">Estado del Sistema</div>
        <div class="text-lg font-bold {estado_color}">{estado}</div>
      </div>
      <div class="text-right">
        <div class="text-xs text-slate-400">{git.get('branch', '?')}</div>
        <div class="text-[10px] text-slate-500 font-mono">{git.get('last_commit', '?')[:40]}</div>
      </div>
    </div>

    <!-- Tests -->
    <div class="glass rounded-2xl p-4 mb-4">
      <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">🧪 Tests</div>
      <div class="flex items-center justify-between">
        <span class="{'text-green-400' if tests.get('ok') else 'text-red-400'} text-sm">{tests.get('summary', '?')}</span>
        <span class="text-xs text-slate-500">{'✅ OK' if tests.get('ok') else '❌ FALLO'}</span>
      </div>
    </div>

    <!-- Facturas -->
    <div class="glass rounded-2xl p-4 mb-4">
      <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">📄 Facturas</div>
      {facturas_html}
    </div>

    <!-- Workflow Runs -->
    <div class="glass rounded-2xl p-4 mb-4">
      <div class="text-xs text-slate-400 uppercase tracking-wider mb-2">⚙️ Últimas Ejecuciones</div>
      {runs_html if runs_html else '<div class="text-slate-500 text-xs">Sin datos</div>'}
    </div>

    <!-- Enlaces rápidos -->
    <div class="grid grid-cols-2 gap-3 mb-8">
      <a href="assets/zira/" target="_blank" class="glass rounded-xl p-3 text-center hover:bg-slate-700/40 transition-colors">
        <svg viewBox="0 0 24 24" class="w-5 h-5 mx-auto mb-1 text-emerald-400">
          <polygon points="12,3 22,21 2,21" fill="none" stroke="currentColor" stroke-width="1.5"/>
          <path d="M 10,13 Q 12,11 14,13" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
          <circle cx="10" cy="11" r="1" fill="currentColor"/>
          <circle cx="14" cy="11" r="1" fill="currentColor"/>
        </svg>
        <div class="text-[10px] text-slate-400">Galería Zira</div>
      </a>
      <a href="https://github.com/oficinabarreal/rancho-raiz-zira" target="_blank" class="glass rounded-xl p-3 text-center hover:bg-slate-700/40 transition-colors">
        <i data-lucide="github" class="w-5 h-5 mx-auto mb-1 text-slate-400"></i>
        <div class="text-[10px] text-slate-400">Repositorio</div>
      </a>
      <a href="https://docs.google.com/document/d/1Lzz00OvhJ6NU9kSNJD9eOERcMUgmFKk7O_FSFNwslik/edit" target="_blank" class="glass rounded-xl p-3 text-center hover:bg-slate-700/40 transition-colors">
        <i data-lucide="file-text" class="w-5 h-5 mx-auto mb-1 text-slate-400"></i>
        <div class="text-[10px] text-slate-400">Buzón</div>
      </a>
      <a href="https://github.com/oficinabarreal/rancho-raiz-zira/actions" target="_blank" class="glass rounded-xl p-3 text-center hover:bg-slate-700/40 transition-colors">
        <i data-lucide="activity" class="w-5 h-5 mx-auto mb-1 text-slate-400"></i>
        <div class="text-[10px] text-slate-400">Actions</div>
      </a>
      <a href="https://github.com/oficinabarreal/rancho-raiz-zira/actions/workflows/simulacion.yml" target="_blank" class="glass rounded-xl p-3 text-center hover:bg-slate-700/40 transition-colors">
        <i data-lucide="play" class="w-5 h-5 mx-auto mb-1 text-slate-400"></i>
        <div class="text-[10px] text-slate-400">Simulación</div>
      </a>
    </div>

    <footer class="text-center text-[10px] text-slate-600 pb-6">
      Generado por Zira · {ts}
    </footer>
  </div>
  <script>lucide.createIcons();</script>
</body>
</html>"""
    return html


# ─── CLI ───────────────────────────────────────────────────────────

def main():
    push = "--push" in sys.argv

    print("📊 Generando dashboard...")
    
    ts = get_timestamp()
    git = get_git_info()
    tests = get_test_status()
    runs = get_gh_workflow_runs()
    facturas = get_facturas()

    html = generar_html(git, tests, runs, facturas, ts)

    output_path = PROJECT_DIR / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard escrito: {output_path} ({len(html)} bytes)")

    if facturas is not None:
        print(f"   Facturas: {len(facturas)} registrada(s)")
    else:
        print("   Facturas: no disponible (sin store local)")
    print(f"   Tests: {tests.get('summary', '?')}")
    print(f"   Runs GH: {len(runs)}")

    if push:
        print("\n📤 Pusheando a gh-pages...")
        try:
            # Guardar el HTML en la rama gh-pages usando subtree split
            subprocess.run(
                ["git", "add", "index.html"],
                cwd=PROJECT_DIR, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"dashboard: actualización {ts}", "--allow-empty"],
                cwd=PROJECT_DIR, check=True
            )
            # Push a gh-pages: usar subtree para mantener solo index.html
            result = subprocess.run(
                ["git", "push", "origin", "HEAD:gh-pages", "--force"],
                cwd=PROJECT_DIR, capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Pusheado a gh-pages")
                print(f"   https://{GH_REPO.split('/')[0]}.github.io/{GH_REPO.split('/')[1]}/")
            else:
                print(f"⚠ Error push: {result.stderr.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Error git: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
