#!/usr/bin/env node
// Captura frames de SVG con fondo chromakey verde para transparencia
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SVGS = [
  'zira-transparente-juguetona',
  'zira-transparente-zen',
  'zira-transparente-magica',
  'zira-transparente-viva',
  'zira-transparente-clasica',
];

const SVG_DIR = '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/assets/zira';
const OUTPUT_DIR = '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/pipeline/.temp';

async function captureFrames(svgName, page) {
  const svgPath = `${SVG_DIR}/${svgName}.svg`;
  const svgContent = fs.readFileSync(svgPath, 'utf-8');
  
  // Crear HTML con fondo chromakey verde
  const html = `<!DOCTYPE html>
<html>
<head><style>
  body { margin: 0; background: #00ff00; display: flex; align-items: center; justify-content: center; width: 400px; height: 400px; }
  svg { display: block; }
</style></head>
<body>${svgContent}</body>
</html>`;

  const tmpHtml = `/data/data/com.termux/files/home/.cache/hermes/tmp/${svgName}.html`;
  fs.mkdirSync(path.dirname(tmpHtml), { recursive: true });
  fs.writeFileSync(tmpHtml, html);

  // Navigate and wait for render
  await page.goto('file://' + tmpHtml, { waitUntil: 'networkidle0', timeout: 15000 });
  await new Promise(r => setTimeout(r, 1000)); // Let CSS animations initialize

  // Capture frames: 12fps, 5 seconds = 60 frames
  // Wait a bit to start at a good animation cycle point, then capture every ~83ms
  const fps = 12;
  const duration = 5; // seconds
  const totalFrames = fps * duration;
  const frameDelay = 1000 / fps; // ms between frames
  
  const frameDir = `${OUTPUT_DIR}/frames_${svgName}`;
  fs.mkdirSync(frameDir, { recursive: true });

  // Initial wait for animation to settle
  await new Promise(r => setTimeout(r, 200));

  process.stdout.write(`  ${svgName}: capturing ${totalFrames} frames...`);
  for (let i = 0; i < totalFrames; i++) {
    const startTime = Date.now();
    const framePath = `${frameDir}/frame_${String(i).padStart(4, '0')}.png`;
    await page.screenshot({
      path: framePath,
      clip: { x: 0, y: 0, width: 400, height: 400 },
      omitBackground: false // we WANT the green background for chromakey
    });
    // Maintain timing
    const elapsed = Date.now() - startTime;
    if (elapsed < frameDelay) {
      await new Promise(r => setTimeout(r, frameDelay - elapsed));
    }
    if (i % 20 === 19) process.stdout.write('.');
  }
  console.log(` done (${totalFrames})`);
  return frameDir;
}

async function main() {
  console.log('\n🎬 Capturando Ziras transparentes con chromakey...\n');

  const browser = await puppeteer.launch({
    executablePath: '/data/data/com.termux/files/usr/bin/chromium-browser',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 400, height: 400 });

  // Disable timeout for the whole process
  page.setDefaultTimeout(30000);

  for (const svgName of SVGS) {
    const svgPath = `${SVG_DIR}/${svgName}.svg`;
    if (!fs.existsSync(svgPath)) {
      console.log(`  ⚠️  ${svgName}.svg no encontrado, saltando`);
      continue;
    }
    await captureFrames(svgName, page);
  }

  await browser.close();
  console.log('\n✅ Captura completada!\n');
}

main().catch(e => { console.error('❌', e.message); process.exit(1); });
