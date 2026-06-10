/**
 * Zira Chat - Backend Webhook
 * ============================
 * 
 * Este script se deploya como Web App de Google Apps Script.
 * 
 * Cómo deployar (2 minutos):
 * 1. Ir a https://script.google.com/create
 * 2. Pegar todo este código
 * 3. Guardar (Ctrl+S) → poner nombre "Zira Chat"
 * 4. Deployar → "Implementar como aplicación web"
 *    - Ejecutar como: "Yo" (tu cuenta)
 *    - Quién tiene acceso: "Cualquier usuario"
 * 5. Copiar la URL que aparece
 * 6. Pegar esa URL en zira-huespedes.html donde dice WEBAPP_URL
 */

// ============================================================
// CONFIGURACIÓN
// ============================================================
const SHEET_ID = '1MK76i7CTM44yCJu32SIq1fdOU5uVMBG5HXWWpoKfklg';
const MENSAJES_TAB = 'mensajes';
const CONVERSACIONES_TAB = 'conversaciones';

// ============================================================
// API endpoints
// ============================================================

// GET ?action=mensajes&session_id=xxx → devuelve los mensajes de una sesión
// GET ?action=nuevos&session_id=xxx → devuelve solo los mensajes NO respondidos
function doGet(e) {
  const action = e.parameter.action || 'mensajes';
  const sessionId = e.parameter.session_id || '';
  
  if (!sessionId) {
    return respond({ error: 'session_id requerido' }, 400);
  }
  
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = ss.getSheetByName(MENSAJES_TAB);
  const data = sheet.getDataRange().getValues();
  
  // Fila 0 = headers
  const messages = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[1] == sessionId) {
      messages.push({
        id: row[0],
        timestamp: row[2],
        remitente: row[3],
        mensaje: row[4],
        respondido: row[5] === 'SI'
      });
    }
  }
  
  if (action === 'nuevos') {
    // Solo los no respondidos (del guest)
    const nuevos = messages.filter(m => m.remitente === 'guest' && !m.respondido);
    return respond({ ok: true, nuevos: nuevos.length, messages: nuevos });
  }
  
  return respond({ ok: true, messages: messages });
}

// POST → recibe un nuevo mensaje del huésped
// Body JSON: { session_id, nombre, mensaje }
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const sessionId = body.session_id || generarId();
    const nombre = body.nombre || 'Huésped';
    const mensaje = body.mensaje || '';
    
    if (!mensaje.trim()) {
      return respond({ error: 'mensaje vacío' }, 400);
    }
    
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const now = new Date();
    const timestamp = Utilities.formatDate(now, 'GMT-3', 'yyyy-MM-dd HH:mm:ss');
    
    // Guardar mensaje
    const msgsSheet = ss.getSheetByName(MENSAJES_TAB);
    const nextId = msgsSheet.getLastRow(); // simple ID
    msgsSheet.appendRow([nextId, sessionId, timestamp, 'guest', mensaje.trim(), 'NO', '']);
    
    // Actualizar conversación
    const convSheet = ss.getSheetByName(CONVERSACIONES_TAB);
    const convData = convSheet.getDataRange().getValues();
    let found = false;
    for (let i = 1; i < convData.length; i++) {
      if (convData[i][0] == sessionId) {
        convSheet.getRange(i + 1, 4).setValue(mensaje.trim().substring(0, 80));
        convSheet.getRange(i + 1, 5).setValue(timestamp);
        found = true;
        break;
      }
    }
    if (!found) {
      convSheet.appendRow([sessionId, nombre, timestamp, mensaje.trim().substring(0, 80), timestamp]);
    }
    
    return respond({ ok: true, session_id: sessionId, id: nextId });
    
  } catch (err) {
    return respond({ error: err.toString() }, 500);
  }
}

// ============================================================
// Helpers
// ============================================================
function generarId() {
  return 'sess_' + Utilities.getUuid().substring(0, 8);
}

function respond(data, statusCode) {
  const output = ContentService.createTextOutput();
  output.setMimeType(ContentService.MimeType.JSON);
  output.setContent(JSON.stringify(data));
  if (statusCode) {
    // Google Apps Script no soporta status codes diferentes fácilmente
    // Lo manejamos desde el frontend
  }
  return output;
}
