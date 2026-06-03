#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import { join } from 'path';

const AUDIO_DIR = '/data/data/com.termux/files/home/ranchoraiz_reels/audio';
const BASE_URL = 'https://audionautix.com/Music';

const TRACKS = [
  { file: 'AcousticGuitar1.mp3', name: 'Acoustic Guitar #1', mood: 'Calming, Relaxing', dur: '2:54' },
  { file: 'AcousticShuffle.mp3', name: 'Acoustic Shuffle', mood: 'Grooving, Bright', dur: '2:42' },
  { file: 'AutumnSunset.mp3', name: 'Autumn Sunset', mood: 'Calming, Relaxing', dur: '3:04' },
  { file: 'GreenLeaves.mp3', name: 'Green Leaves', mood: 'Calming, Uplifting', dur: '2:44' },
  { file: 'HappyStrummin.mp3', name: "Happy Strummin'", mood: 'Bright, Uplifting', dur: '2:46' },
  { file: 'LandrasDream.mp3', name: "Landra's Dream", mood: 'Bright, Uplifting', dur: '2:47' },
  { file: 'OneFineDay.mp3', name: 'One Fine Day', mood: 'Calming, Soothing', dur: '2:48' },
  { file: 'OpenRoad.mp3', name: 'Open Road', mood: 'Driving, Uplifting', dur: '2:26' },
  { file: 'PaperWings.mp3', name: 'Paper Wings', mood: 'Calming, Bright', dur: '3:16' },
  { file: 'RedwoodTrail.mp3', name: 'Redwood Trail', mood: 'Soothing, Bright', dur: '2:48' },
  { file: 'RiverMeditation.mp3', name: 'River Meditation', mood: 'Relaxing, Uplifting', dur: '2:46' },
  { file: 'RunningWatersFullTrack.mp3', name: 'Running Waters (full)', mood: 'Calming, Bright', dur: '4:08' },
  { file: 'Serenity.mp3', name: 'Serenity', mood: 'Calming, Relaxing', dur: '2:47' }
];

async function downloadTrack(track) {
  const dest = join(AUDIO_DIR, track.file);
  if (fs.existsSync(dest)) {
    return { ok: true, track, cached: true };
  }

  const url = `${BASE_URL}/${track.file}`;
  process.stdout.write(`   ${track.name.padEnd(28)} `);
  try {
    execSync(`curl -sL -o "${dest}" "${url}" --max-time 15`, { stdio: 'pipe' });
    const size = fs.statSync(dest).size;
    if (size > 10000) {
      const mb = (size / 1024 / 1024).toFixed(2);
      process.stdout.write(`✅ ${mb} MB\n`);
      return { ok: true, track, size, mb };
    } else {
      fs.unlinkSync(dest);
      process.stdout.write(`❌ muy pequeño (${size} bytes)\n`);
      return { ok: false, track, error: 'too small' };
    }
  } catch (err) {
    process.stdout.write(`❌ ${err.message.slice(0, 30)}\n`);
    return { ok: false, track, error: err.message };
  }
}

async function main() {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`  🎵 Descargando música libre de derechos desde audionautix.com`);
  console.log(`  ${'='.repeat(60)}\n`);

  const args = process.argv.slice(2);
  let tracksToDownload = TRACKS;

  if (args.includes('--all')) {
    // download all
  } else if (args.length > 0) {
    // filter by name
    const filters = args.filter(a => !a.startsWith('--'));
    tracksToDownload = TRACKS.filter(t =>
      filters.some(f => t.file.toLowerCase().includes(f.toLowerCase()))
    );
  } else {
    // default: download selected subset
    tracksToDownload = TRACKS.filter(t =>
      ['AutumnSunset', 'GreenLeaves', 'OpenRoad', 'RiverMeditation',
       'RedwoodTrail', 'OneFineDay', 'AcousticGuitar1', 'PaperWings', 'RunningWatersFullTrack'].includes(
        t.file.replace('.mp3', '')
      )
    );
  }

  if (tracksToDownload.length === 0) {
    console.log('  No se encontraron tracks para descargar.');
    console.log(`  Usa: node ranchocut/descargar-audio.js [nombre parcial]`);
    console.log(`  Ej:  node ranchocut/descargar-audio.js Acoustic Autumn\n`);
    console.log('  Tracks disponibles:');
    TRACKS.forEach(t => console.log(`    ${t.file.padEnd(35)} ${t.name.padEnd(22)} ${t.mood}`));
    return;
  }

  fs.mkdirSync(AUDIO_DIR, { recursive: true });

  let ok = 0, fail = 0;
  for (const track of tracksToDownload) {
    const result = await downloadTrack(track);
    if (result.ok) ok++; else fail++;
  }

  console.log(`\n  📊 ${ok} descargados, ${fail} fallidos\n`);

  if (ok > 0) {
    console.log('  📁 Audios en:', AUDIO_DIR);
    console.log('  Todos bajo licencia Creative Commons Attribution 4.0');
    console.log('  (crédito: Jason Shaw @ audionautix.com)\n');
  }
}

main().catch(err => console.error('Error:', err.message));
