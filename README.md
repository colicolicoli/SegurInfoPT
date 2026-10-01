# ⚡ SegurInfoPT: Cyberpunk Security Dashboard

Sistema automatizado de vigilancia (OSINT) y publicación de noticias de ciberseguridad con estética Cyberpunk para Instagram (Feed & Stories con música) y X (Twitter).

---

## 🚀 Características principales

- **🕵️ Investigador OSINT (Groq AI):** Scraper inteligente multicanal (SeguInfo, WeLiveSecurity, BleepingComputer, CISA, etc.) impulsado por Groq (`openai/gpt-oss-120b` / `llama-3.3-70b`) con filtrado estricto y verificación de códigos CVE reales (sin alucinaciones ni placeholders).
- **✍️ Redactor "Para Todos":** Redacta contenido en lote (*batching*) adaptando conceptos técnicos complejos para público general con mini-glosarios, hilos para X y captions listos para Instagram.
- **🎨 Diseñador NanoBanana (Pollinations Flux):** Crea piezas visuales 9:16 con estética cyberpunk / neon-glitch vía Pollinations AI y superposición tipográfica inteligente con soporte multiplataforma de fuentes (macOS, Linux, Windows).
- **🎵 Publicador Automático de Stories con Música:** Convierte las imágenes en micro-videos MP4 de 15 segundos con pistas Cyberpunk/Synthwave rotativas (`assets/audio/cyberpunk/`) y stickers de enlaces interactivos a la fuente de la noticia.
- **📱 Publicación directa en Feed:** Publicación automatizada en el feed con selección de variantes y edición manual de textos.
- **📟 Dashboard Cyberpunk (FastAPI):** Panel de control interactivo con visualización en tiempo real de logs en terminal, selector de fechas y regeneración on-demand.

---

## 🛠️ Instalación rápida

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/colicolicoli/SegurInfoPT.git
   cd SegurInfoPT
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   # Edita .env y añade tus claves (GROQ_API_KEY, POLLINATIONS_API_KEY, IG_USERNAME, IG_PASSWORD)
   ```

5. **Iniciar el servidor:**
   ```bash
   python app.py
   ```
   Abre [http://localhost:8000](http://localhost:8000) en tu navegador.

---

## 📂 Estructura del Proyecto

```
SegurInfoPT/
├── agents/                  # Agentes especializados
│   ├── investigador.py      # Scraper OSINT y clasificación con Groq
│   ├── redactor.py          # Redacción de captions e hilos de X
│   ├── disenador.py         # Generación de arte (Pollinations) y tipografía (Pillow)
│   └── publicador.py        # Publicación en Instagram (Feed y Stories con música)
├── assets/
│   ├── audio/cyberpunk/     # Pistas de música rotativas (.mp3/.wav) para Stories
│   └── logo.png             # Identidad visual
├── static/                  # Frontend cyberpunk (HTML5, CSS3, JS)
├── app.py                   # Servidor FastAPI y endpoints REST
├── orquestador.py           # Motor de ejecución del pipeline diario
├── sources.json             # Directorio de feeds RSS y palabras clave
└── requirements.txt         # Dependencias multiplataforma
```

---

Desarrollado para el equipo de **SegurInfo para Todos**.
