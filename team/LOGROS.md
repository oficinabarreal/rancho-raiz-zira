# 🏔️ Rancho Raíz — Informe de Logros

> **Para:** Leo (dueño)
> **De:** Diego + Zira
> **Fecha:** 9 de junio 2026

---

## Resumen ejecutivo

En las últimas semanas transformamos Rancho Raíz de **cero presencia digital** a tener un **ecosistema completo de gestión y ventas online** — sin depender de programadores, sin costos mensuales, y con el equipo pudiendo manejar todo desde Google Sheets.

---

## ✅ Lo que ya está funcionando

### 🌐 Sitio Web Profesional
👉 [ranchoraiz.barreal.com](https://oficinabarreal.github.io/rancho-raiz-zira/)

El sitio tiene:
- **Fotos reales** del rancho (habitaciones, pileta, paisajes, interiores)
- **Precios actualizados** extraídos de los WhatsApp reales
- **Galería de imágenes** del lugar
- **Diseño profesional** con la mascota Zira (montaña animada)
- **Responsive** — se ve bien en celular y PC

### 🔐 Panel de Administración Secreto
👉 [Admin Panel](https://oficinabarreal.github.io/rancho-raiz-zira/admin/)

**Contraseña: rancho**

Cualquier persona del equipo puede entrar, ver los datos del sistema y administrar contenido.

### 📊 Google Sheets = El Corazón del Sistema
Todo el contenido del sitio se maneja desde un **Google Sheet compartido**. No hay que saber HTML, no hay que pedirle a un técnico. Si sabés editar una planilla de Excel, sabés actualizar el sitio.

**5 pestañas:**

| Pestaña | ¿Qué hace? |
|---------|-----------|
| `config` | Teléfono, dirección, whatsapp |
| `habitaciones` | Fotos, precios, promociones |
| `servicios` | Todo lo que ofrece el rancho |
| `galeria` | Fotos del lugar |
| `promociones` | Ofertas especiales |

### 🔄 Auto-Actualización
Cada cambio en el Sheet se refleja automáticamente en el sitio web en ~30 minutos. Sin intervención humana.

### 💬 WhatsApp Directo
Todos los botones de "Consultar" del sitio web apuntan al **WhatsApp de Ayelén** (+54 9 11 5959-5869). Cada visita interesada habla directo con administración.

### 📸 10 Fotos Reales en el Sitio
Descargadas del Instagram oficial de Rancho Raíz, sin stock photos, sin imágenes genéricas.

### 🔒 Seguridad
Los datos sensibles (contraseña de admin, URL del Sheet) no se exponen al público. El sitio es seguro.

---

## 📐 Arquitectura del Sistema

```
Google Sheet (el equipo edita)
       │
       ▼
GitHub Actions (procesa automático)
       │
       ▼
GitHub Pages (sitio web en vivo)
       │
       ▼
Visitantes → WhatsApp de Ayelón
```

**Costo operativo: $0 por mes.** Solo GitHub (gratuito) y el conocimiento de editar Google Sheets.

---

## 🤖 RanchoBot — Asistente WhatsApp Inteligente
👉 [Repo privado: oficinabarreal/rancho-bot](https://github.com/oficinabarreal/rancho-bot)

El RanchoBot es un asistente automático que vive en el WhatsApp del rancho y **responde consultas 24/7**:
- 💰 Precios de cabañas
- 📍 Ubicación y cómo llegar
- 🛎️ Servicios disponibles
- 📸 Galería de fotos
- 💬 Contacto directo con el equipo

**Estado:** El bot ya está programado, listo para activarse. Solo requiere vincular el número de WhatsApp del rancho una vez (se hace desde el mismo celu, 30 segundos).

**Próximas features posibles:** captura de leads, notificaciones al equipo, actualización del sitio vía WhatsApp.

## 🏆 Próximos pasos posibles

- [ ] **Subir más fotos** al Sheet para que aparezcan en la galería
- [ ] **Activar RanchoBot** y ponerlo a responder
- [ ] **Agregar más habitaciones** al Sheet cuando se construyan
- [ ] **Sistema de reservas** directo desde la web

---

## 🔗 Enlaces Rápidos

| Recurso | Link |
|---------|------|
| 🌐 Sitio Web | https://oficinabarreal.github.io/rancho-raiz-zira/ |
| 🔐 Admin Panel | https://oficinabarreal.github.io/rancho-raiz-zira/admin/ |
| 📊 Dashboard | https://oficinabarreal.github.io/rancho-raiz-zira/panel/ |
| 💬 WhatsApp | https://wa.me/5491159595869 |
| 📸 Instagram | https://instagram.com/ranchoraiz.barreal |

---

<div align="center">
  <sub>🏔️ <strong>Rancho Raíz</strong> · Barreal, San Juan · Argentina</sub>
  <br>
  <sub>Gestionado por Diego + Zira · Junio 2026</sub>
</div>
