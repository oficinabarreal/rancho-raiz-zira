# 📋 Diario de Experimentos

## 2026-05-27 — Día 1: Baseline + Primeras Recetas

### Propósito
Establecer el baseline de calidad actual con el pipeline FFmpeg existente.
Probar todas las combinaciones básicas (kenburns × estilo × overlay) como
punto de partida.

### Recetas del Día

| # | Receta | Fotos | KB | Texto | Overlay | Estado | Tamaño | Estrellas |
|---|--------|-------|----|-------|---------|--------|--------|-----------|
| 1 | `base-center-fade` | 6,11,19,8 | center | fade | — | ✅ probado | — | — |
| 2 | `pan-left-fade-cine` | 6,11,19,8 | pan_left_to_right | fade | cinematic | ✅ probado | 1.1 MB | ⭐⭐⭐⭐ |
| 3 | `zoomout-fade-cine` | 1,2,6,7 | zoom_out | fade | cinematic | ✅ probado | 1.8 MB | ⭐⭐⭐⭐ |
| 4 | `pan-right-slideleft-cine` | 11,3,5,22 | pan_right_to_left | slide_left | cinematic | ✅ probado | 892 KB | ⭐⭐⭐ |
| 5 | `pan-bottom-pulse-cine` | 3,4,13,8 | pan_bottom_to_top | pulse | cinematic | ✅ probado | 1.1 MB | ⭐⭐⭐⭐ |
| 6 | `center-pulse-cine` | 16,17,18 | center | pulse | cinematic | ✅ probado | 605 KB | ⭐⭐⭐ |
| 7 | `storytelling-pan-slide` | 16,19,5,2,18 | pan_left_to_right | slide_up | cinematic | ✅ probado | 1.1 MB | ⭐⭐⭐⭐⭐ |

### Conclusiones del Día
- El pipeline FFmpeg produce videos consistentes y sin errores
- Overlay cinemático es esencial para legibilidad del texto
- Pan dinámicos + slide_up dan el mejor resultado visual
- Combinación storytelling (logo → pileta → atardecer → noche → logo) funciona bien
- Tamaños entre 600 KB y 1.8 MB — dentro del estándar

### Próximas Recetas a Probar
- Probar color grading (vibrante, suave)
- Probar transiciones diferentes (no solo fade)
- Probar duraciones variables (3s, 5s)
- Probar zoom speeds diferentes
- Probar overlay vignette

---

## Cómo Agregar una Entrada

```markdown
## YYYY-MM-DD — Día N: Título

### Recetas del Día
| # | Receta | Fotos | KB | Texto | Overlay | Estado | Tamaño | Estrellas |
|---|--------|-------|----|-------|---------|--------|--------|-----------|

### Conclusiones
- ...

### Próximas Recetas
- ...
```
