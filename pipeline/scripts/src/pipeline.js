import puppeteer from 'puppeteer';
import fs from 'fs';
import { exec } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TEMPLATES = {
  climaDiario: {
    name: 'Clima Diario',
    duration: 8,
    colorGrading: 'eq=saturation=1.1:contrast=1.05:brightness=0.02',
    filterComplex: (datos) => `[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,${TEMPLATES._colorGrading || 'eq=saturation=1.1:contrast=1.05',
    texts: (datos) => [
      {
        text: 'EL CLIMA EN RANCHO RAÍZ',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 70,
        x: '(w-tw)/2',
        y: '150',
        start: 0,
        end: datos.duration,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: datos.temperatura || '26°C',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 180,
        x: '(w-tw)/2',
        y: '(h-th)/2-100',
        start: 1.5,
        end: datos.duration,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: datos.estado || 'Despejado',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 50,
        x: '(w-tw)/2',
        y: '(h-th)/2+80',
        start: 2.0,
        end: datos.duration,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: datos.consejo || '',
        font: 'Roboto-Light.ttf',
        color: '0xEAE4D3',
        size: 40,
        x: '(w-tw)/2',
        y: '(h-th)/2+180',
        start: 2.5,
        end: datos.duration,
        fadeIn: 1.0,
        fadeOut: 0
      }
    ]
  },

  ranchoRaizClassic: {
    name: 'Rancho Raiz Classic',
    duration: 10,
    colorGrading: 'eq=saturation=1.15:contrast=1.05',
    texts: (datos) => [
      {
        text: 'RANCHO RAÍZ',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 100,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        start: 1.5,
        end: 3.5,
        fadeIn: 1.5,
        fadeOut: 1.0
      },
      {
        text: 'CONEXIÓN ANDINA',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        start: 0.8,
        end: 3.5,
        fadeIn: 1.2,
        fadeOut: 1.0
      },
      {
        text: 'TU REFUGIO',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 100,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        start: 3.5,
        end: 7.0,
        fadeIn: 1.0,
        fadeOut: 1.0
      },
      {
        text: 'ENTRE MONTAÑAS',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        start: 4.0,
        end: 7.0,
        fadeIn: 1.0,
        fadeOut: 1.0
      },
      {
        text: 'RESERVA HOY',
        font: 'Roboto-Bold.ttf',
        color: '0xEAE4D3',
        size: 90,
        x: '(w-tw)/2',
        y: '(h-th)/2-70',
        start: 7.0,
        end: 10.0,
        fadeIn: 1.0,
        fadeOut: 0
      },
      {
        text: datos.instagram || '@ranchoraiz.posada',
        font: 'Roboto-Regular.ttf',
        color: '0xC5A059',
        size: 38,
        x: '(w-tw)/2',
        y: '(h-th)/2+60',
        start: 7.5,
        end: 10.0,
        fadeIn: 1.0,
        fadeOut: 0
      }
    ]
  },

  minimal: {
    name: 'Minimal',
    duration: 6,
    colorGrading: 'eq=saturation=1.05:contrast=1.02',
    texts: (datos) => [
      {
        text: datos.instagram || '@ranchoraiz.posada',
        font: 'Roboto-Medium.ttf',
        color: '0xffffff',
        size: 42,
        x: '(w-tw)/2',
        y: 'h-th-120',
        start: 1.0,
        end: 6.0,
        fadeIn: 0.8,
        fadeOut: 0
      }
    ]
  }
};

function buildDrawText(textObj) {
  const { text, font, color, size, x, y, start, end, fadeIn, fadeOut } = textObj;
  
  if (!text || text.trim() === '') return '';
  
  let alphaExpr = '1';
  
  if (fadeIn > 0 || fadeOut > 0) {
    const parts = [];
    
    if (fadeIn > 0) {
      const fadeStart = start;
      const fadeEnd = start + fadeIn;
      parts.push(`if(lt(t,${fadeStart}),0,if(lt(t,${fadeEnd}),(t-${fadeStart})/${fadeIn}`);
    } else {
      parts.push(`if(lt(t,${start}),0`);
    }
    
    if (fadeOut > 0) {
      const fadeStart = end - fadeOut;
      parts.push(`,if(gt(t,${fadeStart}),1-(t-${fadeStart})/${fadeOut},1)`);
    } else {
      parts.push(`,if(gt(t,${end}),0,1))`);
    }
    
    alphaExpr = parts.join('');
  }
  
  return `drawtext=fontfile=/system/fonts/${font}:text='${text}':fontcolor=${color}:fontsize=${size}:x='${x}':y='${y}':alpha='${alphaExpr}'`;
}

const CHROMIUM_PATHS = [
  '/data/data/com.termux/files/usr/bin/chromium',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/system/bin/chromium'
];

function findChromium() {
  for (const path of CHROMIUM_PATHS) {
    try {
      if (require('fs').existsSync(path)) {
        return path;
      }
    } catch (e) {}
  }
  return null;
}

export async function renderVideoBase(datosConfig) {
  console.log('\n🎬 Paso 1: Renderizando animación 3D en segundo plano...');
  
  const chromiumPath = findChromium();
  console.log(`   📍 Chromium detectado: ${chromiumPath || 'No encontrado'}`);
  
  const launchOptions = { 
    headless: true, 
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] 
  };
  
  if (chromiumPath) {
    launchOptions.executablePath = chromiumPath;
  }
  
  const browser = await puppeteer.launch(launchOptions);
  
  const page = await browser.newPage();
  
  await page.setViewport({ 
    width: 1080, 
    height: 1920,
    deviceScaleFactor: 1
  });
  
  let videoBuffer = null;
  
  await page.exposeFunction('onRecordingComplete', (bufferArray) => {
    videoBuffer = Buffer.from(bufferArray);
    console.log('✅ Animación 3D completada');
  });
  
  const templatePath = join(__dirname, 'template3d.html');
  const htmlContent = fs.readFileSync(templatePath, 'utf8');
  
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  
  await page.evaluate((config) => {
    return new Promise((resolve) => {
      window.setConfig(config);
      window.startRender(config);
      
      const checkComplete = setInterval(() => {
        if (window._renderComplete) {
          clearInterval(checkComplete);
          resolve();
        }
      }, 500);
      
      setTimeout(() => {
        clearInterval(checkComplete);
        resolve();
      }, (config.duration + 3) * 1000);
    });
  }, {
    duration: datosConfig.duration || 8,
    clipType: datosConfig.clipType || 'particles',
    textoPrincipal: datosConfig.textoPrincipal || 'RANCHO'
  });
  
  await page.waitForFunction(() => window._renderComplete || true, { 
    timeout: (datosConfig.duration + 5) * 1000 
  });
  
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  await browser.close();
  
  if (videoBuffer) {
    const outputPath = join(process.cwd(), 'temp_base.webm');
    fs.writeFileSync(outputPath, videoBuffer);
    console.log(`💾 Video base guardado: ${outputPath}`);
    return outputPath;
  }
  
  throw new Error('No se pudo renderizar el video 3D');
}

export function ejecutarFfmpegPipeline(datosConfig, inputVideo) {
  return new Promise((resolve, reject) => {
    console.log('\n🎨 Paso 2: Aplicando overlays gráficos con FFmpeg...');
    
    const templateName = datosConfig.template || 'climaDiario';
    const template = TEMPLATES[templateName] || TEMPLATES.climaDiario;
    
    const texts = template.texts(datosConfig);
    const drawTextFilters = texts.map(buildDrawText).filter(t => t).join(',');
    
    const filterComplex = `[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,${template.colorGrading}${drawTextFilters ? ',' + drawTextFilters : ''}[video]`;
    
    const outputPath = datosConfig.output || '/sdcard/Download/ranchocut-final.mp4';
    
    const comando = [
      'ffmpeg',
      `-i "${inputVideo}"`,
      '-f lavfi -i anullsrc=r=44100:cl=stereo',
      `-filter_complex "${filterComplex}"`,
      '-map "[video]"',
      '-map 1:a',
      `-t ${datosConfig.duration || template.duration}`,
      '-c:v libx264',
      '-pix_fmt yuv420p',
      '-c:a aac',
      '-b:a 192k',
      `-shortest`,
      `"${outputPath}"`,
      '-y'
    ].join(' ');
    
    console.log(`\n📋 Comando FFmpeg:`);
    console.log(comando);
    console.log('');
    
    exec(comando, (error, stdout, stderr) => {
      if (error) {
        console.error(`❌ Fallo en FFmpeg: ${error.message}`);
        console.error(stderr);
        reject(error);
        return;
      }
      
      try {
        fs.unlinkSync(inputVideo);
      } catch (e) {}
      
      console.log(`\n✅ ¡Video publicitario terminado!`);
      console.log(`📍 Guardado en: ${outputPath}`);
      resolve(outputPath);
    });
  });
}

export async function renderCompleto(datosConfig) {
  try {
    console.log('\n═══════════════════════════════════════');
    console.log('🚀 RANCHOCUT LABORATORY');
    console.log('═══════════════════════════════════════');
    
    const videoBase = await renderVideoBase(datosConfig);
    const videoFinal = await ejecutarFfmpegPipeline(datosConfig, videoBase);
    
    console.log('\n═══════════════════════════════════════');
    console.log('✅ PROCESO COMPLETADO CON ÉXITO!');
    console.log('═══════════════════════════════════════\n');
    
    return videoFinal;
    
  } catch (error) {
    console.error('\n❌ Error en el pipeline:', error.message);
    throw error;
  }
}
