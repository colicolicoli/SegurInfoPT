import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Configurar la API Key de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY no encontrada en el archivo .env")

# Definiremos la salida estructurada esperada de Gemini
class SocialMediaPost(BaseModel):
    category: str = Field(description="La categoría de la noticia (Ej. Estafa, Brecha de Datos, Consejos)")
    summary: str = Field(description="Resumen de la noticia en 1 o 2 párrafos, sin tecnicismos.")
    x_thread: list[str] = Field(description="Lista de 1 a 3 strings (tweets) que conforman el hilo de X. El úlitmo debe tener un llamado a la acción y un placeholder para el link.")
    instagram_caption: str = Field(description="Texto para la descripción de Instagram, con emojis y llamado a la acción.")
    instagram_visual_prompt: str = Field(description="Instrucción detallada de cómo debería verse la imagen para Instagram (colores, texto en la imagen, estilo).")

def process_news_with_ai(news_item):
    """
    Toma un diccionario de noticia y devuelve el contenido generado por Gemini.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'tu_api_key_aqui':
        print("ERROR: API Key no configurada. Ejecución simulada.")
        return None

    # Usamos el modelo Gemini 2.0 Flash
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
Eres el creador de contenido principal del proyecto "SegurInfo para todos". 
Tu objetivo es democratizar la seguridad de la información. 
Tu audiencia es el público general sin conocimientos técnicos (desde adolescentes hasta adultos mayores) en Argentina y Latinoamérica.

TONO: Amigable, educativo, empático y preventivo (nunca alarmista). "Para todos" significa simplificar todo al máximo nivel posible.

REGLA ESTRICTA 1: Está estrictamente prohibido usar términos técnicos sin explicarlos. Si usas palabras como "Phishing", "Malware" o "Ransomware", debes proveer inmediatamente una analogía simple (ej. "Malware es como un virus de la gripe, pero para tu compu").
REGLA ESTRICTA 2: No asumas que la gente sabe qué es una "Vulnerabilidad Zero-Day" o un "Ataque DDoS". Traduce TODO.
REGLA ESTRICTA 3: Mantén el foco en LATAM/Argentina si podés dar contexto regional, mejor.

NOTICIA ORIGINAL PARA PROCESAR:
Título: {news_item['title']}
Fuente: {news_item['source']}
Resumen original: {news_item['summary']}

TAREA: Genera el contenido estructurado en JSON respetando el esquema solicitado.
El hilo de X debe tener un gancho.
El visual_prompt debe ser específico para generar luego una imagen (ej. texto clave, sin mucho texto para frenar el scroll).
"""

    try:
        # Generamos usando JSON estructurado (Gemini soporta 'response_schema' en versiones recientes de la SDK)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SocialMediaPost,
                temperature=0.7,
            )
        )
        
        # El response.text debería ser un JSON validado por Pydantic
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Error procesando la noticia con Gemini: {e}")
        return None

if __name__ == "__main__":
    # Test rápido de ejecución
    dummy_news = {
        "title": "Alerta por Phishing bancario masivo en Argentina",
        "source": "SeguridadTech",
        "summary": "Se detectó una nueva campaña de phishing dirigida a usuarios de bancos en Argentina, donde roban tokens de MFA."
    }
    res = process_news_with_ai(dummy_news)
    if res:
        print(json.dumps(res, indent=2, ensure_ascii=False))
