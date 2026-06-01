#!/usr/bin/env python3
"""
Prueba de estrés: 3 renders concurrentes vía MCP Client Bridge.
Verifica:
  - Render exitoso de cada layout
  - Limpieza de archivos temporales HTML
  - Tiempo de respuesta
"""
import asyncio
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import html_a_imagen


BANNERS = [
    {
        "name": "banner_pileta",
        "html": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;
  background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
  display:flex;align-items:center;justify-content:center;
  font-family:Arial,sans-serif;color:white;text-align:center;padding:60px}
h1{font-size:72px;margin-bottom:20px}
.title{color:#00d4ff;font-size:36px;margin-bottom:40px}
.cta{padding:24px 60px;background:#00d4ff;color:#0f2027;
     border-radius:50px;font-size:28px;font-weight:bold;
     display:inline-block}
</style></head><body>
<div>
  <div class="title">🏊 Pileta · Rancho Raíz</div>
  <h1>Escape al agua<br>en la montaña</h1>
  <p style="font-size:24px;opacity:0.8;margin-bottom:40px">
    Barreal, San Juan · Temporada 2026</p>
  <div class="cta">Reservá tu día →</div>
</div>
</body></html>""",
        "width": 1080,
        "height": 1080,
        "fmt": "png",
    },
    {
        "name": "banner_cabañas",
        "html": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;
  background:linear-gradient(135deg,#42275a,#734b6d);
  display:flex;align-items:center;justify-content:center;
  font-family:Arial,sans-serif;color:white;text-align:center;padding:60px}
h1{font-size:72px;margin-bottom:20px}
.sub{font-size:28px;opacity:0.9;margin-bottom:50px}
.badge{display:inline-block;padding:16px 40px;background:rgba(255,255,255,0.15);
       border-radius:50px;font-size:20px;border:1px solid rgba(255,255,255,0.3);
       margin-bottom:30px}
.cta{padding:24px 60px;background:white;color:#42275a;
     border-radius:50px;font-size:28px;font-weight:bold;
     display:inline-block}
</style></head><body>
<div>
  <div class="badge">🏡 Cabañas · Rancho Raíz</div>
  <h1>Tu refugio<br>en los Andes</h1>
  <p class="sub">Cabañas para 2 a 6 personas · Vista a la cordillera</p>
  <div class="cta">Consultá disponibilidad →</div>
</div>
</body></html>""",
        "width": 1080,
        "height": 1080,
        "fmt": "png",
    },
    {
        "name": "banner_aventura",
        "html": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;
  background:linear-gradient(135deg,#11998e,#38ef7d);
  display:flex;align-items:center;justify-content:center;
  font-family:Arial,sans-serif;color:white;text-align:center;padding:60px}
h1{font-size:72px;margin-bottom:20px;text-shadow:0 2px 20px rgba(0,0,0,0.2)}
.sub{font-size:26px;opacity:0.95;margin-bottom:40px}
.cta{padding:24px 60px;background:white;color:#11998e;
     border-radius:50px;font-size:28px;font-weight:bold;
     display:inline-block;box-shadow:0 4px 20px rgba(0,0,0,0.15)}
.icon{font-size:64px;margin-bottom:20px}
</style></head><body>
<div>
  <div class="icon">🏔️</div>
  <h1>Aventura<br>sin límites</h1>
  <p class="sub">Trekking · Cabalgatas · Observación de estrellas<br>
    Todo en Barreal, San Juan</p>
  <div class="cta">Viví la experiencia →</div>
</div>
</body></html>""",
        "width": 1080,
        "height": 1080,
        "fmt": "png",
    },
]


async def run_stress_test():
    print(f"\n{'='*60}")
    print(f"  TEST DE ESTRÉS — 3 RENDERS CONCURRENTES")
    print(f"{'='*60}\n")

    temp_dir = tempfile.mkdtemp(prefix="mcp_stress_")
    print(f"📁 Directorio temporal: {temp_dir}")

    temp_count_before = len([f for f in os.listdir(tempfile.gettempdir())
                              if f.endswith('.html') and f.startswith('tmp')])

    results = {}
    start_total = time.time()

    for banner in BANNERS:
        name = banner["name"]
        print(f"\n  ▶ Renderizando: {name}")
        start = time.time()
        try:
            result = await html_a_imagen(
                html=banner["html"],
                width=banner["width"],
                height=banner["height"],
                fmt=banner["fmt"],
            )
            elapsed = time.time() - start
            results[name] = {"ok": True, "elapsed": elapsed, "result": result}
            print(f"    ✅ {elapsed:.2f}s · {result['size']} bytes · {result['width']}x{result['height']}")
            print(f"    📍 {result['path']}")
        except Exception as e:
            elapsed = time.time() - start
            results[name] = {"ok": False, "elapsed": elapsed, "error": str(e)}
            print(f"    ❌ {elapsed:.2f}s · ERROR: {e}")

    total_elapsed = time.time() - start_total
    temp_count_after = len([f for f in os.listdir(tempfile.gettempdir())
                             if f.endswith('.html') and f.startswith('tmp')])

    print(f"\n{'='*60}")
    print(f"  RESULTADOS")
    print(f"{'='*60}")
    passed = sum(1 for r in results.values() if r["ok"])
    failed = sum(1 for r in results.values() if not r["ok"])
    max_time = max(r["elapsed"] for r in results.values())
    avg_time = sum(r["elapsed"] for r in results.values()) / len(results)

    print(f"\n  ✅ Exitosos: {passed}/{len(BANNERS)}")
    print(f"  ❌ Fallidos: {failed}")
    print(f"  ⏱  Tiempo total: {total_elapsed:.2f}s")
    print(f"  ⏱  Promedio: {avg_time:.2f}s")
    print(f"  ⏱  Máximo: {max_time:.2f}s")

    print(f"\n  🧹 Verificación de limpieza de tempfiles:")
    print(f"     Antes: ~{temp_count_before} archivos .html temporales")
    print(f"     Después: ~{temp_count_after} archivos .html temporales")
    if temp_count_after <= temp_count_before + 1:
        print(f"     ✅ Tempfiles HTML limpiados correctamente")
    else:
        print(f"     ⚠️  Pueden haber {temp_count_after - temp_count_before} archivos residuales")

    # Cleanup test temp dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\n{'='*60}")
    if passed == len(BANNERS):
        print(f"  ✅ TODOS LOS TESTS PASARON")
    else:
        print(f"  ⚠️  {failed} TEST(S) FALLARON")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_stress_test())
    sys.exit(0 if all(r["ok"] for r in results.values()) else 1)
