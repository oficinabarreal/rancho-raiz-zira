"""Enviar por email el script del bot para Windows"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crm.connectors import GmailConnector

SCRIPT_CONTENT = """const { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const pino = require('pino');

const SESSION_DIR = './session';
const TELEFONO = process.argv[2] || '5492645017161';

async function iniciarBot() {
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();
  const sock = makeWASocket({
    version, auth: state, printQRInTerminal: false,
    logger: pino({ level: 'warn' }),
    browser: ['RanchoBot', 'Safari', '3.0'],
    syncFullHistory: false, markOnlineOnConnect: true, generateHighQualityLink: true,
  });
  sock.ev.on('creds.update', saveCreds);
  sock.ev.on('connection.update', ({ connection, lastDisconnect }) => {
    if (connection === 'open') {
      console.log('\\n✅ RanchoBot conectado!');
      console.log('📢 Ahora cerrá esto y copiá la carpeta session/ a Termux.\\n');
      process.exit(0);
    }
    if (connection === 'close') {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      if (reason === DisconnectReason.loggedOut) {
        console.log('❌ Sesión cerrada remotamente.');
        fs.rmSync(SESSION_DIR, { recursive: true, force: true });
        process.exit(1);
      }
      console.log('\\n⚠️ Cerrada (' + (reason || '?') + '). Reconectando...');
      setTimeout(() => iniciarBot(), 5000);
    }
  });
  // Código de 8 dígitos
  if (!sock.authState?.creds?.registered) {
    console.log('\\n⏳ Generando código...\\n');
    setTimeout(async () => {
      try {
        const codigo = await sock.requestPairingCode(TELEFONO);
        const f = codigo.match(/.{1,4}/g).join(' ');
        console.log('========================================');
        console.log('  🔢 CÓDIGO: ' + f);
        console.log('========================================');
        console.log('\\n📱 WhatsApp Business → 3 puntitos');
        console.log('   → Dispositivos vinculados');
        console.log('   → Vincular un dispositivo');
        console.log('   → "Vincular con número de teléfono"');
        console.log('   → Ingresá: ' + f + '\\n');
      } catch(e) {
        console.log('❌ Error: ' + e.message);
      }
    }, 3000);
  }
}
console.log('==============================');
console.log('  🏔️  RanchoBot - Vinculación');
console.log('  Número: ' + TELEFONO);
console.log('==============================\\n');
iniciarBot().catch(e => { console.error('❌', e); process.exit(1); });
"""

def main():
    body = f"""\
Meto este script en la PC y lo corre así:

📥 Instrucciones:

1. Instalá Node.js desde https://nodejs.org (versión LTS, next next next)
2. Abrí PowerShell o CMD y ejecutá:

   mkdir C:\\rancho-bot
   cd C:\\rancho-bot
   npm init -y
   npm install @whiskeysockets/baileys @hapi/boom pino

3. CREÁ el archivo C:\\rancho-bot\\index.js y pegá este código (abajo)
4. Ejecutá:   node index.js
5. Te va a mostrar un código de 8 dígitos — ponelo en WhatsApp Business
6. Cuando diga "RanchoBot conectado!", buscá la carpeta C:\\rancho-bot\\session\\
7. Mandame esa carpeta (comprimida en ZIP o por Drive) y yo la pongo en Termux

══════════════════════════════════════════
CÓDIGO DEL BOT (guardar como index.js):
══════════════════════════════════════════

{SCRIPT_CONTENT}

══════════════════════════════════════════
"""

    gmail = GmailConnector()
    r = gmail.send_message(
        "oficinabarreal@gmail.com",
        "🏔️ RanchoBot - Script para vincular desde Windows",
        body
    )
    if r.ok:
        print("✅ Email enviado a oficinabarreal@gmail.com")
    else:
        print(f"❌ Error al enviar: {r.error}")
        # Fallback: escribir local
        out = Path("/data/data/com.termux/files/home/script_bot_windows.js")
        out.write_text(SCRIPT_CONTENT)
        print(f"✅ Guardado local en {out}")

if __name__ == "__main__":
    main()
