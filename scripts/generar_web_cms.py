#!/usr/bin/env python3
"""Generate the rancho-raiz website from Google Sheets CMS data.

Usage:
    python3 scripts/generar_web_cms.py
    # Reads the public Sheet, generates index.html and admin/index.html
"""
import csv
import io
import json
import os
import urllib.request
import html as html_mod

SHEET_ID = "1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI"

def read_sheet_tab(tab_name):
    """Read a Google Sheet tab using the Sheets API (public sheet, no auth needed for read)."""
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            # Use API key for public sheet access (works in CI)
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/'{tab_name}'!A1:Z100?key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode())
            rows = data.get("values", [])
            if rows:
                return _parse_rows(rows)
        # Try using googleapiclient if available
        import sys
        sys.path.insert(0, '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3')
        from crm.google_auth import get_service
        svc = get_service('sheets', 'v4', 'sheets')
        if svc:
            result = svc.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'{tab_name}'!A1:Z100",
                majorDimension='ROWS'
            ).execute()
            rows = result.get('values', [])
        else:
            rows = _read_sheet_csv_fallback(tab_name)
    except Exception:
        rows = _read_sheet_csv_fallback(tab_name)

    return _parse_rows(rows)


def _parse_rows(rows):
    """Convert raw rows to dict list using first row as headers."""
    if not rows or len(rows) < 1:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        while len(row) < len(headers):
            row.append("")
        item = {}
        for i, h in enumerate(headers):
            item[h] = str(row[i]).strip()
        result.append(item)
    return result


def _read_sheet_csv_fallback(tab_name):
    """Fallback: read via public CSV export."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read().decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        return list(reader)
    except Exception as e:
        print(f"⚠️  CSV fallback error for '{tab_name}': {e}")
        return []

def get_config(data):
    """Convert config rows to a dict."""
    cfg = {}
    for row in data:
        key = row.get("clave", "")
        val = row.get("valor", "")
        if key:
            cfg[key] = val
    return cfg

def render_habitaciones(habitaciones, cfg):
    """Render room cards HTML with optional promo pricing."""
    active = [h for h in habitaciones if h.get("activo", "").upper() == "SI"]
    active.sort(key=lambda x: x.get("orden", "99"))
    if not active:
        return '<p class="text-slate-400 text-center">Próximamente información de habitaciones.</p>'
    
    cards = ""
    for h in active:
        nombre = html_mod.escape(h.get("nombre", ""))
        precio = html_mod.escape(h.get("precio", ""))
        precio_promo = h.get("precio_promocion", "").strip()
        promo_label = h.get("promo_label", "").strip()
        desc = html_mod.escape(h.get("descripcion", ""))
        img = h.get("imagen_url", "").strip()
        img_html = ""
        if img:
            img_html = f'<img src="{html_mod.escape(img)}" alt="{nombre}" class="w-full h-48 object-cover rounded-lg mb-4">'
        else:
            img_html = '<div class="w-full h-48 bg-dark-3 rounded-lg mb-4 flex items-center justify-center text-slate-500"><svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg></div>'
        
        # Price display: show promo if available
        if precio_promo and precio:
            precio_html = f'''
                <div class="flex items-baseline gap-2">
                    <span class="text-slate-500 text-sm line-through">${html_mod.escape(precio)}</span>
                    <span class="text-green-400 text-2xl font-bold">${html_mod.escape(precio_promo)}</span>
                    <span class="text-slate-400 text-xs">/noche</span>
                </div>'''
            badge_text = html_mod.escape(promo_label) if promo_label else "OFERTA"
            promo_badge = f'<span class="absolute top-3 right-3 bg-green-500 text-dark text-xs font-bold px-2 py-1 rounded-full">{badge_text}</span>'
        elif precio:
            precio_html = f'<span class="text-gold text-2xl font-bold">${precio}</span><span class="text-slate-400 text-sm">/noche</span>'
            promo_badge = ''
        else:
            precio_html = ''
            promo_badge = ''
        
        cards += f'''
        <div class="bg-dark-2 rounded-xl p-6 border border-slate-700/50 hover:border-gold/30 transition-all duration-300 relative">
            {promo_badge}
            {img_html}
            <h3 class="text-xl font-semibold text-white mb-2">{nombre}</h3>
            <p class="text-slate-400 text-sm mb-4 leading-relaxed">{desc}</p>
            <div class="flex items-center justify-between">
                {precio_html}
                <a href="https://wa.me/{cfg.get("whatsapp", "")}?text=Hola%20Rancho%20Raíz%2C%20quiero%20reservar%20{urllib.parse.quote(nombre)}" 
                   class="bg-gold hover:bg-gold-dark text-dark font-medium px-4 py-2 rounded-lg text-sm transition-all duration-300">
                    Reservar
                </a>
            </div>
        </div>'''
    return cards

def render_servicios(servicios):
    """Render services grid HTML."""
    active = [s for s in servicios if s.get("activo", "").upper() == "SI"]
    if not active:
        return '<p class="text-slate-400 text-center">Próximamente.</p>'
    
    items = ""
    icons = {
        "wifi": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0"/>',
        "cafe": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 20.016c-2.196 0-4.034-.855-5.09-2.174C5.856 16.523 5.5 14.82 5.5 13.5c0-2.5 1.5-5.5 3-7.5l1-1.5M12 20.016c2.196 0 4.034-.855 5.09-2.174C18.144 16.523 18.5 14.82 18.5 13.5c0-2.5-1.5-5.5-3-7.5l-1-1.5M12 20.016V8m0 0V4.5"/>',
        "caballo": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>',
        "auto": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7h8m-8 0a2 2 0 01-2 2H5l-1 4h16l-1-4h-1a2 2 0 01-2-2m-8 0V5a2 2 0 012-2h4a2 2 0 012 2v2m0 0h.01M7 16h.01M17 16h.01"/>',
        "montaña": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 21l6-12 4 6 4-9 4 15H3z"/>',
    }
    
    for s in active:
        nombre = html_mod.escape(s.get("nombre", ""))
        desc = html_mod.escape(s.get("descripcion", ""))
        icon_key = s.get("icono", "").strip().lower()
        path = icons.get(icon_key, icons["montaña"])
        items += f'''
        <div class="bg-dark-2/80 rounded-xl p-5 border border-slate-700/30 hover:border-gold/20 transition-all duration-300">
            <div class="w-10 h-10 rounded-lg bg-gold/10 flex items-center justify-center mb-3">
                <svg class="w-5 h-5 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">{path}</svg>
            </div>
            <h4 class="font-semibold text-white mb-1">{nombre}</h4>
            <p class="text-slate-400 text-xs leading-relaxed">{desc}</p>
        </div>'''
    return items

def render_galeria(galeria):
    """Render gallery HTML."""
    active = [g for g in galeria if g.get("activo", "").upper() == "SI"]
    active.sort(key=lambda x: x.get("orden", "99"))
    if not active or not any(g.get("imagen_url", "").strip() for g in active):
        return '<p class="text-slate-400 text-center">Galería próximamente.</p>'
    
    items = ""
    for g in active:
        url = g.get("imagen_url", "").strip()
        desc = html_mod.escape(g.get("descripcion", ""))
        if url:
            items += f'''
            <div class="group relative overflow-hidden rounded-xl">
                <img src="{html_mod.escape(url)}" alt="{desc}" class="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-105">
                <div class="absolute inset-0 bg-gradient-to-t from-dark/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                    <p class="text-white text-sm">{desc}</p>
                </div>
            </div>'''
    return items

def render_promociones(promociones):
    """Render promotions/deals HTML."""
    active = [p for p in promociones if p.get("activo", "").upper() == "SI"]
    active.sort(key=lambda x: x.get("orden", "99"))
    if not active:
        return ""
    
    cards = ""
    for p in active:
        nombre = html_mod.escape(p.get("nombre", ""))
        desc = html_mod.escape(p.get("descripcion", ""))
        precio_reg = p.get("precio_regular", "").strip()
        precio_promo = p.get("precio_promo", "").strip()
        img = p.get("imagen_url", "").strip()
        
        img_html = ""
        if img:
            img_html = f'<img src="{html_mod.escape(img)}" alt="{nombre}" class="w-full h-40 object-cover rounded-lg mb-4">'
        else:
            img_html = '<div class="w-full h-40 bg-gradient-to-br from-gold/20 to-dark-3 rounded-lg mb-4 flex items-center justify-center"><svg class="w-10 h-10 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/></svg></div>'
        
        if precio_promo and precio_reg:
            price_html = f'''
                <div class="flex items-baseline gap-2 justify-center">
                    <span class="text-slate-500 text-sm line-through">${html_mod.escape(precio_reg)}</span>
                    <span class="text-green-400 text-2xl font-bold">${html_mod.escape(precio_promo)}</span>
                </div>'''
        elif precio_promo:
            price_html = f'<span class="text-green-400 text-2xl font-bold">${html_mod.escape(precio_promo)}</span>'
        else:
            price_html = ''
        
        cards += f'''
        <div class="bg-dark-2 rounded-xl p-6 border border-gold/20 hover:border-gold/40 transition-all duration-300 text-center">
            {img_html}
            <span class="inline-block bg-green-500/20 text-green-400 text-xs font-bold px-3 py-1 rounded-full mb-3">🔥 PROMO</span>
            <h3 class="text-lg font-bold text-white mb-2">{nombre}</h3>
            <p class="text-slate-400 text-sm mb-4 leading-relaxed">{desc}</p>
            {price_html}
        </div>'''
    return cards

def generate_site(config, habitaciones, servicios, galeria, promociones):
    """Generate the complete index.html."""
    telefono = html_mod.escape(config.get("telefono", ""))
    whatsapp = html_mod.escape(config.get("whatsapp", ""))
    email = html_mod.escape(config.get("email", ""))
    direccion = html_mod.escape(config.get("direccion", ""))
    ig = html_mod.escape(config.get("ig_usuario", "ranchoraiz.barreal"))
    
    rooms_html = render_habitaciones(habitaciones, config)
    services_html = render_servicios(servicios)
    gallery_html = render_galeria(galeria)
    promos_html = render_promociones(promociones)
    
    # Only add promos section if there are active promotions
    promos_section = f'''
    <!-- PROMOCIONES -->
    <section id="promociones" class="py-20 px-4 bg-dark-2/50">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">🔥 Promociones</h2>
          <p class="text-slate-400">Ofertas especiales para que vivas la montaña</p>
        </div>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {promos_html}
        </div>
      </div>
    </section>
    ''' if promos_html else ''
    
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rancho Raíz · Posada de Montaña · Barreal, San Juan</title>
  <meta name="description" content="Rancho Raíz - Posada en Barreal, San Juan, Argentina. Al pie de la Cordillera de los Andes.">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpolygon points='20,6 34,34 6,34' fill='%23C5A059'/%3E%3C/svg%3E">
  <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    :root {{ --gold: #C5A059; --gold-light: #E8D5A3; --gold-dark: #A07D3A; --dark: #0B1121; --dark-2: #111827; --dark-3: #1E293B; --slate: #334155; }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', sans-serif; background: var(--dark); color: #f1f5f9; overflow-x: hidden; }}
    @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-8px); }} }}
    @keyframes starField {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-2000px); }} }}
    .animate-fadeUp {{ animation: fadeUp 0.8s ease-out forwards; }}
    .animate-float {{ animation: float 4s ease-in-out infinite; }}
    .stars {{ position: fixed; top: 0; left: 0; width: 100%; height: 200%; background: transparent url('data:image/svg+xml,%3Csvg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Ccircle cx=\"10\" cy=\"10\" r=\"1\" fill=\"white\" opacity=\"0.3\"/%3E%3Ccircle cx=\"50\" cy=\"80\" r=\"0.5\" fill=\"white\" opacity=\"0.2\"/%3E%3Ccircle cx=\"120\" cy=\"30\" r=\"1.5\" fill=\"white\" opacity=\"0.4\"/%3E%3Ccircle cx=\"180\" cy=\"60\" r=\"0.5\" fill=\"white\" opacity=\"0.2\"/%3E%3Ccircle cx=\"30\" cy=\"140\" r=\"1\" fill=\"white\" opacity=\"0.3\"/%3E%3Ccircle cx=\"150\" cy=\"150\" r=\"0.5\" fill=\"white\" opacity=\"0.2\"/%3E%3Ccircle cx=\"70\" cy=\"180\" r=\"1\" fill=\"white\" opacity=\"0.3\"/%3E%3Ccircle cx=\"160\" cy=\"120\" r=\"0.5\" fill=\"white\" opacity=\"0.2\"/%3E%3C/svg%3E') repeat; animation: starField 60s linear infinite; pointer-events: none; z-index: 0; }}
    .content {{ position: relative; z-index: 1; }}
    .gold-gradient {{ background: linear-gradient(135deg, var(--gold), var(--gold-dark), var(--gold)); background-size: 200% 200%; animation: gradientShift 4s ease infinite; }}
  </style>
</head>
<body>
  <div class="stars"></div>
  <div class="content">
    
    <!-- NAV -->
    <nav class="fixed top-0 left-0 w-full z-50 bg-dark/80 backdrop-blur-lg border-b border-slate-800/50">
      <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <a href="#" class="text-xl font-bold tracking-tight"><span class="text-gold">▲</span> Rancho Raíz</a>
        <div class="hidden md:flex items-center gap-6 text-sm text-slate-300">
          <a href="#habitaciones" class="hover:text-gold transition-colors">Habitaciones</a>
          <a href="#servicios" class="hover:text-gold transition-colors">Servicios</a>
          <a href="#galeria" class="hover:text-gold transition-colors">Galería</a>
          <a href="#contacto" class="hover:text-gold transition-colors">Contacto</a>
        </div>
        <a href="https://wa.me/{whatsapp}?text=Hola%20Rancho%20Ra%C3%ADz%2C%20quiero%20consultar%20disponibilidad" 
           class="bg-gold hover:bg-gold-dark text-dark text-sm font-medium px-4 py-2 rounded-lg transition-all duration-300">
          Reservar
        </a>
      </div>
    </nav>

    <!-- HERO -->
    <section class="min-h-screen flex items-center justify-center relative overflow-hidden pt-16">
      <div class="absolute inset-0 bg-gradient-to-b from-dark via-dark-2/50 to-dark"></div>
      <div class="absolute bottom-0 left-0 w-full h-64 bg-gradient-to-t from-dark to-transparent"></div>
      <div class="relative z-10 text-center px-4 max-w-4xl">
        <div class="animate-fadeUp">
          <div class="text-gold text-sm tracking-[0.2em] uppercase mb-4">San Juan · Argentina</div>
          <h1 class="text-5xl md:text-7xl font-black tracking-tight mb-6">
            <span class="text-white">Rancho</span> <span class="gold-gradient bg-clip-text text-transparent">Raíz</span>
          </h1>
          <p class="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-8 leading-relaxed">
            Posada de montaña al pie de la Cordillera de los Andes.<br>
            Donde la naturaleza encuentra tu alma.
          </p>
          <div class="flex flex-wrap gap-4 justify-center">
            <a href="https://wa.me/{whatsapp}?text=Hola%20Rancho%20Ra%C3%ADz%2C%20quiero%20reservar" 
               class="bg-gold hover:bg-gold-dark text-dark font-semibold px-8 py-3 rounded-xl transition-all duration-300 text-lg">
              Reservá ahora
            </a>
            <a href="#habitaciones" 
               class="border border-slate-600 hover:border-gold text-slate-300 hover:text-white font-medium px-8 py-3 rounded-xl transition-all duration-300 text-lg">
              Ver más
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- HABITACIONES -->
    <section id="habitaciones" class="py-20 px-4">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Nuestras Habitaciones</h2>
          <p class="text-slate-400">Elegí el espacio que más se adapte a tu viaje</p>
        </div>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {rooms_html}
        </div>
      </div>
    </section>

    <!-- SERVICIOS -->
    <section id="servicios" class="py-20 px-4 bg-dark-2/50">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Servicios</h2>
          <p class="text-slate-400">Todo lo que necesitás para una experiencia inolvidable</p>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          {services_html}
        </div>
      </div>
    </section>

    <!-- GALERÍA -->
    <section id="galeria" class="py-20 px-4">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Galería</h2>
          <p class="text-slate-400">Viví Rancho Raíz a través de imágenes</p>
        </div>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gallery_html}
        </div>
      </div>
    </section>

    {promos_section}
    <!-- CONTACTO -->
    <section id="contacto" class="py-20 px-4 bg-dark-2/50">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-bold text-white mb-4">Contacto</h2>
          <p class="text-slate-400">Estamos listos para recibirte</p>
        </div>
        <div class="max-w-xl mx-auto space-y-4">
          <div class="bg-dark-3 rounded-xl p-4 flex items-center gap-4">
            <svg class="w-5 h-5 text-gold shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
            <a href="tel:{telefono}" class="text-slate-300 hover:text-gold transition-colors">{telefono}</a>
          </div>
          <div class="bg-dark-3 rounded-xl p-4 flex items-center gap-4">
            <svg class="w-5 h-5 text-gold shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            <a href="mailto:{email}" class="text-slate-300 hover:text-gold transition-colors">{email}</a>
          </div>
          <div class="bg-dark-3 rounded-xl p-4 flex items-center gap-4">
            <svg class="w-5 h-5 text-gold shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <span class="text-slate-300">{direccion}</span>
          </div>
          <div class="bg-dark-3 rounded-xl p-4 flex items-center gap-4">
            <svg class="w-5 h-5 text-gold shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a1 1 0 00.948-.684l1.498-4.493A1 1 0 019.38 1h5.24a1 1 0 01.948.684l1.498 4.493a1 1 0 00.948.684H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <a href="https://instagram.com/{ig}" target="_blank" class="text-slate-300 hover:text-gold transition-colors">@{ig}</a>
          </div>
          <div class="mt-8 text-center">
            <a href="https://wa.me/{whatsapp}?text=Hola%20Rancho%20Ra%C3%ADz%2C%20quiero%20consultar%20disponibilidad" 
               class="inline-block bg-gold hover:bg-gold-dark text-dark font-semibold px-8 py-3 rounded-xl transition-all duration-300 text-lg">
              Consultar disponibilidad
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="py-8 px-4 border-t border-slate-800/50">
      <div class="max-w-6xl mx-auto text-center text-slate-500 text-sm">
        <p>© 2026 Rancho Raíz · Barreal, San Juan · Argentina</p>
        <p class="mt-1">Hecho con ❤️ en la Cordillera de los Andes</p>
      </div>
    </footer>

  </div>
</body>
</html>'''

def main():
    print("📖 Leyendo CMS desde Google Sheet...")
    config_data = read_sheet_tab("config")
    habitaciones = read_sheet_tab("habitaciones")
    servicios = read_sheet_tab("servicios")
    galeria = read_sheet_tab("galeria")
    promociones = read_sheet_tab("promociones")
    
    config = get_config(config_data)
    
    print(f"   Config: {len(config)} claves")
    print(f"   Habitaciones: {len(habitaciones)}")
    print(f"   Servicios: {len(servicios)}")
    print(f"   Galería: {len(galeria)}")
    print(f"   Promociones: {len(promociones)}")
    
    print("🏗️  Generando sitio web...")
    html = generate_site(config, habitaciones, servicios, galeria, promociones)
    
    # Write to web root
    output_dir = os.path.dirname(os.path.abspath(__file__)) + "/.."
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html generado ({len(html)} bytes)")
    
    # Also write to panel dir for GH Pages
    panel_path = os.path.join(output_dir, "panel", "index.html")
    os.makedirs(os.path.dirname(panel_path), exist_ok=True)
    with open(panel_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ panel/index.html generado")
    
    # Save config for admin page
    admin_dir = os.path.join(output_dir, "admin")
    os.makedirs(admin_dir, exist_ok=True)
    with open(os.path.join(admin_dir, "cms_data.json"), "w", encoding="utf-8") as f:
        json.dump({
            "config": config,
            "habitaciones": habitaciones,
            "servicios": servicios,
            "galeria": galeria,
            "promociones": promociones,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
        }, f, ensure_ascii=False, indent=2)
    print("✅ admin/cms_data.json generado")
    
    print("\n🎉 Listo! Sitio generado desde CMS.")

if __name__ == "__main__":
    import urllib.parse
    main()
