# Changelog

Todas las novedades y cambios notables en este proyecto serán documentados en este archivo.

## [v2.0.0] - 2026-10-01

### 🚀 Nuevas Funcionalidades
- **Integración con Groq Cloud AI:** Migración de los agentes Investigador y Redactor a la API ultra-rápida de Groq (`openai/gpt-oss-120b` / `llama-3.3-70b-versatile`), eliminando saturaciones y errores 503 por alta demanda de modelos en preview.
- **Stories de Instagram con Música Cyberpunk:**
  - Sistema de generación automática de video vertical (1080x1920) de 15 segundos con FFmpeg.
  - Soporte de pistas de audio locales en `assets/audio/cyberpunk/` con rotación aleatoria automática en cada publicación.
  - Fade-out suave en los últimos 2 segundos del audio.
  - Conservación del Sticker de Link clickable hacia la fuente de la noticia original.
  - Generación automática de miniaturas para evitar fallos de upload.
- **Soporte Nativo Multiplataforma (macOS / Linux / Windows):**
  - Detección automática de fuentes del sistema de macOS (`Impact.ttf`, `Arial Bold.ttf`) y fallbacks en Pillow.
  - Compatibilidad de entorno virtual con Python 3.14 en macOS (Apple Silicon).
  - Cambio de puerto por defecto a `8000` para evitar colisiones con el AirPlay Receiver de macOS (`ControlCenter`).

### 🛡️ Mejoras de Calidad y Anti-Alucinación (CVE)
- **Eliminación estricta de CVEs ficticios:**
  - Envío del extracto y resumen completo del artículo desde los feeds RSS al LLM para capturar CVEs reales.
  - Reglas estrictas en los prompts prohibiendo inventar placeholders (`CVE-XXXX`, `CVE-2026-XXXXX`).
  - Filtro regex de sanitización en Python (`limpiar_cve_ficticios`) para limpiar automáticamente cualquier marcador ficticio en captions y títulos.

### 🧹 Limpieza y DevOps
- Archivo `.env.example` para facilitar la configuración inicial sin exponer credenciales.
- Archivo `.gitignore` robusto que previene el commiteo de claves API, entornos virtuales, logs y videos temporales.
- Actualización de `requirements.txt` con paquetes multiplataforma y soporte de `groq`, `imageio-ffmpeg` y `moviepy`.
