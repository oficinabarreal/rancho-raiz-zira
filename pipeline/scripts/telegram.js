#!/usr/bin/env node

import fs from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, '..');

const TOKEN = '8580346196:AAEz00B63NEsB2hIUXaAEQnZTSI9ECS2qnE';
const CHAT_ID = '8272684219';
const API_BASE = `https://api.telegram.org/bot${TOKEN}`;

export async function sendVideo(videoPath, caption = '') {
  if (!fs.existsSync(videoPath)) {
    return { ok: false, error: `Archivo no existe: ${videoPath}` };
  }

  const stats = fs.statSync(videoPath);
  const maxSize = 50 * 1024 * 1024;
  if (stats.size > maxSize) {
    return { ok: false, error: `Video demasiado grande: ${(stats.size / 1024 / 1024).toFixed(1)} MB (max 50 MB)` };
  }

  const url = `${API_BASE}/sendVideo`;

  try {
    const formData = new FormData();
    const blob = new Blob([fs.readFileSync(videoPath)], { type: 'video/mp4' });
    formData.append('video', blob, 'video.mp4');
    formData.append('chat_id', CHAT_ID);
    if (caption) formData.append('caption', caption);

    const resp = await fetch(url, { method: 'POST', body: formData });
    const data = await resp.json();

    if (data.ok) {
      return { ok: true, message_id: data.result?.message_id };
    } else {
      return { ok: false, error: data.description || 'Error desconocido' };
    }
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

export async function sendMessage(text) {
  const url = `${API_BASE}/sendMessage`;
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: CHAT_ID, text })
    });
    return await resp.json();
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║  TELEGRAM - Envío de videos                                ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  USO:                                                      ║
║    node ranchocut/telegram.js --video=RUTA                 ║
║    node ranchocut/telegram.js --video=RUTA --caption=TEXTO ║
║    node ranchocut/telegram.js --mensaje=TEXTO              ║
║    node ranchocut/telegram.js --test                       ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    `);
    return;
  }

  for (const arg of args) {
    if (arg.startsWith('--video=')) {
      const path = arg.replace('--video=', '');
      let caption = '';
      for (const a of args) {
        if (a.startsWith('--caption=')) caption = a.replace('--caption=', '');
      }
      console.log(`📤 Enviando video: ${path}...`);
      const result = await sendVideo(path, caption);
      if (result.ok) {
        console.log(`   ✅ Enviado (message_id: ${result.message_id})`);
      } else {
        console.log(`   ❌ ${result.error}`);
      }
    }

    if (arg.startsWith('--mensaje=')) {
      const text = arg.replace('--mensaje=', '');
      console.log(`📤 Enviando mensaje...`);
      const result = await sendMessage(text);
      console.log(result.ok ? '   ✅ Enviado' : `   ❌ ${result.description || result.error}`);
    }

    if (arg === '--test') {
      console.log('🧪 Test de conexión Telegram...');
      const result = await sendMessage('🧪 Test de conexión desde ranchocut');
      if (result.ok) {
        console.log('   ✅ Conexión OK');
      } else {
        console.log(`   ❌ ${result.description || result.error}`);
      }
    }
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch(err => console.error('❌ Error:', err.message));
}
