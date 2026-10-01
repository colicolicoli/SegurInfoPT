import os
import json
import re
from groq import Groq
import feedparser
from datetime import datetime, timedelta

def limpiar_cve_ficticios(texto: str) -> str:
    """Elimina marcadores de posición de CVE inventados o placeholders como CVE-2026-XXXXX."""
    if not texto:
        return ""
    patron = r'\(?CVE[-‑]?[0-9]{4}[-‑]?[XAYBxa-yb_]{2,}\)?'
    texto = re.sub(patron, '', texto)
    texto = re.sub(r' {2,}', ' ', texto)
    return texto.strip()

class InvestigadorSegurInfo:
    def __init__(self):
        self.model_name = os.environ.get("GROQ_MODEL", 'openai/gpt-oss-120b')
        self.history_file = os.path.join("output", "processed_links.json")
        self.sources_file = "sources.json"
        self.system_prompt = """
        Eres un investigador de ciberseguridad experto en OSINT. Tu tarea es filtrar y resumir noticias relevantes.
        
        CLASIFICACIÓN (CRÍTICO):
        - 'Vulnerabilidad': Errores de software, CVEs, parches críticos.
        - 'Incidente': Filtraciones de datos, ataques activos, ransomware, intrusiones.
        - 'Malware': Nuevos troyanos, virus, campañas de phishing técnico.
        - 'Latam': Cualquier noticia que afecte específicamente a Argentina o Latinoamérica.
        - 'General': Novedades tecnológicas de seguridad, leyes, o tendencias.

        REGLA ESTRICTA DE CVE:
        Está ESTRICTAMENTE PROHIBIDO inventar o usar marcadores ficticios como 'CVE-2026-XXXXX', 'CVE-XXXX', etc.
        Solo incluye un código CVE si la fuente original lo menciona EXPLÍCITAMENTE (ej: CVE-2024-12345).
        Si la noticia NO especifica un código CVE concreto y real, NO menciones la sigla CVE ni ningún código inventado.

        Resumen: Detallado y profesional (aprox 250-350 palabras) explicando el vector de ataque, impacto y mitigaciones.
        
        FORMATO DE RESPUESTA:
        Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura:
        {
            "noticias": [
                {
                    "titulo_original": "Título atractivo siempre traducido al español",
                    "enlace": "URL original de la noticia",
                    "resumen_tecnico": "Resumen técnico detallado de 250-350 palabras",
                    "categoria": "Vulnerabilidad | Incidente | Malware | Latam | General"
                }
            ]
        }
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
        
        input_text = f"Analiza estas noticias y devuelve un JSON con las {max_items} más impactantes (vulnerabilidades, ataques, incidentes). RECUERDA: no inventes códigos CVE ficticios (como CVE-XXXX).\n\n"
        for n in raw_news:
            resumen_previo = n.get('summary', '').strip()
            input_text += f"Título: {n['title']}\nLink: {n['link']}\n"
            if resumen_previo:
                input_text += f"Detalle: {resumen_previo[:400]}\n"
            input_text += "\n"

        try:
            groq_key = os.environ.get("GROQ_API_KEY")
            if not groq_key:
                print("🛑 [@InvestigadorSegurInfo]: Falta GROQ_API_KEY en .env")
                return []

            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": input_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            raw_content = completion.choices[0].message.content
            data = json.loads(raw_content)
            noticias_filtradas = data.get("noticias", [])
            
            # Sanitizar y guardar en historial
            for item in noticias_filtradas:
                item["resumen_tecnico"] = limpiar_cve_ficticios(item.get("resumen_tecnico", ""))
                item["titulo_original"] = limpiar_cve_ficticios(item.get("titulo_original", ""))
                self._save_history(item.get("enlace", ""))
                
            print(f"✅ [@InvestigadorSegurInfo]: {len(noticias_filtradas)} noticias filtradas con éxito con Groq ({self.model_name}).")
            return noticias_filtradas
        except Exception as e:
            print(f"🕵️‍♂️ [@InvestigadorSegurInfo]: Error [API GROQ]: {e}")
            return []
