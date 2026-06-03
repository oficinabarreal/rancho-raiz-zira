# Conocimiento Absorbido de Proyectos Anteriores

> Proyectos revisados y absorbidos en hola-3. Origenes borrados.
> Última actualización: 3 Jun 2026

---

## 1. rancho-ai — Sistema Multi-Agente

**Origen:** `/sdcard/puente/rancho-ai/` (borrado)
**Valor:** Arquitectura de coordinador + expertos especializados

### Patrón de arquitectura

```
Coordinador (objetivo → plan → delegar)
  ├── Experto Video (FFmpeg/MoviePy)
  ├── Experto Fotos (banco de fotos)
  ├── Experto Email (Gmail API)
  ├── Experto Instagram (publicación)
  ├── Experto WhatsApp (Business API)
  ├── Experto Calendar (Google Calendar)
  ├── Experto Drive (Google Drive)
  └── Inspector (tareas multi-dominio, opcional)
```

**Aplicación en Zira:** Zira puede evolucionar a un sistema multi-modo donde cada personalidad (Clásica, Juguetona, Zen, Mágica, etc.) sea un "experto" con su propio estilo de comunicación y generación de contenido.

---

## 2. colab_videos — Técnicas de Video AI

**Origen:** `/sdcard/puente/colab_videos/` (borrado)
**Valor:** 3 técnicas de generación de video desde Google Colab

| Técnica | Notebook | Qué hace |
|---|---|---|
| **Ken Burns** | `01_KEN_BURNS_ANIMADOR.ipynb` | Animación de fotos fijas: zoom/pan sobre imagen |
| **AnimateDiff** | `02_ANIMEDIFF_FOTOS.ipynb` | IA que anima fotos reales (agua fluyendo, partículas, luz) |
| **SadTalker + XTTS** | `03_SADTALKER_AVATAR.ipynb` | Avatar virtual que habla en español con labios sincronizados |

**Para Zira:** AnimateDiff podría animar las fotos reales de Rancho Raíz con movimiento sutil. SadTalker + Zira como avatar parlante sería un "vendedor virtual" 24/7.

---

## 3. rancho-raiz-leads — Pipeline de Captación

**Origen:** `/sdcard/puente/rancho-raiz-leads/` (borrado)
**Valor:** Sistema completo de scoring + chatbot + automatización

### Pipeline Lead → Venta

```
CAPTACIÓN → PERFILADO → CALIFICADO → NUTRIENTE → CIERRE
  likes       scraper     score 0-100   chatbot     WhatsApp
  comments    IG API      frío/caliente DM + follow  Diego/ventas
```

### Sistema de Scoring

| Señal | Puntos |
|---|---|
| +500 seguidores | +15 |
| Posts > 50 + sigue > 200 | +15 |
| Perfil personal (no marca) | +10 |
| Seguidores 200-3,000 | +10 |
| Relacionado turismo/zona | +20 |
| **Máximo** | **100** |

**Clasificación:** 0-30 ❄️ Frío → 31-60 🌤️ Tibio → 61-85 ☀️ Caliente → 86-100 🔥 Venta

### Stack WhatsApp Bot
- Librería: `@whiskeysockets/baileys` (Baileys v7)
- Túnel: `localhost.run` (SSH reverse)
- Gestor: `pm2` o `tmux`
- Wake lock: `termux-wake-lock`

---

## 4. AURA — Filosofía de IA Simbiótica

**Origen:** `/sdcard/puente/aura/` y `aura-back[1-5]/` (borrado)
**Valor:** Concepto de sistema que percibe + anticipa usando sensores Android

### Filosofía
- **Reactividad** (paradigma actual): usuario toca → teléfono responde
- **Simbiosis** (AURA): teléfono coexiste, percibe y anticipa necesidades

### Stack
- Runtime: Termux + proot-distro
- Sensores: termux-api (GPS, sensores, cámara, TTS)
- Memoria: experiencias.json
- Agente: OpenCode/OpenClaw como córtex prefrontal

### Inspiración para Zira
Zira podría algún día percibir el contexto (clima, hora, reservas activas) y adaptar su personalidad/mensajes automáticamente.

---

## 5. WhatsApp Chats — Perfiles de Equipo

**Origen:** `/sdcard/Documents/rancho-rai/` y `/sdcard/Download/` (borrado)
**Valor:** Perfiles de Leo, Ayelén y dinámica del equipo

→ Ver `team/perfiles_equipo.md`

---

## 6. Audio Pipeline

**Origen:** `publicidad/` y `~/ranchoraiz_reels/` (borrados)
**Valor:** Audionautix, descargas, mapeo tema→audio

→ Ver `pipeline/audio/README.md`

---

## 7. lab.js — Pipeline de Reels FFmpeg

**Origen:** `publicidad/ranchocut/lab.js` (borrado)
**Valor:** Pipeline completo de generación de Reels con Ken Burns, transiciones, overlay de texto, y audio contextual.

→ Ver `pipeline/scripts/lab.js` y `pipeline/scripts/src/`
