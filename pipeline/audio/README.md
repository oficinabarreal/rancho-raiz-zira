# 🎵 Pipeline de Audio — Rancho Raíz

> Última actualización: 3 Jun 2026

---

## 📦 Fuente principal: audionautix.com

**Artista:** Jason Shaw  
**Licencia:** Creative Commons Attribution 4.0 (requiere atribución)  
**URL base:** `https://audionautix.com/Music/`  
**Script de descarga:** `pipeline/scripts/descargar-audio.js`

### Tracks disponibles

| Archivo | Tema | Mood | Tags IG |
|---|---|---|---|
| `RiverMeditation.mp3` | pileta, agua, relax | Relaxing, Uplifting | #Pileta #Relax |
| `AutumnSunset.mp3` | atardecer, dorado | Calming, Relaxing | #Atardecer #Calma |
| `GreenLeaves.mp3` | montaña, naturaleza | Calming, Uplifting | #Naturaleza |
| `PaperWings.mp3` | noche, estrellas | Calming, Bright | #Noche #Estrellas |
| `RedwoodTrail.mp3` | bosque, sendero | Soothing, Bright | #Bosque |
| `OpenRoad.mp3` | viaje, aventura | Driving, Uplifting | #Viaje |
| `AcousticGuitar1.mp3` | logo, marca, cálido | Calming, Relaxing | #Logo #Marca |
| `OneFineDay.mp3` | día soleado, feliz | Calming, Soothing | #Día #Feliz |
| `RunningWatersFullTrack.mp3` | agua corriente, largo | Calming, Bright | #Agua |
| `AcousticShuffle.mp3` | ritmo, brillante | Grooving, Bright | — |
| `HappyStrummin.mp3` | alegre | Bright, Uplifting | — |
| `LandrasDream.mp3` | soñador | Bright, Uplifting | — |
| `Serenity.mp3` | serenidad | Calming, Relaxing | — |

### Mapeo tema → audio

```
pileta/agua/piscina      → RiverMeditation.mp3
atardecer/sol/ocaso      → AutumnSunset.mp3
montaña/paisaje/cerro    → GreenLeaves.mp3
noche/luna/estrellas     → PaperWings.mp3
naturaleza/bosque/río    → RedwoodTrail.mp3
logo/marca               → AcousticGuitar1.mp3
viaje/camino             → OpenRoad.mp3
día/feliz/alegría        → HappyStrummin.mp3 o OneFineDay.mp3
```

---

## 🌿 Sonidos de naturaleza — para futuras descargas

Además de música, conviene tener sonidos ambiente reales para:
- Videos de pileta → agua corriendo, chapoteo
- Videos de noche → grillos, viento suave, búho
- Videos de montaña → viento, aves rapaces
- Videos de bosque → pájaros, arroyo
- Videos de fogata → fuego crepitante

### Fuentes recomendadas (royalty-free)

| Fuente | URL | Licencia |
|---|---|---|
| **freesound.org** | https://freesound.org | CC0/Attribution — buscar "nature", "stream", "birds" |
| **pixabay.com/sound-effects** | https://pixabay.com/sound-effects/ | Pixabay License (gratis, sin atribución) |
| **mixkit.co** | https://mixkit.co/free-sound-effects/nature/ | Mixkit License (gratis) |
| **uppbeat.io** | https://uppbeat.io | Gratis con atribución |
| **zapsplat.com** | https://www.zapsplat.com | Gratis con atribución |

### Sonidos prioritarios para Rancho Raíz

1. 💧 **Agua de pileta** — chapoteo suave, agua corriendo
2. 🔥 **Fogata** — fuego crepitante
3. 🦗 **Grillos de noche** — ambiente nocturno sereno
4. 🐦 **Pájaros de montaña** — amanecer en los Andes
5. 🌬️ **Viento en los árboles** — brisa suave
6. 🏞️ **Arroyo/río** — agua entre piedras
7. 🎻 **Música folclórica cuyana ** — opcional, para videos de identidad local

### Script de descarga sugerido

```bash
# Descargar de audionautix (usando script existente)
node pipeline/scripts/descargar-audio.js

# Descargar de freesound/pixabay (pendiente de implementar)
# Usar curl + API de freesound o scraper de pixabay
```

---

## 🛠️ Uso en el pipeline

1. **Para Reels:** `--audio=NOMBRE.mp3` en lab.js
   ```bash
   node pipeline/scripts/lab.js --slideshow=pileta --audio=RiverMeditation.mp3
   ```
2. **Para Zira overlay:** mezclar en FFmpeg con el mix_audio script
   ```bash
   python3 scripts/mix_audio_reels.py
   ```
3. **Para nuevos audios:** descargar desde audionautix
   ```bash
   node pipeline/scripts/descargar-audio.js River GreenLeaves
   ```

### Atribución requerida (CC BY 4.0)
En descripciones de IG incluir:
> "Música: Jason Shaw @ audionautix.com"
