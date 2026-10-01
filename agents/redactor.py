import os
import json
import re
from groq import Groq

def limpiar_cve_ficticios(texto: str) -> str:
    """Elimina marcadores de posición de CVE inventados o placeholders como CVE-2026-XXXXX."""
    if not texto:
        return ""
    patron = r'\(?CVE[-‑]?[0-9]{4}[-‑]?[XAYBxa-yb_]{2,}\)?'
    texto = re.sub(patron, '', texto)
    texto = re.sub(r' {2,}', ' ', texto)
    return texto.strip()

class RedactorFacil:
    def __init__(self):
        self.model_name = os.environ.get("GROQ_MODEL", 'openai/gpt-oss-120b')
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.system_prompt = """
        Eres el redactor jefe de 'SegurInfo para todos'. Tu tarea es procesar noticias de ciberseguridad y generar contenido para redes sociales que sea EDUCATIVO e IMPACTANTE.
        
        REGLAS DE CONTENIDO (PHILOSOPHY 'PARA TODOS'):
        - Instagram (caption_ig): NO seas demasiado breve. El cuerpo debe tener 2 o 3 párrafos cortos explicando POR QUÉ esta noticia es importante. 
        - GLOSARIO: Si usas términos técnicos (2FA, Malware, Phishing, Ransomware, Kernel, SDK, etc.), incluye una mini-explicación o traducción entre paréntesis o al final del bloque (Ej: "2FA (Autenticación de dos pasos)").
        - REFUERZO DE LINK: Debido a que Instagram no deja clickear links en captions, SIEMPRE termina el caption indicando: "🔗 Link clickable en nuestras Stories 👆" seguido del link crudo para atribución.
        - CVE ESTRICTO: NUNCA inventes códigos CVE ni uses marcadores de posición como 'CVE-2026-XXXXX' o 'CVE-XXXX'. Si la noticia no contiene un código CVE real y verificado, NO menciones la palabra CVE ni agregues códigos ficticios.
        - Tono: Profesional, Cyberpunk, pero EXPLICADO para personas no técnicas.
        
        REGLAS DE FORMATO (CRÍTICO):
        1. ESTRUCTURA IG: El caption_ig DEBE seguir este orden: Desarrollo Detallado con Glosario \n\n Pregunta para la audiencia \n\n 👇 \n\n #Hashtags \n\n "Link en Stories 👆" \n\n Link Original.
        2. LOGOS Y MARCAS: Si mencionan marcas (Microsoft, Apple, Google, Android, Binance, Chrome, etc.), el prompt_visual DEBE incluir: "include the recognizable and centered logo of [Brand] as a central element".
        3. TÍTULO EN IMAGEN (ANTIREDUNDANCIA): El titulo_imagen DEBE ser un "Hook" (gancho) de máximo 4 palabras en MAYÚSCULAS y ESPAÑOL. **PROHIBIDO REPETIR LA MISMA PALABRA** (Ej: NO pongas "IA Y IA"). Usa palabras de acción: "ALERTA", "RIESGO", "CHROME", "ATAQUE", "REVELADO", "URGENTE".
        4. ESTILO VISUAL: Prompts en INGLÉS. Estilo: Photorealistic, cinematic lighting, intense cyberpunk neon aesthetic, high resolution, ultra-tall 9:16 portrait orientation for Instagram.

        FORMATO DE RESPUESTA:
        Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura:
        {
            "items": [
                {
                    "post_x": ["Tweet 1...", "Tweet 2...", "Tweet 3... [Link]"],
                    "caption_ig": "Texto completo para Instagram...",
                    "titulo_imagen": "HOOK CORTO EN MAYÚSCULAS",
                    "prompt_visual": "Detailed prompt in English with cinematic cyberpunk aesthetic..."
                }
            ]
        }
        """

    def redactar_lote(self, noticias_list):
        """Procesa múltiples noticias en una sola llamada para ahorrar cuota."""
        if not noticias_list: return []
        print(f"✍️ [@RedactorFacil]: Procesando LOTE de {len(noticias_list)} noticias con Groq ({self.model_name})...")
        
        # Preparar el input masivo
        bulk_input = ""
        for i, n in enumerate(noticias_list):
            bulk_input += f"--- NOTICIA {i} ---\nTÍTULO: {n.get('titulo_original', '')}\nLINK: {n.get('enlace', '')}\nRESUMEN: {n.get('resumen_tecnico', '')}\n\n"

        try:
            if not self.api_key:
                print("🛑 [@RedactorFacil]: Falta GROQ_API_KEY en .env")
                return []

            client = Groq(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": "PROCESA ESTE LOTE:\n" + bulk_input}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            raw_content = completion.choices[0].message.content
            data = json.loads(raw_content)
            results = data.get("items", [])
            
            # Post-procesamiento de seguridad para cada item
            for idx, item in enumerate(results):
                if idx < len(noticias_list):
                    fuente = noticias_list[idx].get("enlace", "")
                    caption = limpiar_cve_ficticios(item.get("caption_ig", ""))
                    if fuente and fuente not in caption:
                        caption = f"{caption.strip()}\n\n{fuente}"
                    elif fuente and fuente in caption:
                        if not caption.endswith(f"\n\n{fuente}"):
                            clean = caption.replace(fuente, "").strip()
                            caption = f"{clean}\n\n{fuente}"
                    item["caption_ig"] = caption
                    item["titulo_imagen"] = limpiar_cve_ficticios(item.get("titulo_imagen", ""))
                    if "post_x" in item and isinstance(item["post_x"], list):
                        item["post_x"] = [limpiar_cve_ficticios(t) for t in item["post_x"]]
            
            print(f"✍️ [@RedactorFacil]: Lote procesado con éxito con Groq.")
            return results
        except Exception as e:
            print(f"✍️ [@RedactorFacil]: Error [API GROQ] en batching: {e}")
            return []

    def redactar_contenido(self, resumen_tecnico_dict):
        """Fallback para una sola noticia (usado en regeneración on-demand)."""
        res = self.redactar_lote([resumen_tecnico_dict])
        return res[0] if res else None
