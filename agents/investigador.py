import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import feedparser
from datetime import datetime, timedelta

class ResumenTecnico(BaseModel):
    titulo_original: str = Field(description="El título de la noticia SIEMPRE TRADUCIDO AL ESPAÑOL de forma atractiva.")
    enlace: str = Field(description="Enlace URL a la fuente original")
    resumen_tecnico: str = Field(description="Resumen técnico detallado (aprox 250-350 palabras) explicando el vector de ataque, el impacto y posibles mitigaciones.")
    categoria: str = Field(description="Categoría de la noticia: 'Vulnerabilidad', 'Incidente', 'Malware', 'Latam' o 'General'.")

class InvestigadorSegurInfo:
    def __init__(self):
        # Usamos el modelo Next-Gen confirmado por el usuario
        self.model_name = 'gemini-3.1-flash-lite-preview'
        self.history_file = os.path.join("output", "processed_links.json")
        self.sources_file = "sources.json"
        self.system_prompt = """
        Eres un investigador de ciberseguridad experto en OSINT. Tu tarea es filtrar y resumir noticias relevantes.
        
        CLSIFICACIÓN (CRÍTICO):
        - 'Vulnerabilidad': Errores de software, CVEs, parches críticos.
        - 'Incidente': Filtraciones de datos, ataques activos, ransomware, intrusiones.
        - 'Malware': Nuevos troyanos, virus, campañas de phishing técnico.
        - 'Latam': Cualquier noticia que afecte específicamente a Argentina o Latinoamérica.
        - 'General': Novedades tecnológicas de seguridad, leyes, o tendencias.

        Resumen: Detallado y profesional.
        """

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                return json.load(f)
        return []

    def _save_history(self, link):
        history = self._load_history()
        history.append(link)
        # Mantener últimos 500 links
        with open(self.history_file, "w") as f:
            json.dump(history[-500:], f, indent=4)

    def _fetch_rss_news(self):
        if not os.path.exists(self.sources_file):
            return []
            
        with open(self.sources_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        history = self._load_history()
        news = []
        
        for feed_info in config["rss_feeds"]:
            print(f"📡 [@InvestigadorSegurInfo]: Consultando {feed_info['name']}...")
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries[:8]: # Revisar los últimos 8 de cada portal
                    if entry.link not in history:
                        news.append({
                            "title": entry.title,
                            "link": entry.link,
                            "summary": getattr(entry, 'summary', '')[:800]
                        })
            except Exception as e:
                print(f"⚠️ Error en fuente {feed_info['name']}: {e}")
                
        return news

    def investigar_y_procesar(self, max_items=15):
        """Busca noticias, elimina duplicados y devuelve las N más relevantes."""
        print("🕵️‍♂️ [@InvestigadorSegurInfo]: Scrapeando fuentes OSINT...")
        raw_news = self._fetch_rss_news()
        
        if not raw_news:
            print("🕵️‍♂️ [@InvestigadorSegurInfo]: No hay noticias nuevas para procesar.")
            return []

        print(f"🕵️‍♂️ [@InvestigadorSegurInfo]: {len(raw_news)} novedades detectadas. Seleccionando las {max_items} mejores...")
        
        input_text = f"Analiza estas noticias y devuelve un JSON con las {max_items} más impactantes (vulnerabilidades, ataques, incidentes):\n"
        for n in raw_news:
            input_text += f"Título: {n['title']}\nLink: {n['link']}\n\n"

        try:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            # Pedimos una lista de noticias
            class ListaResumenes(BaseModel):
                noticias: list[ResumenTecnico]

            response = client.models.generate_content(
                model=self.model_name,
                contents=self.system_prompt + "\n\nTEXTO:\n" + input_text,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ListaResumenes,
                    temperature=0.3
                )
            )
            data = json.loads(response.text)
            
            # Guardar en historial para no repetir
            for item in data["noticias"]:
                self._save_history(item["enlace"])
                
            print(f"✅ [@InvestigadorSegurInfo]: {len(data['noticias'])} noticias filtradas con éxito.")
            return data["noticias"]
        except Exception as e:
            print(f"🕵️‍♂️ [@InvestigadorSegurInfo]: Error [API TEXTO]: {e}")
            return []
