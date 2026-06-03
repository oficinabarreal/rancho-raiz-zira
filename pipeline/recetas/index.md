# Sistema de Experimentos — Recetas de Video

## Filosofía

Cada día probamos combinaciones diferentes de estrategias, herramientas y
tecnologías. Cada combinación se documenta como una **receta**. Cuando una
receta alcanza calidad CapCut, se promueve a **estándar**.

---

## Ciclo de una Receta

```
Candidato ──→ Probado ──→ Aprobado ──→ ESTÁNDAR
  (idea)      (se generó   (pasó        (se incorpora
               video)       evaluación)   al pipeline)
```

---

## Espacio de Exploración

### Variables de Video (FFmpeg puras)
| Variable | Valores | Por qué importa |
|----------|---------|-----------------|
| Ken Burns | 12 modos | Movimiento de cámara |
| Estilo texto | fade, slide_up, slide_left, pulse | Animación de texto |
| Overlay | none, cinematic, cinematic_thin, vignette | Marco visual |
| Color grade | none, vibrante, suave, sepia, b&w | Ambiente |
| Duración/foto | 3s, 4s, 5s | Ritmo del reel |
| Zoom speed | 0.0005, 0.0008, 0.001 | Velocidad de cámara |
| Zoom max | 1.08, 1.12, 1.15, 1.20 | Intensidad del zoom |
| Transición | 10+ tipos (xfade) | Corte entre fotos |
| Font size título | 60, 70, 80 | Jerarquía visual |
| Font size subtítulo | 30, 35, 40 | Legibilidad |

### Variables Híbridas (FFmpeg + Overlay externo)
| Variable | Valores | Por qué importa |
|----------|---------|-----------------|
| Overlay PNG | logo, textura | Branding, textura |
| Gradient overlay | linear, radial | Ambiente dramático |
| Three.js overlay | scramble, wave, glitch | Efectos avanzados |

### Variables de Herramienta
| Herramienta | Cuándo usarla |
|-------------|---------------|
| FFmpeg puro | 80% de casos, más rápido |
| Three.js + FFmpeg | Efectos avanzados, texto animado |
| Canvas 2D Node.js | Overlays programáticos (futuro) |
| NVIDIA NIM + prompt | Selección inteligente de fotos |

---

## Cómo Probar una Receta

```bash
# 1. Crear receta (editar catalogo.json o usar --nueva)
node ranchocut/experimento.js --nueva

# 2. Ejecutar receta
node ranchocut/experimento.js --receta=kb-pan-fade-vibrante

# 3. Ver diario
node ranchocut/experimento.js --diario

# 4. Comparar resultados
node ranchocut/experimento.js --comparar

# 5. Promover a estándar (editar catalogo.json: estado → "estandar")
```

---

## Evaluación de Calidad

Cada receta probada se evalúa en:

1. **Tamaño** — < 2 MB ideal, < 3 MB aceptable
2. **Duración** — 15-25s ideal
3. **Movimiento** — Suave, no brusco (sin saltos)
4. **Texto** — Legible, bien posicionado, animación natural
5. **Color** — Agradable, coherente entre fotos
6. **Transiciones** — Suaves, no distractivas

Escala: ⭐ (básico) a ⭐⭐⭐⭐⭐ (CapCut quality)
