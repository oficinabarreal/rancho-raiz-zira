#!/usr/bin/env node

import fs from 'fs';
import { exec } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join, basename, extname } from 'path';
import { sendVideo } from './telegram.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PROJECT_ROOT = '/data/data/com.termux/files/home/publicidad';
const DOWNLOADS = '/data/data/com.termux/files/home/downloads';
const DIR_IMGS = join(PROJECT_ROOT, 'lab', 'imgs');
const DIR_OUTPUT = join(DOWNLOADS, 'rancho-raiz-publicidad', '_WORKING_CYCLE');

const DB_PATH = join(__dirname, 'assets', 'db.json');
let DB = null;

const COLORES = {
  primario: '0xEAE4D3',
  secundario: '0xC5A059',
  blanco: '0xFFFFFF'
};

const VARIANTES = [
  { id: 'base', nombre: 'Base', vfExtra: '', descripcion: 'Ken Burns + texto' },
  { id: 'cinematic', nombre: 'Cinematic', vfExtra: ',drawbox=x=0:y=0:w=iw:h=160:color=black@1:t=fill,drawbox=x=0:y=ih-160:w=iw:h=160:color=black@1:t=fill', descripcion: '+ barras negras' },
  { id: 'vibrante', nombre: 'Vibrante', vfExtra: ',eq=contrast=1.15:saturation=1.3:brightness=0.02', descripcion: '+ color boost' },
  { id: 'suave', nombre: 'Suave', vfExtra: ',eq=contrast=1.05:saturation=0.95:brightness=0.01', descripcion: '+ tono natural' }
];

const KEN_BURNS = {
  center: {
    nombre: 'Centro',
    descripcion: 'Zoom hacia el centro (default)',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*0.5'
  },
  top_left: {
    nombre: 'Arriba Izquierda',
    descripcion: 'Zoom hacia esquina superior izquierda',
    x: '(iw-iw/zoom)*0.2',
    y: '(ih-ih/zoom)*0.2'
  },
  top_right: {
    nombre: 'Arriba Derecha',
    descripcion: 'Zoom hacia esquina superior derecha',
    x: '(iw-iw/zoom)*0.8',
    y: '(ih-ih/zoom)*0.2'
  },
  bottom_left: {
    nombre: 'Abajo Izquierda',
    descripcion: 'Zoom hacia esquina inferior izquierda',
    x: '(iw-iw/zoom)*0.2',
    y: '(ih-ih/zoom)*0.8'
  },
  bottom_right: {
    nombre: 'Abajo Derecha',
    descripcion: 'Zoom hacia esquina inferior derecha',
    x: '(iw-iw/zoom)*0.8',
    y: '(ih-ih/zoom)*0.8'
  },
  top: {
    nombre: 'Arriba',
    descripcion: 'Zoom hacia la parte superior',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*0.2'
  },
  bottom: {
    nombre: 'Abajo',
    descripcion: 'Zoom hacia la parte inferior',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*0.8'
  },
  pan_left_to_right: {
    nombre: 'Pan Izq → Der',
    descripcion: 'Barre de izquierda a derecha mientras hace zoom',
    x: '(iw-iw/zoom)*(0.2 + 0.6*on/(30*5))',
    y: '(ih-ih/zoom)*0.5'
  },
  pan_right_to_left: {
    nombre: 'Pan Der → Izq',
    descripcion: 'Barre de derecha a izquierda mientras hace zoom',
    x: '(iw-iw/zoom)*(0.8 - 0.6*on/(30*5))',
    y: '(ih-ih/zoom)*0.5'
  },
  pan_top_to_bottom: {
    nombre: 'Pan Arr → Aba',
    descripcion: 'Barre de arriba hacia abajo mientras hace zoom',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*(0.2 + 0.6*on/(30*5))'
  },
  pan_bottom_to_top: {
    nombre: 'Pan Aba → Arr',
    descripcion: 'Barre de abajo hacia arriba mientras hace zoom',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*(0.8 - 0.6*on/(30*5))'
  },
  zoom_out: {
    nombre: 'Zoom Out',
    descripcion: 'Alejamiento en lugar de acercamiento',
    x: '(iw-iw/zoom)*0.5',
    y: '(ih-ih/zoom)*0.5',
    startZoom: 1.15,
    endZoom: 1.0,
    zoomExpr: "max(1.15-0.001*on,1.0)"
  }
};

const ANIMACIONES_TEXTO = {
  fade: {
    nombre: 'Fade In',
    descripcion: 'Aparece suavemente (default)',
    texto1: (t) => `alpha=if(lt(${t},0.3),0,if(lt(${t},1.0),(${t}-0.3)/0.7,1))`,
    texto2: (t) => `alpha=if(lt(${t},0.8),0,if(lt(${t},1.3),(${t}-0.8)/0.5,1))`
  },
  
  slide_up: {
    nombre: 'Slide Up',
    descripcion: 'Sube desde abajo',
    entrada: 'desde y=h+100 hasta y=final',
  },
};

const TRANSICIONES = [
  'fade', 'fadeblack', 'circleopen', 'circleclose', 'wipeleft', 
  'slideright', 'slideup', 'dissolve', 'diagtl', 'zoomin'
];

const OVERLAYS = {
  cinematic: {
    nombre: 'Cinematic Bars',
    descripcion: 'Barras negras superior e inferior fijas',
    vf: ',drawbox=x=0:y=0:w=iw:h=180:color=black@0.9:t=fill,drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.9:t=fill'
  },
  cinematic_thin: {
    nombre: 'Cinematic Delgado',
    descripcion: 'Barras negras mas delgadas',
    vf: ',drawbox=x=0:y=0:w=iw:h=100:color=black@0.9:t=fill,drawbox=x=0:y=ih-100:w=iw:h=100:color=black@0.9:t=fill'
  },
  gradient_top: {
    nombre: 'Gradiente Superior',
    descripcion: 'Gradiente oscuro en la parte superior para legibilidad de texto',
    vf: ''
  },
  vignette: {
    nombre: 'Vignette',
    descripcion: 'Oscurecimiento en las esquinas para enfoque en el centro',
    vf: ',vignette=angle=0.5'
  }
};

function cargarDB() {
  if (DB) return DB;
  try {
    DB = JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
    return DB;
  } catch (e) {
    console.error('Error cargando DB:', e.message);
    return null;
  }
}

function asegurarDir(ruta) {
  if (!fs.existsSync(ruta)) fs.mkdirSync(ruta, { recursive: true });
}

function buscarFotoPorNumero(numero) {
  cargarDB();
  if (!DB) return null;
  const num = parseInt(numero);
  return DB.fotos._index.find(f => f._numero_original === num) || null;
}

function obtenerTexto(foto, idx = 0) {
  if (foto.texto_overlay && foto.texto_overlay.length > idx) {
    return foto.texto_overlay[idx];
  }
  if (foto.tags?.includes('pileta')) return 'VERANO EN LAS MONTAÑAS';
  if (foto.tags?.includes('noche')) return 'NOCHES MÁGICAS';
  if (foto.tags?.includes('atardecer')) return 'ATARDECERES INOLVIDABLES';
  return 'RANCHO RAÍZ';
}

function ejecutar(comando, descripcion) {
  return new Promise((resolve, reject) => {
    console.log(`\n🎬 ${descripcion}`);
    exec(comando, (error, stdout, stderr) => {
      if (error) {
        console.log(`   ⚠️  Error: ${error.message?.substring(0, 150) || 'falló'}`);
        resolve(false);
        return;
      }
      console.log(`   ✅ OK`);
      resolve(true);
    });
  });
}

const ESTILOS_SIMPLES = {
  fade: {
    id: 'fade',
    nombre: 'Fade In',
    dt1: `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='T1':fontcolor=C:fontsize=70:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,1))'`,
    dt2: `drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='T2':fontcolor=C:fontsize=40:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,1))'`
  }
};

function makeDrawtextSimple(texto1, texto2, estilo = 'fade') {
  const shadow = 'shadowcolor=black@0.7:shadowx=4:shadowy=4';
  const shadow2 = 'shadowcolor=black@0.5:shadowx=2:shadowy=2';
  
  if (estilo === 'fade' || true) {
    return `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:x=(w-tw)/2:y=150:${shadow}:alpha=if(lt(t\\,0.3)\\,0\\,if(lt(t\\,1.0)\\,(t-0.3)/0.7\\,1)),drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:x=(w-tw)/2:y=h-th-120:${shadow2}:alpha=if(lt(t\\,0.8)\\,0\\,if(lt(t\\,1.3)\\,(t-0.8)/0.5\\,1))`;
  }
}

function construirZoompan(opciones = {}) {
  const duracion = opciones.duracion || 5;
  const fps = 30;
  const totalFrames = duracion * fps;
  
  const kbId = opciones.kenBurns || 'center';
  const kb = KEN_BURNS[kbId] || KEN_BURNS.center;
  
  const zoomSpeed = opciones.zoomSpeed || 0.001;
  const zoomMax = opciones.zoomMax || 1.12;
  
  if (kb.zoomExpr) {
    return `zoompan=z='${kb.zoomExpr}':x='${kb.x}':y='${kb.y}':d=1:s=1080x1920:fps=${fps},format=yuv420p`;
  }
  
  const x = kb.x || '(iw-iw/zoom)*0.5';
  const y = kb.y || '(ih-ih/zoom)*0.5';
  
  const xFinal = x.replace('/(30\\*5)', `/(${fps}*${duracion})`);
  const yFinal = y.replace('/(30\\*5)', `/(${fps}*${duracion})`);
  
  return `zoompan=z='min(zoom+${zoomSpeed},${zoomMax})':x='${xFinal}':y='${yFinal}':d=1:s=1080x1920:fps=${fps},format=yuv420p`;
}

function construirOverlay(opciones = {}) {
  const overlayTipo = opciones.overlay || null;
  if (!overlayTipo) return '';
  
  if (overlayTipo === 'cinematic' || overlayTipo === 'cinematic_thin') {
    return OVERLAYS[overlayTipo]?.vf || '';
  }
  if (overlayTipo === 'vignette') {
    return OVERLAYS.vignette.vf;
  }
  if (overlayTipo === 'full') {
    return ',drawbox=x=0:y=0:w=iw:h=180:color=black@0.9:t=fill,drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.9:t=fill';
  }
  return '';
}

async function generarVideoBase(foto, outputPath, opciones = {}) {
  const duracion = opciones.duracion || 5;
  const texto1 = opciones.texto1 || obtenerTexto(foto, 0);
  const texto2 = opciones.texto2 || '@RANCHORAIZ.POSADA';
  const estilo = opciones.estilo || 'fade';
  
  const fotoPath = join(DIR_IMGS, foto.archivo);
  if (!fs.existsSync(fotoPath)) {
    console.log(`   ❌ No existe: ${fotoPath}`);
    return false;
  }
  
  const zoom = construirZoompan(opciones);
  const overlay = construirOverlay(opciones);
  
  let textoFilters = '';
  
  if (estilo === 'fade') {
    const alpha1 = `alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,1))'`;
    const alpha2 = `alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,1))'`;
    
    textoFilters = `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:${alpha1},drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:${alpha2}`;
  }
  else if (estilo === 'slide_up') {
    const y1 = `y='if(lt(t,0.3),h+100,if(lt(t,1.0),h+100-(h+100-150)*(t-0.3)/0.7,150))'`;
    const y2 = `y='if(lt(t,0.8),h+50,if(lt(t,1.3),h+50-(h+50-(h-th-120))*(t-0.8)/0.5,h-th-120))'`;
    
    textoFilters = `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:x=(w-tw)/2:${y1}:shadowcolor=black@0.7:shadowx=4:shadowy=4,drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:x=(w-tw)/2:${y2}:shadowcolor=black@0.5:shadowx=2:shadowy=2`;
  }
  else if (estilo === 'slide_left') {
    const x1 = `x='if(lt(t,0.3),-tw-100,if(lt(t,1.0),-tw-100+((w-tw)/2 - (-tw-100))*(t-0.3)/0.7,(w-tw)/2))'`;
    const x2 = `x='if(lt(t,0.8),-tw-100,if(lt(t,1.3),-tw-100+((w-tw)/2 - (-tw-100))*(t-0.8)/0.5,(w-tw)/2))'`;
    
    textoFilters = `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:${x1}:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4,drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:${x2}:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2`;
  }
  else if (estilo === 'pulse') {
    const a1 = `alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,0.85+0.15*sin(2*PI*(t-1.0))))'`;
    const a2 = `alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,0.85+0.1*sin(2*PI*(t-1.3))))'`;
    
    textoFilters = `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:${a1},drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:${a2}`;
  }
   else {
     const a1 = `alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,1))'`;
     const a2 = `alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,1))'`;
     
     textoFilters = `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${texto1}':fontcolor=${COLORES.primario}:fontsize=70:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:${a1},drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${texto2}':fontcolor=${COLORES.secundario}:fontsize=40:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:${a2}`;
   }
   
   let vf = `${zoom}`;
   if (overlay) {
     vf += overlay;
   }
   vf += `,${textoFilters}`;
  
  const cmd = `ffmpeg -loop 1 -i "${fotoPath}" -f lavfi -i anullsrc=r=44100:cl=stereo -t ${duracion} -vf "${vf}" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "${outputPath}" -y`;
  
  return ejecutar(cmd, `${estilo}: ${texto1.substring(0, 30)}...`);
}

async function generarSlide(foto, outputPath, opciones = {}) {
  return generarVideoBase(foto, outputPath, opciones);
}

async function unirConTransicion(v1, v2, transicion, durTrans, outPath) {
  const offset = 3;
  
  const cmd = `ffmpeg -i "${v1}" -i "${v2}" -filter_complex "[0:v][1:v]xfade=transition=${transicion}:duration=${durTrans}:offset=${offset}[v];[0:a][1:a]acrossfade=d=${durTrans}[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac "${outPath}" -y`;
  
  return ejecutar(cmd, `transicion: ${transicion}`);
}

async function slideshowDesdeFotos(fotos, opciones = {}) {
  asegurarDir(DIR_OUTPUT);
  
  const estilo = opciones.estilo || 'fade';
  const nombre = opciones.nombre || 'slideshow';
  const outputPath = opciones.outputPath || join(DIR_OUTPUT, `${nombre}_${Date.now()}.mp4`);
  const durFoto = opciones.duracionFoto || 4;
  const durTrans = opciones.durTrans || 0.8;
  const transiciones = opciones.transiciones || TRANSICIONES;
  
  console.log(`\n╔════════════════════════════════════════════════════════════╗`);
  console.log(`║  SLIDESHOW: ${fotos.length} fotos | Estilo: ${estilo}       ║`);
  console.log(`╚════════════════════════════════════════════════════════════╝`);
  
  const slides = [];
  const temps = [];
  
  for (let i = 0; i < fotos.length; i++) {
    const tempPath = join(DIR_OUTPUT, `slide_${nombre}_${i}.mp4`);
    temps.push(tempPath);
    
     const exito = await generarSlide(fotos[i], tempPath, { 
       estilo, 
       duracion: durFoto,
       zoomSpeed: 0.0008,
       kenBurns: opciones.kenBurns
     });
    
    if (exito && fs.existsSync(tempPath)) {
      slides.push(tempPath);
    }
  }
  
  if (slides.length < 1) {
    console.log('❌ No se generaron slides');
    return null;
  }
  
  if (slides.length === 1) {
    if (slides[0] !== outputPath) {
      fs.renameSync(slides[0], outputPath);
    }
    console.log(`✅ Single: ${outputPath}`);
    return outputPath;
  }
  
  console.log(`\n🔗 Uniendo con transiciones...`);
  
  let actual = slides[0];
  
  for (let i = 1; i < slides.length; i++) {
    const trans = transiciones[(i - 1) % transiciones.length];
    const tempOut = join(DIR_OUTPUT, `merge_${nombre}_${i}.mp4`);
    temps.push(tempOut);
    
    await unirConTransicion(actual, slides[i], trans, durTrans, tempOut);
    
    if (i > 1 && actual !== slides[0] && fs.existsSync(actual)) {
      try { fs.unlinkSync(actual); } catch(e){}
    }
    
    actual = tempOut;
  }
  
  if (fs.existsSync(actual)) {
    fs.renameSync(actual, outputPath);
    console.log(`\n✅ COMPLETO: ${outputPath}`);
  }
  
  temps.forEach(t => {
    if (fs.existsSync(t) && t !== outputPath) {
      try { fs.unlinkSync(t); } catch(e){}
    }
  });
  
  return outputPath;
}

async function mezclarAudio(videoPath, audioPath, volumen = 0.25) {
  if (!audioPath || !videoPath || !fs.existsSync(videoPath)) return videoPath;
  if (!fs.existsSync(audioPath)) {
    console.log(`   ⚠️ Audio no encontrado: ${audioPath}`);
    return videoPath;
  }
  
  const d = dirname(videoPath);
  const e = extname(videoPath);
  const b = basename(videoPath, e);
  const outPath = join(d, `${b}_con_audio${e}`);

  const cmd = `ffmpeg -i "${videoPath}" -i "${audioPath}" -filter_complex "[1:a]volume=${volumen}[a]" -c:v copy -c:a aac -shortest -map 0:v:0 -map "[a]" "${outPath}" -y 2>/dev/null`;
  
  await ejecutar(cmd, `Mezclando audio: ${basename(audioPath)}`);
  
  if (fs.existsSync(outPath)) {
    try { fs.unlinkSync(videoPath); } catch(e) {}
    return outPath;
  }
  return videoPath;
}

async function slideshowPorTema(tema, opciones = {}) {
  cargarDB();
  asegurarDir(DIR_OUTPUT);
  
  const temas = {
    pileta: { tags: ['pileta', 'piscina', 'agua'], nombre: 'Piletas' },
    noche: { tags: ['noche', 'luna', 'estrellas'], nombre: 'Noches' },
    atardecer: { tags: ['atardecer', 'tarde'], nombre: 'Atardeceres' },
    montanas: { tags: ['montanas', 'paisaje', 'andes'], nombre: 'Vistas' },
    branding: { tags: ['logo', 'marca', 'rancho'], nombre: 'Marca' }
  };
  
  if (!temas[tema]) {
    console.log(`Temas: ${Object.keys(temas).join(', ')}`);
    return null;
  }
  
  const config = temas[tema];
  
  let fotos = [];
  for (const tag of config.tags) {
    const conTag = DB.fotos._index.filter(f => 
      f.tags?.some(t => t.toLowerCase().includes(tag.toLowerCase()))
    );
    fotos = [...fotos, ...conTag];
  }
  
  const unicas = [];
  const vistos = new Set();
  for (const f of fotos) {
    if (!vistos.has(f._numero_original)) {
      vistos.add(f._numero_original);
      unicas.push(f);
    }
  }
  
  if (unicas.length === 0) {
    console.log(`No hay fotos para: ${tema}`);
    return null;
  }
  
  console.log(`\n🎯 Tema: ${config.nombre} | ${unicas.length} fotos`);
  
  return slideshowDesdeFotos(unicas, {
    nombre: tema,
    estilo: opciones.estilo || 'fade',
    kenBurns: opciones.kenBurns || 'center',
    outputPath: join(DIR_OUTPUT, `slideshow_${tema}_${Date.now()}.mp4`)
  });
}

function mostrarAyuda() {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║  RANCHOCUT v6 - Ken Burns Direccional + Texto + Slideshows ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  USO:                                                        ║
║    node ranchocut/lab.js --foto=19                          ║
║    node ranchocut/lab.js --foto=19 --estilo=slide_up       ║
║    node ranchocut/lab.js --foto=19 --kenburns=top_left     ║
║    node ranchocut/lab.js --foto=19 --kenburns=pan_left_to_right ║
║                                                              ║
║    node ranchocut/lab.js --slideshow=pileta                 ║
║    node ranchocut/lab.js --slideshow=noche --kenburns=zoom_out ║
║                                                              ║
║    node ranchocut/lab.js --manual=19,6,11,5                ║
║                                                              ║
╠════════════════════════════════════════════════════════════╣
║  --audio=NOMBRE.mp3   = Agregar musica de fondo (ver lista)║
║  --telegram           = Enviar video a Telegram al terminar ║
║                                                              ║
╠════════════════════════════════════════════════════════════╣
║  LISTAR OPCIONES:                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  --estilos            = Lista estilos de texto              ║
║  --kenburns-tipos     = Lista tipos de Ken Burns (12 modos) ║
║                                                              ║
╠════════════════════════════════════════════════════════════╣
║  TIPOS de KEN BURNS (12 modos):                             ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  ESTATICOS (zoom hacia punto fijo):                          ║
║  • center, top_left, top_right, bottom_left, bottom_right   ║
║  • top, bottom                                               ║
║                                                              ║
║  DINAMICOS (barrido + zoom):                                ║
║  • pan_left_to_right, pan_right_to_left                     ║
║  • pan_top_to_bottom, pan_bottom_to_top                     ║
║  • zoom_out (alejamiento en vez de acercamiento)            ║
║                                                              ║
╠════════════════════════════════════════════════════════════╣
║  WORKFLOW HIBRIDO (Three.js + FFmpeg):                      ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  PASO 1: Generar overlay HTML:                               ║
║     Abrir en navegador: ranchocut/overlay-generator.html    ║
║     o efectos avanzados:                                     ║
║     lab/arte-gallery/transiciones/01-scramble.html         ║
║     lab/arte-gallery/transiciones/03-wave-reveal.html      ║
║                                                              ║
║  PASO 2: Grabar overlay (boton "GRABAR" en HTML)           ║
║     Descarga: overlay_rancho_XXXXXX.webm                    ║
║                                                              ║
║  PASO 3: Overlay con FFmpeg (fondo transparente):           ║
║                                                              ║
║  Overlay simple:                                             ║
║  ffmpeg -i base.mp4 -i overlay.webm -filter_complex         ║
║    "[0:v][1:v]overlay[out]" -map "[out]" -map 0:a final.mp4║
║                                                              ║
║  Overlay con chroma key (si fondo es color solido):         ║
║  ffmpeg -i base.mp4 -i overlay.mp4 -filter_complex          ║
║    "[1:v]chromakey=0x000000:0.1[ovr];[0:v][ovr]overlay[out]"║
║    -map "[out]" -map 0:a final.mp4                           ║
║                                                              ║
║  Overlay de texto SOLO (barras negras conservan video):     ║
║  ffmpeg -i base.mp4 -i overlay.webm -filter_complex         ║
║    "[1:v]alphaextract[alf];[0:v][1:v][alf]overlay[out]"    ║
║    -map "[out]" -map 0:a final.mp4                           ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
  `);
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    mostrarAyuda();
    return;
  }
  
  let fotoNum = null;
  let variante = null;
  let texto1 = null;
  let texto2 = null;
  let slideshowTema = null;
  let manualFotos = null;
  let duracion = null;
  let outputPath = null;
   let estilo = 'fade';
   let kenBurns = 'center';
   let overlay = null;
    let listarEstilos = false;
    let listarKenBurns = false;
     let listarOverlays = false;
     let listarAudio = false;
     let enviarTelegram = false;
     let audioFile = null;
  
  args.forEach(arg => {
    if (arg.startsWith('--foto=')) {
      fotoNum = parseInt(arg.replace('--foto=', ''));
    } else if (arg.startsWith('--audio=')) {
      audioFile = arg.replace('--audio=', '');
    } else if (arg.startsWith('--variante=')) {
      variante = arg.replace('--variante=', '');
    } else if (arg.startsWith('--texto1=')) {
      texto1 = arg.replace('--texto1=', '');
    } else if (arg.startsWith('--texto2=')) {
      texto2 = arg.replace('--texto2=', '');
    } else if (arg.startsWith('--slideshow=')) {
      slideshowTema = arg.replace('--slideshow=', '');
    } else if (arg.startsWith('--manual=')) {
      manualFotos = arg.replace('--manual=', '').split(',').map(n => parseInt(n.trim()));
    } else if (arg.startsWith('--duracion=')) {
      duracion = parseInt(arg.replace('--duracion=', ''));
    } else if (arg.startsWith('--output=')) {
      outputPath = arg.replace('--output=', '');
     } else if (arg.startsWith('--estilo=')) {
       estilo = arg.replace('--estilo=', '');
     } else if (arg.startsWith('--kenburns=')) {
       kenBurns = arg.replace('--kenburns=', '');
     } else if (arg.startsWith('--overlay=')) {
       overlay = arg.replace('--overlay=', '');
     } else if (arg === '--estilos' || arg === '--listar-estilos') {
       listarEstilos = true;
     } else if (arg === '--kenburns-tipos' || arg === '--listar-kenburns') {
       listarKenBurns = true;
      } else if (arg === '--overlays' || arg === '--listar-overlays') {
        listarOverlays = true;
       } else if (arg === '--telegram') {
         enviarTelegram = true;
       } else if (arg === '--listar-audio' || arg === '--audios') {
         listarAudio = true;
       }
   });
  
   if (listarOverlays) {
     console.log(`\n📹 Overlays disponibles:\n`);
     console.log(`   cinematic        - Barras negras gruesas (180px)`);
     console.log(`   cinematic_thin   - Barras negras delgadas (100px)`);
     console.log(`   vignette         - Oscurecimiento de esquinas`);
     console.log(`   full             - Barras + efectos combinados`);
     return;
   }

   if (listarKenBurns) {
     console.log(`\n🎥 Tipos de Ken Burns disponibles:\n`);
     Object.keys(KEN_BURNS).forEach(id => {
       const kb = KEN_BURNS[id];
       console.log(`   ${id.padEnd(20)} - ${kb.nombre}: ${kb.descripcion}`);
     });
     return;
   }

   if (listarEstilos) {
     console.log(`\n🎨 Estilos de texto disponibles:\n`);
     console.log('   fade      - Por defecto. Aparece suavemente');
     console.log('   slide_up  - Sube desde abajo');
     console.log('   slide_left- Entra desde la izquierda');
     console.log('   pulse     - Aparece y luego pulsa');
     console.log(`\n🎬 Transiciones de video disponibles (${TRANSICIONES.length}):`);
     console.log(`   ${TRANSICIONES.slice(0, 6).join(', ')}...`);
     return;
   }

   if (listarAudio) {
     const AUDIO_DIR = '/data/data/com.termux/files/home/ranchoraiz_reels/audio';
     if (fs.existsSync(AUDIO_DIR)) {
       const files = fs.readdirSync(AUDIO_DIR).filter(f => f.endsWith('.mp3'));
       console.log(`\n🎵 Audios disponibles (${files.length}):\n`);
       files.forEach(f => {
         const size = fs.statSync(join(AUDIO_DIR, f)).size;
         const mb = (size / 1024 / 1024).toFixed(2);
         console.log(`   ${f.padEnd(35)} ${mb} MB`);
       });
       console.log(`\n   Usar: --audio=NOMBRE.mp3`);
     } else {
       console.log('\n   No hay audios descargados.');
       console.log('   Ejecuta: node ranchocut/descargar-audio.js');
     }
     return;
   }
  
  const estilosValidos = ['fade', 'slide_up', 'slide_left', 'pulse'];
  if (!estilosValidos.includes(estilo)) {
    console.log(`⚠️  Estilo "${estilo}" no válido. Usando "fade".`);
    console.log(`   Opciones: ${estilosValidos.join(', ')}`);
    estilo = 'fade';
  }
  
  cargarDB();

  const AUDIO_DIR = '/data/data/com.termux/files/home/ranchoraiz_reels/audio';
  const audioPath = audioFile ? join(AUDIO_DIR, audioFile) : null;
  
   if (slideshowTema) {
     let out = await slideshowPorTema(slideshowTema, { estilo, kenBurns, overlay });
     if (out && audioPath) out = await mezclarAudio(out, audioPath);
     if (enviarTelegram && out) {
       const tg = await sendVideo(out, `🎬 ${slideshowTema} | ${kenBurns} | ${estilo}`);
       console.log(tg.ok ? '   📤 Enviado a Telegram' : `   ⚠️ Telegram: ${tg.error}`);
     }
     return;
   }
   
   if (manualFotos && manualFotos.length > 0) {
     const fotos = manualFotos.map(n => buscarFotoPorNumero(n)).filter(Boolean);
     
     if (fotos.length === 0) {
       console.log('No se encontraron fotos');
       return;
     }
     
     let out = await slideshowDesdeFotos(fotos, {
        nombre: 'manual',
        estilo,
        kenBurns,
        overlay,
        outputPath: outputPath || join(DIR_OUTPUT, `slideshow_manual_${Date.now()}.mp4`)
     });
     if (out && audioPath) out = await mezclarAudio(out, audioPath);
     if (enviarTelegram && out) {
       const tg = await sendVideo(out, `🎬 Manual | ${kenBurns} | ${estilo}`);
       console.log(tg.ok ? '   📤 Enviado a Telegram' : `   ⚠️ Telegram: ${tg.error}`);
     }
     return;
   }
  
  if (fotoNum) {
    asegurarDir(DIR_OUTPUT);
    const foto = buscarFotoPorNumero(fotoNum);
    
    if (!foto) {
      console.log(`Foto #${fotoNum} no encontrada`);
      return;
    }
    
    console.log(`\n📸 Foto #${foto._numero_original}`);
    console.log(`   ${foto.descripcion?.substring(0, 60)}...`);
    console.log(`   🎨 Estilo: ${estilo}`);
    
    const t1 = texto1 || obtenerTexto(foto, 0);
    const t2 = texto2 || '@RANCHORAIZ.POSADA';
    
    const out = outputPath || join(DIR_OUTPUT, 
      `${String(fotoNum).padStart(2, '0')}_${estilo}_${Date.now()}.mp4`);
    
     await generarVideoBase(foto, out, { 
        estilo, 
        kenBurns,
        overlay,
        texto1: t1, 
        texto2: t2,
        duracion: duracion || 5
      });
     
     let outputFinal = out;
     if (audioPath) outputFinal = await mezclarAudio(out, audioPath);
     
     console.log(`\n📍 Output: ${outputFinal}`);
     if (enviarTelegram) {
       const tg = await sendVideo(outputFinal, `📸 Foto #${fotoNum} | ${kenBurns} | ${estilo}`);
       console.log(tg.ok ? '   📤 Enviado a Telegram' : `   ⚠️ Telegram: ${tg.error}`);
     }
     return;
  }
  
  mostrarAyuda();
}

main().catch(err => {
  console.error('\n❌ Error:', err.message);
  console.error(err.stack);
});
