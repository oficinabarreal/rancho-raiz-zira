# Plantilla de Receta

```json
{
  "id": "NOMBRE-UNICO",
  "fecha": "2026-05-27",
  "version": 1,
  "nombre": "Nombre Descriptivo",
  "descripcion": "Qué prueba esta receta y por qué",

  "herramientas": ["ffmpeg"],
  "tecnologia_principal": "ffmpeg",

  "params": {
    "kenBurns": "center",
    "estilo": "fade",
    "overlay": null,
    "colorGrade": null,
    "duracion": 4,
    "zoomSpeed": 0.0008,
    "zoomMax": 1.12,
    "transiciones": ["fade", "fadeblack", "circleopen"],
    "fontSize_titulo": 70,
    "fontSize_subtitulo": 40,
    "fps": 30
  },

  "fotos": [6, 11, 19, 8],
  "texto_titulo": "AUTO",
  "texto_subtitulo": "@RANCHORAIZ.POSADA",

  "calidad": {
    "estado": "candidato",
    "evaluacion": null,
    "estrellas": null,
    "tamano_mb": null,
    "duracion_seg": null,
    "notas": null
  },

  "tags": ["kenburns", "fade", "basico"]
}
```

---

## Campos

| Campo | Descripción |
|-------|-------------|
| `id` | Identificador único (snake_case) |
| `fecha` | Fecha de creación |
| `version` | Versión de la receta |
| `nombre` | Nombre legible |
| `descripcion` | Hipótesis: qué queremos probar |
| `herramientas` | Array: ffmpeg, threejs, canvas, nvidia-nim |
| `params` | Parámetros exactos del pipeline |
| `params.kenBurns` | Uno de los 12 modos |
| `params.estilo` | fade, slide_up, slide_left, pulse |
| `params.overlay` | null, cinematic, cinematic_thin, vignette |
| `params.colorGrade` | null, vibrante, suave, sepia, b&w |
| `params.duracion` | Segundos por foto |
| `params.zoomSpeed` | Velocidad de zoom (0.0005-0.001) |
| `params.zoomMax` | Zoom máximo (1.08-1.20) |
| `params.transiciones` | Array de tipos xfade |
| `params.fontSize_titulo` | Tamaño del título en px |
| `params.fontSize_subtitulo` | Tamaño del subtítulo en px |
| `fotos` | Array de números de foto |
| `texto_titulo` | "AUTO" usa detección por tags |
| `calidad.estado` | candidato, probado, aprobado, estandar |
| `calidad.evaluacion` | Texto de evaluación |
| `calidad.estrellas` | ⭐ a ⭐⭐⭐⭐⭐ |
| `tags` | Para búsqueda y agrupación |

---

## Estados

| Estado | Significado |
|--------|-------------|
| `candidato` | Receta propuesta, no probada |
| `probado` | Video generado, pendiente de evaluar |
| `aprobado` | Evaluado positivamente |
| `estandar` | Incorporado al pipeline principal |

---

## Estrategias de Exploración Sugeridas

### Semana 1: Base FFmpeg
Variar Ken Burns + estilo + overlay sobre las mismas fotos.

### Semana 2: Color Grading
Probar eq (contraste/saturación/brillo), curvas, colorbalance (evitando bug).

### Semana 3: Transiciones
Probar diferentes combinaciones y duraciones de xfade.

### Semana 4: Híbrido
Probar overlays de Three.js + FFmpeg base.
