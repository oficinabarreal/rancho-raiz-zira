#!/usr/bin/env node
// Convierte SVG animado en frames PNG
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SVG_PATH = process.argv[2];
const OUTPUT_DIR = process.argv[3] || '/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/assets/zira/posts';
const NAME = path.basename(SVG_PATH, '.svg');

async function main() {
  if (!SVG_PATH) {
    console.error('Uso: node capture-svg-frames.js <ruta.svg>');
    process.exit(1);
  }

  const svgContent = fs.readFileSync(SVG_PATH, 'utf-8');
  const html = `<!DOCTYPE html><html><body style="margin:0;background:#000">${svgContent}</body></html>`;

  const tmpDir = '/data/data/com.termux/files/home/.cache/hermes/tmp';
  fs.mkdirSync(tmpDir, { recursive: true });
  const tmpHtml = `${tmpDir}/${NAME}.html`;
  fs.writeFileSync(tmpHtml, html);

  const browser = await puppeteer.launch({
    executablePath: '/data/data/com.termux/files/usr/bin/chromium-browser',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 400, height: 400 });
  await page.goto('file://' + tmpHtml, { waitUntil: 'networkidle0' });
  
  // Wait a moment for CSS animations to initialize
  await new Promise(r => setTimeout(r, 500));

  // Capture 10 frames over 4 seconds (covers blink cycle + wave cycle)
  const totalFrames = 10;
  const frameDir = `${OUTPUT_DIR}/frames_${NAME}`;
  fs.mkdirSync(frameDir, { recursive: true });

  for (let i = 0; i < totalFrames; i++) {
    await new Promise(r => setTimeout(r, 400)); // 400ms between frames
    const framePath = `${frameDir}/frame_${String(i).padStart(3,'0')}.png`;
    await page.screenshot({ path: framePath, clip: { x: 0, y: 0, width: 400, height: 400 } });
    process.stdout.write('.');
  }

  // Also capture 2 extra for end-of-cycle
  await new Promise(r => setTimeout(r, 600));
  const framePath = `${frameDir}/frame_${String(totalFrames).padStart(3,'0')}.png`;
  await page.screenshot({ path: framePath, clip: { x: 0, y: 0, width: 400, height: 400 } });
  process.stdout.write('.');

  await browser.close();
  console.log(`\n✅ ${totalFrames+1} frames capturados en ${frameDir}/`);
}

main().catch(e => { console.error('❌', e.message); process.exit(1); });
