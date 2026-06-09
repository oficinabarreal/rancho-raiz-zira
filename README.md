<div align="center">
  <img src="assets/zira/zira-greeting-leo.svg" width="180" alt="Zira">
  <h1>🏔️ Rancho Raíz · Zira CRM</h1>
  <p><strong>Sistema de gestión inteligente para posada rural</strong></p>
  <p>
    <a href="https://oficinabarreal.github.io/rancho-raiz-zira/">
      <img src="https://img.shields.io/badge/🌐%20Sitio%20Web-online-10b981?style=for-the-badge" alt="Sitio Web">
    </a>
    <a href="https://oficinabarreal.github.io/rancho-raiz-zira/admin/">
      <img src="https://img.shields.io/badge/🔐%20Admin%20Panel-online-6366f1?style=for-the-badge" alt="Admin Panel">
    </a>
    <a href="https://wa.me/5491159595869">
      <img src="https://img.shields.io/badge/💬%20WhatsApp-Ayelén-25D366?style=for-the-badge&logo=whatsapp" alt="WhatsApp">
    </a>
  </p>
  <p>
    <img src="https://img.shields.io/github/last-commit/oficinabarreal/rancho-raiz-zira?label=última%20actualización&style=flat-square">
    <img src="https://img.shields.io/github/repo-size/oficinabarreal/rancho-raiz-zira?style=flat-square">
    <img src="https://img.shields.io/github/actions/workflow/status/oficinabarreal/rancho-raiz-zira/cms-web.yml?branch=main&label=CMS%20Auto-Update&style=flat-square">
  </p>
</div>

---

## 🌟 ¿Qué es esto?

**Zira CRM** es el sistema que automatiza la gestión de **Rancho Raíz** (Barreal, San Juan). No es un sitio web común — es un ecosistema completo que:

- ✅ **Muestra el sitio web** con fotos reales, precios actualizados y servicios
- ✅ **Deja que el equipo administre** todo desde Google Sheets (sin programar)
- ✅ **Recibe consultas** por WhatsApp y las organiza
- ✅ **Se actualiza solo** cada vez que alguien cambia algo en el Sheet

> 💡 Si sabés usar Google Sheets, ya sabés usar el sistema.

---

## 🎯 Para el equipo (Leo, Ayelén, Diego)

### 🌐 Sitio Web Público
👉 **[ranchoraiz.barreal.com](https://oficinabarreal.github.io/rancho-raiz-zira/)**

El sitio ya está en vivo con:
- **Fotos reales** del rancho (habitaciones, pileta, paisajes)
- **Precios actualizados** por habitación y por persona
- **WhatsApp directo** al número de Ayelén
- **Galería** con imágenes del lugar
- **Promociones** activas

### 🔐 Panel de Administración
👉 **[Admin Panel](https://oficinabarreal.github.io/rancho-raiz-zira/admin/)**

Cualquier cambio que hagan en el Google Sheets se refleja automáticamente en el sitio web en ~30 minutos. Pueden actualizar:

| Sección | Qué pueden cambiar |
|---------|-------------------|
| 🛏️ **Habitaciones** | Fotos, precios, descripciones, promociones |
| 🛎️ **Servicios** | Lo que ofrece el rancho |
| 📸 **Galería** | Fotos del lugar |
| 🏷️ **Promociones** | Ofertas especiales |
| ⚙️ **Config** | Teléfono, dirección, WhatsApp |

**Contraseña del admin:** `rancho`

### 📊 Tablero de Control
👉 **[Dashboard](https://oficinabarreal.github.io/rancho-raiz-zira/panel/)**

Vista rápida del estado del sistema, reservas y métricas.

---

## 🚀 Lo que ya funciona (logros)

### 📸 Fotos Reales en el Sitio
Descargamos 10 fotos reales del Instagram de Rancho Raíz y las pusimos en el sitio. Sin stock photos, sin imágenes genéricas — son las habitaciones, la pileta, el paisaje de Barreal.

### 💬 WhatsApp Integrado
Todas las consultas del sitio web van directo al WhatsApp de Ayelén. Un solo número para gestionar reservas: **+54 9 11 5959-5869**.

### 📋 Google Sheets = CMS
El equipo edita el Sheet y el sitio se actualiza solo. No hay que tocar código, no hay que pedirle a un programador. Se hizo un video tutorial para que cualquiera pueda hacerlo.

### 🔄 Auto-Despliegue
Cada cambio en el Sheet dispara una actualización automática del sitio web. El sistema construye y publica la nueva versión en ~2 minutos.

### 🔒 Seguridad
Los datos sensibles (contraseña de admin, URL del Sheet) no se exponen públicamente. El sitio es seguro.

### 🖼️ Banner Animado
Zira (la montañita) está viva en el sitio — saluda a los visitantes con animaciones SVG.

---

## 🛠️ Cómo actualizar el sitio (para el equipo)

### Paso 1: Abrir el Google Sheet
El link está en el panel de admin.

### Paso 2: Editar la pestaña que corresponda
| Pestaña | Para qué |
|---------|----------|
| `config` | Teléfono, dirección, WhatsApp |
| `habitaciones` | Fotos, precios, descripciones |
| `servicios` | Lo que ofrecemos |
| `galeria` | Fotos del rancho |
| `promociones` | Ofertas especiales |

### Paso 3: ¡Listo!
El sitio se actualiza solo en 30 minutos. Si querés que sea inmediato, avisale a Diego.

> ⚠️ **Importante:** No subir fotos con huéspedes. Solo paisajes, habitaciones vacías y espacios comunes.

---

## 📱 Redes

- **Instagram:** [@ranchoraiz.barreal](https://instagram.com/ranchoraiz.barreal)
- **WhatsApp:** [+54 9 11 5959-5869](https://wa.me/5491159595869)
- **Dashboard:** [GitHub Pages](https://oficinabarreal.github.io/rancho-raiz-zira/)

---

## 🧠 Para los curiosos (stack técnico)

| Componente | Tecnología |
|-----------|-----------|
| 🤖 **Agente IA** | big-pickle via Hermes Agent (Termux/Android) |
| 🐍 **Backend scripts** | Python 3.13 |
| 🌐 **Hosting** | GitHub Pages |
| 📊 **CMS** | Google Sheets API |
| 🔄 **CI/CD** | GitHub Actions (auto-deploy cada 30 min) |
| 💬 **Contacto** | WhatsApp API vía wa.me links |
| 🖼️ **Mascota** | Zira — montaña SVG animada |

---

<div align="center">
  <sub>🏔️ <strong>Rancho Raíz</strong> · Evaristo Gomez 3511, Barreal, San Juan · Argentina</sub>
  <br>
  <sub>Gestionado con ❤️ por Diego, Zira y el equipo · 2026</sub>
  <br>
  <sub>🔧 Última limpieza: 9 de junio 2026</sub>
</div>
