# SegurInfo PT 🛡️📡🚀

**Unified Cyberpunk Security Digest Dashboard with Instagram Stories & Feed Integration.**

Democratizando la ciberseguridad para Argentina y Latinoamérica mediante IA y automatización estética.

## 🌟 Características Principales
- **Investigador OSINT:** Scrapea automáticamente noticias de seguridad de fuentes líderes (RSS).
- **Redactor 'Para Todos':** Traduce y simplifica tecnicismos complejos para el público general usando Gemini 3.1 Flash.
- **Diseñador NanoBanana:** Genera posters cibernéticos en formato **9:16 (768x1344)** optimizados para Instagram.
- **Story Integration:** Publicación directa de Historias con **Link Stickers clickeables**.
- **Dashboard Cyberpunk:** Interfaz visual futurista para curar, editar y disparar publicaciones.

## 🚀 Instalación Rápida

1. **Clonar el repo:**
   ```bash
   git clone https://github.com/colicolicoli/SegurInfoPT.git
   cd SegurInfoPT
   ```

2. **Configurar Entorno:**
   Crea un archivo `.env` con:
   ```env
   GEMINI_API_KEY=tu_clave
   POLLINATIONS_API_KEY=tu_clave
   IG_USERNAME=usuario_instagram
   IG_PASSWORD=password_instagram
   ```

3. **Instalar Dependencias:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install fastapi uvicorn google-genai instagrapi requests feedparser beautifulsoup4 python-dotenv
   ```

4. **Lanzar Dashboard:**
   ```bash
   python app.py
   ```
   Accede a: `http://localhost:5000`

## 🛠️ Stack Tecnológico
- **Backend:** Python / FastAPI
- **AI (Texto):** Google Gemini 3.1 Flash-Lite
- **AI (Imagen):** Pollinations AI (Motor Flux)
- **IG Engine:** Instagrapi
- **Frontend:** HTML5 / CSS3 (Vanilla Cyberpunk Design)

---
*Desarrollado con ❤️ para la comunidad de Seguridad de la Información.*
