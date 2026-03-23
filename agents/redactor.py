import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class EntregablesRedes(BaseModel):
    post_x: list[str] = Field(description="Un hilo de X (máximo 3 tweets). El último tweet DEBE terminar con el link.")
    caption_ig: str = Field(description="Texto para Instagram. Usa '\n\n' (doble salto de línea) para separar bloques. El link final DEBE estar en una línea separada al final de todo.")
    titulo_imagen: str = Field(description="Título corto (máx 4 palabras) para la imagen.")
    prompt_visual: str = Field(description="Descripción visual en INGLÉS. Incluye 'Logo of [Company]' si se menciona una marca.")

class LoteEntregables(BaseModel):
    items: list[EntregablesRedes]

class RedactorFacil:
    def __init__(self):
        self.model_name = 'gemini-3.1-flash-lite-preview' 
        self.api_key = os.environ.get("GEMINI_REDACTOR_KEY") or os.environ.get("GEMINI_API_KEY")
        self.system_prompt = """
        Eres el redactor jefe de 'SegurInfo para todos'. Tu tarea es procesar noticias de ciberseguridad y generar contenido para redes sociales que sea EDUCATIVO e IMPACTANTE.
        
        REGLAS DE CONTENIDO:
        REGLAS DE CONTENIDO (PHILOSOPHY 'PARA TODOS'):
        - Instagram (caption_ig): NO seas demasiado breve. El cuerpo debe tener 2 o 3 párrafos cortos explicando POR QUÉ esta noticia es importante. 
        - GLOSARIO: Si usas términos técnicos (2FA, Malware, Phishing, Ransomware, Kernel, SDK, etc.), incluye una mini-explicación o traducción entre paréntesis o al final del bloque (Ej: "2FA (Autenticación de dos pasos)").
        - REFUERZO DE LINK: Debido a que Instagram no deja clickear links en captions, SIEMPRE termina el caption indicando: "🔗 Link clickable en nuestras Stories 👆" seguido del link crudo para atribución.
        - Tono: Profesional, Cyberpunk, pero EXPLICADO para personas no técnicas.
        
        REGLAS DE FORMATO (CRÍTICO):
        1. ESTRUCTURA IG: El caption_ig DEBE seguir este orden: Desarrollo Detallado con Glosario \n\n Pregunta para la audiencia \n\n 👇 \n\n #Hashtags \n\n "Link en Stories 👆" \n\n Link Original.
        2. LOGOS Y MARCAS: Si mencionan marcas (Microsoft, Apple, Google, Android, Binance, Chrome, etc.), el prompt_visual DEBE incluir: "include the recognizable and centered logo of [Brand] as a central element".
        3. TÍTULO EN IMAGEN (ANTIREDUNDANCIA): El titulo_imagen DEBE ser un "Hook" (gancho) de máximo 4 palabras en MAYÚSCULAS y ESPAÑOL. **PROHIBIDO REPETIR LA MISMA PALABRA** (Ej: NO pongas "IA Y IA"). Usa palabras de acción: "ALERTA", "RIESGO", "CHROME", "ATAQUE", "REVELADO", "URGENTE".
        4. ESTILO VISUAL: Prompts en INGLÉS. Estilo: Photorealistic, cinematic lighting, intense cyberpunk neon aesthetic, high resolution, ultra-tall 9:16 portrait orientation for Instagram.
        """

    def redactar_lote(self, noticias_list):
        """Procesa múltiples noticias en una sola llamada para ahorrar cuota."""
        if not noticias_list: return []
        print(f"✍️ [@RedactorFacil]: Procesando LOTE de {len(noticias_list)} noticias en una sola llamada (Batch Optimization)...")
        
        # Preparar el input masivo
        bulk_input = ""
        for i, n in enumerate(noticias_list):
            bulk_input += f"--- NOTICIA {i} ---\nTÍTULO: {n['titulo_original']}\nLINK: {n['enlace']}\nRESUMEN: {n['resumen_tecnico']}\n\n"

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=self.system_prompt + "\n\nPROCESA ESTE LOTE:\n" + bulk_input,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LoteEntregables,
                    temperature=0.7
                )
            )
            data = json.loads(response.text)
            results = data.get("items", [])
            
            # Post-procesamiento de seguridad para cada item
            for idx, item in enumerate(results):
                fuente = noticias_list[idx].get("enlace", "")
                caption = item.get("caption_ig", "")
                if fuente and fuente not in caption:
                    item["caption_ig"] = f"{caption.strip()}\n\n{fuente}"
                elif fuente and fuente in caption:
                    if not caption.endswith(f"\n\n{fuente}"):
                        clean = caption.replace(fuente, "").strip()
                        item["caption_ig"] = f"{clean}\n\n{fuente}"
            
            print(f"✍️ [@RedactorFacil]: Lote procesado con éxito.")
            return results
        except Exception as e:
            print(f"✍️ [@RedactorFacil]: Error [API TEXTO] en batching: {e}")
            return []

    def redactar_contenido(self, resumen_tecnico_dict):
        """Fallback para una sola noticia (usado en regeneración on-demand)."""
        res = self.redactar_lote([resumen_tecnico_dict])
        return res[0] if res else None
