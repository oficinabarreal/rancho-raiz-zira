# Hoja de Ruta — CRM Rancho Raíz

## 🟢 Completado
- [x] Conectores: Gmail, Calendar, Drive, Sheets, Kommo, Telegram, Instagram
- [x] Token OAuth con gmail.modify + drive.file + calendar + spreadsheets
- [x] 8 reservas extraídas de chats WhatsApp
- [x] Planilla `Reservas_Rancho_Raiz` en Sheets
- [x] Simulación de 6 escenarios (reserva, check-in, incidencia, check-out, resumen diario, aprobación)
- [x] Workflow unificado: Gmail → Kommo → Calendar → Sheets → Telegram
- [x] Perfiles del equipo (Leo, Ayelen, Diego, Chiqui)
- [x] Perfiles de 8 huéspedes registrados
- [x] Telegram listener (recibir y procesar reservas por chat)
- [x] Informe diario generador (vía Telegram + Email)

## 🟡 En progreso / Pendiente

### Infraestructura
- [ ] Resolver WhatsApp token (renovar en Meta Developers)
- [ ] Guardar credenciales en CREDENCIALES.md

### Flujo CRM
- [ ] Inventario real (convertir .xlsx a Sheets o cargarlo)
- [ ] Workflow real con Gmail (sin demo)
- [ ] Listener automático cada N minutos (cron/loop permanente)
- [ ] Historial de huéspedes con preferencias (alergias, deportes, etc.)
- [ ] Competencia: alertas cuando bajen precios (Telegram)

### IA / Automatización
- [ ] Integrar Zen model para parsear mails de reserva (más preciso que regex)
- [ ] Análisis de sentimiento de comentarios de huéspedes
- [ ] Recomendaciones de precios basadas en competencia y ocupación
- [ ] Generación automática de contenido Instagram con IA

### Contenido
- [ ] Laboratorio de creación de contenido Instagram
- [ ] Programación de posts
- [ ] Análisis de engagement

### Reportes
- [ ] Informe diario automático (email a Leo + Telegram grupo)
- [ ] Dashboard semanal: ocupación, ingresos, redes
- [ ] Alertas de mantenimiento (heladera, piletas, etc.)

### Futuro
- [ ] Migrar a servidor (Cloudflare Workers + cron)
- [ ] Webhook WhatsApp
- [ ] App mobile para huéspedes
