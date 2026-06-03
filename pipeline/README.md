# 🏔️ Pipeline Unificado Zira

Integración entre publicidad/ (legacy) y hola-3 (Zira CRM)

## Estructura

pipeline/
├── db.json          ← Metadata de 22 fotos reales (tags, hora, clima)
├── fotos/           ← 22 fotos reales de Rancho Raíz
├── audio/           ← Música contextual (mapeo tema→audio en ARTE_OPENCODE.md)
├── scripts/
│   ├── lab.js       ← Generación de Reels (Ken Burns + texto + transiciones)
│   ├── telegram.js  ← Envío a Telegram
│   ├── descargar-audio.js
│   └── experimento.js
├── README.md        ← Este archivo
/scripts/
├── publicar_instagram.py   ← Publica imágenes/Reels en Instagram
├── zira_on_photo.py        ← Superpone Zira sobre fotos reales
├── pipeline_movimiento.py  ← SVG animado → frames → video
├── capture-frames.js       ← Captura animaciones SVG como frames
└── publicar_reels_legacy.py ← Publica Reels legacy
