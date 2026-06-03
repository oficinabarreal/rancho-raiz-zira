#!/usr/bin/env node

import fs from 'fs';
import { exec } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { sendVideo, sendMessage } from './telegram.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const RECETAS_DIR = join(__dirname, 'recetas');
const CATALOGO_PATH = join(RECETAS_DIR, 'catalogo.json');
const DIARIO_PATH = join(RECETAS_DIR, 'diario.md');
const DIR_OUTPUT = '/data/data/com.termux/files/home/downloads/rancho-raiz-publicidad/_WORKING_CYCLE';
const DIR_FINAL = '/data/data/com.termux/files/home/ranchoraiz_reels';
const DIR_IMGS = '/data/data/com.termux/files/home/publicidad/lab/imgs';
const DB_PATH = join(__dirname, 'assets', 'db.json');

const COLORES = {
  primario: '#EAE4D3',
  secundario: '#C5A059'
};

const OVERLAYS = {
  cinematic: ',drawbox=x=0:y=0:w=iw:h=180:color=black@0.9:t=fill,drawbox=x=0:y=ih-180:w=iw:h=180:color=black@0.9:t=fill',
  cinematic_thin: ',drawbox=x=0:y=0:w=iw:h=100:color=black@0.9:t=fill,drawbox=x=0:y=ih-100:w=iw:h=100:color=black@0.9:t=fill',
  vignette: ',vignette=angle=0.5'
};

const COLOR_GRADES = {
  vibrante: ',eq=contrast=1.15:saturation=1.3:brightness=0.02',
  suave: ',eq=contrast=1.05:saturation=0.95:brightness=0.01',
  sepia: ',colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131',
  b_w: ',hue=s=0'
};

const ESTILOS = {
  fade: (t1, t2, sz1, sz2) => {
    const a1 = "alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,1))'";
    const a2 = "alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,1))'";
    return [
      `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${t1}':fontcolor=0xEAE4D3:fontsize=${sz1}:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:${a1}`,
      `drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${t2}':fontcolor=0xC5A059:fontsize=${sz2}:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:${a2}`
    ].join(',');
  },
  slide_up: (t1, t2, sz1, sz2) => {
    const y1 = "y='if(lt(t,0.3),h+100,if(lt(t,1.0),h+100-(h+100-150)*(t-0.3)/0.7,150))'";
    const y2 = "y='if(lt(t,0.8),h+50,if(lt(t,1.3),h+50-(h+50-(h-th-120))*(t-0.8)/0.5,h-th-120))'";
    return [
      `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${t1}':fontcolor=0xEAE4D3:fontsize=${sz1}:x=(w-tw)/2:${y1}:shadowcolor=black@0.7:shadowx=4:shadowy=4`,
      `drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${t2}':fontcolor=0xC5A059:fontsize=${sz2}:x=(w-tw)/2:${y2}:shadowcolor=black@0.5:shadowx=2:shadowy=2`
    ].join(',');
  },
  slide_left: (t1, t2, sz1, sz2) => {
    const x1 = "x='if(lt(t,0.3),-tw-100,if(lt(t,1.0),-tw-100+((w-tw)/2 - (-tw-100))*(t-0.3)/0.7,(w-tw)/2))'";
    const x2 = "x='if(lt(t,0.8),-tw-100,if(lt(t,1.3),-tw-100+((w-tw)/2 - (-tw-100))*(t-0.8)/0.5,(w-tw)/2))'";
    return [
      `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${t1}':fontcolor=0xEAE4D3:fontsize=${sz1}:${x1}:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4`,
      `drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${t2}':fontcolor=0xC5A059:fontsize=${sz2}:${x2}:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2`
    ].join(',');
  },
  pulse: (t1, t2, sz1, sz2) => {
    const a1 = "alpha='if(lt(t,0.3),0,if(lt(t,1.0),(t-0.3)/0.7,0.85+0.15*sin(2*PI*(t-1.0))))'";
    const a2 = "alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,0.85+0.1*sin(2*PI*(t-1.3))))'";
    return [
      `drawtext=fontfile=/system/fonts/Roboto-Bold.ttf:text='${t1}':fontcolor=0xEAE4D3:fontsize=${sz1}:x=(w-tw)/2:y=150:shadowcolor=black@0.7:shadowx=4:shadowy=4:${a1}`,
      `drawtext=fontfile=/system/fonts/Roboto-Regular.ttf:text='${t2}':fontcolor=0xC5A059:fontsize=${sz2}:x=(w-tw)/2:y=h-th-120:shadowcolor=black@0.5:shadowx=2:shadowy=2:${a2}`
    ].join(',');
  }
};

function cargarCatalogo() {
  try {
    return JSON.parse(fs.readFileSync(CATALOGO_PATH, 'utf8'));
  } catch {
    return { recetas: [] };
  }
}

function guardarCatalogo(data) {
  fs.writeFileSync(CATALOGO_PATH, JSON.stringify(data, null, 2));
}

function cargarDB() {
  try {
    return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
  } catch {
    return null;
  }
}

function buscarFoto(numero) {
  const db = cargarDB();
  if (!db) return null;
  return db.fotos._index.find(f => f._numero_original === parseInt(numero)) || null;
}

function obtenerTexto(foto) {
  if (foto.texto_overlay && foto.texto_overlay.length > 0) return foto.texto_overlay[0];
  if (foto.tags?.includes('pileta')) return 'REFRESCA TUS SENTIDOS';
  if (foto.tags?.includes('noche')) return 'BAJO LAS ESTRELLAS';
  if (foto.tags?.includes('atardecer')) return 'ATARDECER DORADO';
  if (foto.tags?.includes('montanas')) return 'VISTAS QUE ENAMORAN';
  if (foto.tags?.includes('logo')) return 'RANCHO RAÍZ';
  return 'RANCHO RAÍZ';
}

function asegurarDir(ruta) {
  if (!fs.existsSync(ruta)) fs.mkdirSync(ruta, { recursive: true });
}

function ejecutar(comando, descripcion) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    process.stdout.write(`   ${descripcion}... `);
    exec(comando, (error, stdout, stderr) => {
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      if (error) {
        process.stdout.write(`❌ (${elapsed}s)\n`);
        resolve({ ok: false, error: error.message, elapsed });
        return;
      }
      process.stdout.write(`✅ (${elapsed}s)\n`);
      resolve({ ok: true, elapsed });
    });
  });
}

function construirZoompan(params) {
  const duracion = params.duracion || 4;
  const fps = params.fps || 30;
  const speed = params.zoomSpeed || 0.0008;
  const max = params.zoomMax || 1.12;
  const kb = params.kenBurns || 'center';

  const KEN_BURNS = {
    center: { x: '(iw-iw/zoom)*0.5', y: '(ih-ih/zoom)*0.5' },
    top_left: { x: '(iw-iw/zoom)*0.2', y: '(ih-ih/zoom)*0.2' },
    top_right: { x: '(iw-iw/zoom)*0.8', y: '(ih-ih/zoom)*0.2' },
    bottom_left: { x: '(iw-iw/zoom)*0.2', y: '(ih-ih/zoom)*0.8' },
    bottom_right: { x: '(iw-iw/zoom)*0.8', y: '(ih-ih/zoom)*0.8' },
    top: { x: '(iw-iw/zoom)*0.5', y: '(ih-ih/zoom)*0.2' },
    bottom: { x: '(iw-iw/zoom)*0.5', y: '(ih-ih/zoom)*0.8' },
    pan_left_to_right: {
      x: `(iw-iw/zoom)*(0.2 + 0.6*on/(${fps}*${duracion}))`,
      y: '(ih-ih/zoom)*0.5'
    },
    pan_right_to_left: {
      x: `(iw-iw/zoom)*(0.8 - 0.6*on/(${fps}*${duracion}))`,
      y: '(ih-ih/zoom)*0.5'
    },
    pan_top_to_bottom: {
      x: '(iw-iw/zoom)*0.5',
      y: `(ih-ih/zoom)*(0.2 + 0.6*on/(${fps}*${duracion}))`
    },
    pan_bottom_to_top: {
      x: '(iw-iw/zoom)*0.5',
      y: `(ih-ih/zoom)*(0.8 - 0.6*on/(${fps}*${duracion}))`
    },
    zoom_out: {
      x: '(iw-iw/zoom)*0.5',
      y: '(ih-ih/zoom)*0.5',
      zoomExpr: `max(1.15-0.001*on,1.0)`
    }
  };

  const config = KEN_BURNS[kb] || KEN_BURNS.center;

  if (config.zoomExpr) {
    return `zoompan=z='${config.zoomExpr}':x='${config.x}':y='${config.y}':d=1:s=1080x1920:fps=${fps},format=yuv420p`;
  }

  const zoomExpr = `min(zoom+${speed},${max})`;
  return `zoompan=z='${zoomExpr}':x='${config.x}':y='${config.y}':d=1:s=1080x1920:fps=${fps},format=yuv420p`;
}

async function generarSlide(foto, outputPath, params, texto1, texto2) {
  const fotoPath = join(DIR_IMGS, foto.archivo);
  if (!fs.existsSync(fotoPath)) {
    console.log(`   ❌ No existe foto: ${fotoPath}`);
    return false;
  }

  const zoom = construirZoompan(params);
  const estilo = params.estilo || 'fade';
  const sz1 = params.fontSize_titulo || 70;
  const sz2 = params.fontSize_subtitulo || 40;
  const overlay = params.overlay ? (OVERLAYS[params.overlay] || '') : '';
  const grade = params.colorGrade ? (COLOR_GRADES[params.colorGrade] || '') : '';

  const textoFilters = (ESTILOS[estilo] || ESTILOS.fade)(texto1, texto2, sz1, sz2);

  let vf = `${zoom}${overlay}${grade},${textoFilters}`;

  const cmd = `ffmpeg -loop 1 -i "${fotoPath}" -f lavfi -i anullsrc=r=44100:cl=stereo -t ${params.duracion || 4} -vf "${vf}" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "${outputPath}" -y 2>/dev/null`;

  return ejecutar(cmd, `Foto #${foto._numero_original}`);
}

async function unirConTransicion(v1, v2, transicion, durTrans, outPath) {
  const offset = 3;
  const cmd = `ffmpeg -i "${v1}" -i "${v2}" -filter_complex "[0:v][1:v]xfade=transition=${transicion}:duration=${durTrans}:offset=${offset}[v];[0:a][1:a]acrossfade=d=${durTrans}[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac "${outPath}" -y 2>/dev/null`;
  return ejecutar(cmd, `Transición: ${transicion}`);
}

async function ejecutarReceta(receta) {
  console.log(`\n╔════════════════════════════════════════════════════════════╗`);
  console.log(`║  🧪 EXPERIMENTO: ${receta.nombre.padEnd(40)}║`);
  console.log(`║  ID: ${receta.id.padEnd(52)}║`);
  console.log(`╚════════════════════════════════════════════════════════════╝`);

  asegurarDir(DIR_OUTPUT);

  const fotos = receta.fotos.map(n => buscarFoto(n)).filter(Boolean);
  if (fotos.length === 0) {
    console.log('❌ No se encontraron fotos');
    return null;
  }

  console.log(`\n📸 ${fotos.length} fotos: ${fotos.map(f => `#${f._numero_original}`).join(', ')}`);
  console.log(`🎬 Ken Burns: ${receta.params.kenBurns}`);
  console.log(`🎨 Estilo texto: ${receta.params.estilo}`);
  console.log(`📺 Overlay: ${receta.params.overlay || 'ninguno'}`);
  console.log(`🌈 Color grade: ${receta.params.colorGrade || 'ninguno'}`);
  console.log(`⏱  ${receta.params.duracion}s por foto\n`);

  const slides = [];
  const temps = [];

  for (const foto of fotos) {
    const tempPath = join(DIR_OUTPUT, `slide_${receta.id}_${foto._numero_original}.mp4`);
    temps.push(tempPath);

    const t1 = obtenerTexto(foto);
    const t2 = '@RANCHORAIZ.POSADA';

    const ok = await generarSlide(foto, tempPath, receta.params, t1, t2);
    if (ok && fs.existsSync(tempPath)) {
      slides.push(tempPath);
    }
  }

  if (slides.length < 1) {
    console.log('❌ No se generaron slides');
    return null;
  }

  if (slides.length === 1) {
    const outPath = join(DIR_OUTPUT, `${receta.id}_${Date.now()}.mp4`);
    fs.renameSync(slides[0], outPath);
    return medirResultado(outPath, receta);
  }

  console.log(`\n🔗 Uniendo ${slides.length} slides con transiciones...`);

  const transiciones = receta.params.transiciones || ['fade'];
  let actual = slides[0];

  for (let i = 1; i < slides.length; i++) {
    const trans = transiciones[(i - 1) % transiciones.length];
    const tempOut = join(DIR_OUTPUT, `merge_${receta.id}_${i}.mp4`);
    temps.push(tempOut);

    const result = await unirConTransicion(actual, slides[i], trans, 0.8, tempOut);
    if (!result.ok) {
      console.log(`⚠️  Error en merge, usando slide individual como base`);
      break;
    }

    if (i > 1 && actual !== slides[0]) {
      try { fs.unlinkSync(actual); } catch {}
    }
    actual = tempOut;
  }

  const outputPath = join(DIR_FINAL, `${receta.id}_${Date.now()}.mp4`);
  asegurarDir(DIR_FINAL);

  if (fs.existsSync(actual)) {
    fs.renameSync(actual, outputPath);
  }

  temps.forEach(t => {
    if (fs.existsSync(t)) try { fs.unlinkSync(t); } catch {}
  });

  return medirResultado(outputPath, receta);
}

function medirResultado(path, receta) {
  if (!fs.existsSync(path)) {
    console.log('   ❌ No se encontró el archivo de salida');
    return null;
  }

  const stats = fs.statSync(path);
  const tamanoMB = (stats.size / (1024 * 1024)).toFixed(2);

  console.log(`\n📊 RESULTADO: ${path}`);
  console.log(`   Tamaño: ${tamanoMB} MB`);

  return {
    path,
    tamano_mb: parseFloat(tamanoMB),
    receta_id: receta.id
  };
}

async function main() {
  const args = process.argv.slice(2);

  const catalogo = cargarCatalogo();

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║  EXPERIMENTO - Runner de Recetas de Video                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  USO:                                                      ║
║    node ranchocut/experimento.js --receta=ID               ║
║    node ranchocut/experimento.js --todas                   ║
║    node ranchocut/experimento.js --listar                  ║
║    node ranchocut/experimento.js --nueva                   ║
║    node ranchocut/experimento.js --diario                  ║
║    node ranchocut/experimento.js --estado=ID               ║
║    node ranchocut/experimento.js --aprobar=ID              ║
║    node ranchocut/experimento.js --receta=ID --telegram    ║
║    node ranchocut/experimento.js --todas --telegram        ║
║                                                            ║
║  ESTADOS de receta:                                        ║
║    candidato → probado → aprobado → estandar              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    `);
    return;
  }

  const enviarTelegram = args.includes('--telegram');

  for (const arg of args) {
    if (arg.startsWith('--receta=')) {
      const id = arg.replace('--receta=', '');
      const receta = catalogo.recetas.find(r => r.id === id);
      if (!receta) {
        console.log(`❌ Receta "${id}" no encontrada`);
        console.log(`   Usa --listar para ver todas`);
        return;
      }
      const resultado = await ejecutarReceta(receta);
      if (resultado) {
        receta.calidad.estado = 'probado';
        receta.calidad.tamano_mb = resultado.tamano_mb;
        receta.calidad.notas = (receta.calidad.notas || '') +
          ` | ${new Date().toISOString().slice(0, 10)}: ${resultado.tamano_mb}MB`;
        guardarCatalogo(catalogo);
        console.log(`\n✅ Receta "${id}" actualizada a estado: probado`);

        if (enviarTelegram && resultado.path) {
          console.log(`\n📤 Enviando a Telegram...`);
          const tg = await sendVideo(resultado.path, `🧪 ${receta.nombre}\n${receta.params.kenBurns} | ${receta.params.estilo} | ${receta.params.overlay || 'sin overlay'}\n${resultado.tamano_mb} MB`);
          if (tg.ok) {
            console.log(`   ✅ Video enviado a Telegram`);
          } else {
            console.log(`   ⚠️  Error Telegram: ${tg.error}`);
          }
        }
      }
    }

    else if (arg === '--todas') {
      const candidatas = catalogo.recetas.filter(r =>
        r.calidad.estado === 'candidato' || r.calidad.estado === 'probado'
      );
      if (candidatas.length === 0) {
        console.log('No hay recetas pendientes por probar');
        return;
      }
      console.log(`\n🧪 Ejecutando ${candidatas.length} recetas...`);
      for (const receta of candidatas) {
        const resultado = await ejecutarReceta(receta);
        if (resultado) {
          receta.calidad.estado = 'probado';
          receta.calidad.tamano_mb = resultado.tamano_mb;
          receta.calidad.notas = (receta.calidad.notas || '') +
            ` | ${new Date().toISOString().slice(0, 10)}: ${resultado.tamano_mb}MB`;
          guardarCatalogo(catalogo);
          console.log(`✅ "${receta.id}" → probado (${resultado.tamano_mb} MB)`);

          if (enviarTelegram && resultado.path) {
            console.log(`   📤 Enviando a Telegram...`);
            const tg = await sendVideo(resultado.path, `🧪 ${receta.nombre}\n${resultado.tamano_mb} MB`);
            if (tg.ok) {
              console.log(`   ✅ Video enviado`);
            } else {
              console.log(`   ⚠️  Error: ${tg.error}`);
            }
          }
        }
      }
    }

    else if (arg === '--listar') {
      const porEstado = {};
      for (const r of catalogo.recetas) {
        const est = r.calidad.estado || 'candidato';
        if (!porEstado[est]) porEstado[est] = [];
        porEstado[est].push(r);
      }
      console.log(`\n📋 Catálogo: ${catalogo.recetas.length} recetas\n`);
      for (const [estado, recetas] of Object.entries(porEstado)) {
        console.log(`  [${estado.toUpperCase()}]`);
        for (const r of recetas) {
          const stars = r.calidad.estrellas ? '⭐'.repeat(r.calidad.estrellas) : '   ';
          const mb = r.calidad.tamano_mb ? `${r.calidad.tamano_mb}MB` : '---';
          console.log(`    ${r.id.padEnd(32)} ${stars} ${mb.padEnd(8)} ${r.nombre}`);
        }
        console.log();
      }
    }

    else if (arg === '--diario') {
      if (fs.existsSync(DIARIO_PATH)) {
        const diario = fs.readFileSync(DIARIO_PATH, 'utf8');
        console.log(diario);
      } else {
        console.log('No hay diario aún');
      }
    }

    else if (arg.startsWith('--estado=')) {
      const id = arg.replace('--estado=', '').split(':');
      const recetaId = id[0];
      const nuevoEstado = id[1] || 'probado';
      const receta = catalogo.recetas.find(r => r.id === recetaId);
      if (!receta) {
        console.log(`❌ Receta "${recetaId}" no encontrada`);
        return;
      }
      receta.calidad.estado = nuevoEstado;
      guardarCatalogo(catalogo);
      console.log(`✅ "${recetaId}" → estado: ${nuevoEstado}`);
    }

    else if (arg.startsWith('--aprobar=')) {
      const id = arg.replace('--aprobar=', '');
      const receta = catalogo.recetas.find(r => r.id === id);
      if (!receta) {
        console.log(`❌ Receta "${id}" no encontrada`);
        return;
      }
      receta.calidad.estado = 'estandar';
      guardarCatalogo(catalogo);
      console.log(`\n🏆 "${receta.nombre}" PROMOVIDA A ESTÁNDAR!`);
      console.log(`   Esta receta ahora es parte del pipeline oficial`);
      await sendMessage(`🏆 NUEVO ESTÁNDAR: "${receta.nombre}"\n${receta.params.kenBurns} | ${receta.params.estilo}\nCalificación: ${'⭐'.repeat(receta.calidad.estrellas || 5)}`);
    }

    else if (arg === '--nueva') {
      console.log('\n🧪 Crear nueva receta');
      console.log('   Edita ranchocut/recetas/catalogo.json manualmente');
      console.log('   o usa el siguiente template:\n');
      console.log(JSON.stringify({
        id: 'mi-receta',
        fecha: new Date().toISOString().slice(0, 10),
        version: 1,
        nombre: 'Mi Receta',
        descripcion: 'Describe qué quieres probar',
        herramientas: ['ffmpeg'],
        params: {
          kenBurns: 'center',
          estilo: 'fade',
          overlay: null,
          colorGrade: null,
          duracion: 4,
          zoomSpeed: 0.0008,
          zoomMax: 1.12,
          transiciones: ['fade'],
          fontSize_titulo: 70,
          fontSize_subtitulo: 40,
          fps: 30
        },
        fotos: [6, 11, 19, 8],
        calidad: { estado: 'candidato', evaluacion: null, estrellas: null, tamano_mb: null, notas: 'Por probar' },
        tags: ['por-probar']
      }, null, 2));
    }
  }
}

main().catch(err => {
  console.error('\n❌ Error:', err.message);
  process.exit(1);
});
