import os
import requests
import urllib.parse
import random
from io import BytesIO
from PIL import Image
from datetime import datetime

class DisenadorNanoBanana:
    def __init__(self):
        self.system_prompt = "Eres el diseñador gráfico automatizado del equipo. Tu tarea es generar imágenes basadas en el prompt visual."
        self.api_key = os.environ.get("POLLINATIONS_API_KEY")
        if self.api_key:
            print(f"✅ [@Disenador - v2.6]: API Key detectada (...{self.api_key[-4:]}) | {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"⚠️ [@Disenador - v2.6]: No se detectó API Key | {datetime.now().strftime('%H:%M:%S')}")

    def _intentar_pollinations(self, prompts, output_dir, base_filename):
        import time
        print(f"🍌 [@DisenadorNanoBanana]: [API IMAGEN] Invocando motor Pollinations AI...")
        generated_paths = []
        
        # Cargar API KEY de la instancia
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            print("🔑 Autenticando con API Key de Pollinations.")
        
        modelos_fallback = ["flux", "turbo", None] 
        
        for i, p_variacion in enumerate(prompts):
            success = False
            for m_idx, model_name in enumerate(modelos_fallback):
                if success: break
                
                # Intentamos hasta 2 veces por cada modelo si hay errores temporales (como 500 o Timeout)
                for intento_modelo in range(2):
                    try:
                        full_path = os.path.join(output_dir, f"{base_filename}_{i}.jpg")
                        
                        # Esperar para evitar 429
                        if i > 0 or m_idx > 0 or intento_modelo > 0: time.sleep(5)
                        
                        ts = datetime.now().strftime('%H:%M:%S')
                        print(f"🤖 [V2.6-FINAL] Opción {i} (Modelo: {model_name or 'flux'} | Intento {intento_modelo+1}/2) | {ts}")
                        
                        # Usamos el endpoint POST (OpenAI compatible) que es más robusto para API Keys
                        # Documentación: gen.pollinations.ai/v1/images/generations
                        api_url = "https://gen.pollinations.ai/v1/images/generations"
                        
                        payload = {
                            "prompt": p_variacion,
                            "model": model_name or "flux",
                            "width": 704,
                            "height": 1216,
                            "aspect_ratio": "9:16",
                            "seed": random.randint(1, 999999),
                            "nologo": True,
                            "enhance": False
                        }
                        
                        # POST request con el Bearer Token corporativo/secret
                        print(f"📡 [V2.6] Enviando petición a Pollinations... (Timeout: 90s)")
                        res_p = requests.post(api_url, headers=headers, json=payload, timeout=90)
                        print(f"📥 [V2.6] Respuesta recibida: {res_p.status_code}")
                        
                        if res_p.status_code == 200:
                            # El endpoint de Pollinations devuelve por defecto JSON con b64 o URL
                            # Pero si pedimos binario o manejamos la respuesta:
                            data = res_p.json()
                            # Pollinations devuelve un array 'data' con objetos {url: "..."} o {b64_json: "..."}
                            # Por defecto es b64_json en su doc para /v1/images/generations
                            
                            import base64
                            if 'data' in data and len(data['data']) > 0:
                                item = data['data'][0]
                                if 'b64_json' in item:
                                    img_data = base64.b64decode(item['b64_json'])
                                    print(f"💾 [V2.6] Guardando imagen de {len(img_data)} bytes...")
                                    with open(full_path, "wb") as f:
                                        f.write(img_data)
                                elif 'url' in item:
                                    img_res = requests.get(item['url'], timeout=30)
                                    print(f"💾 [V2.6] Descargando imagen de {len(img_res.content)} bytes...")
                                    with open(full_path, "wb") as f:
                                        f.write(img_res.content)
                                
                                generated_paths.append(full_path)
                                success = True
                                break
                        elif res_p.status_code == 429:
                            print(f"⏳ Rate Limit (429) en POST. Esperando 15 segundos...")
                            time.sleep(15)
                        elif res_p.status_code >= 500:
                            print(f"🌐 Error de servidor Pollinations ({res_p.status_code})....")
                            time.sleep(5)
                        else:
                            print(f"❌ Error {res_p.status_code}: {res_p.text[:100]}")
                            break # No recuperable
                    
                    except requests.exceptions.Timeout:
                        print(f"⏱️ Timeout en POST (90s). Reintentando...")
                    except Exception as e:
                        print(f"❌ Excepción en POST: {e}")
            
            if not success:
                print(f"🛑 Fallaron todos los intentos para la opción {i}")
                
        return generated_paths

    def _intentar_gemini(self, prompts, output_dir, base_filename):
        # Intentamos con el modelo Imagen 4 solo como secundario por si el usuario escala a pago
        model_name = "imagen-3.0-generate-001" 
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            
            generated_paths = []
            for i, p_variacion in enumerate(prompts):
                result = client.models.generate_images(
                    model=model_name,
                    prompt=p_variacion,
                    config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="3:4")
                )
                for img_res in result.generated_images:
                    img_path = os.path.join(output_dir, f"gemini_{base_filename}_{i}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_res.image.image_bytes)
                    generated_paths.append(img_path)
            return generated_paths
        except Exception as e:
            # No logeamos error ruidoso aquí porque ya sabemos que suele ser pago
            return None

    def generar_imagenes_opciones(self, prompt_visual, titulo_imagen, output_dir="output/images", base_filename="post", max_images=1):
        """Genera N opciones de imagen con Pollinations (Free) y Gemini (Paid Fallback)."""
        print(f"🍌 [@DisenadorNanoBanana]: Preparando {max_images} pieza(s) visual(es) para '{titulo_imagen}'...")
        
        # Optimizamos prompts para Pollinations (FLUX ama el detalle estilizado)
        variaciones_estilo = [
            "aesthetic cyberpunk, neon blue and pink, digital art, high quality, 8k, cinematic lighting",
            "glitch art techno-style, abstract data streams, futuristic circuits, sharp focus",
            "cyberpunk city street, rainy night, holographic billboards, deep contrast"
        ]
        
        # Mezclamos estilos aleatorios si pedimos pocos
        random.shuffle(variaciones_estilo)
        variaciones_a_usar = variaciones_estilo[:max_images]
        
        prompts_finales = []
        for estilo in variaciones_a_usar:
            # Reestructuramos el prompt para que FLUX genere arte vertical y tipografía legible
            p = (
                f"Digital Poster for Instagram, 9:16 aspect ratio. {prompt_visual}. "
                f"CINEMATIC NEON CYBERPUNK AESTHETIC with high contrast and volumetric lighting. "
                f"The image MUST feature a large, centered, and perfectly readable 3D text that says '{titulo_imagen}'. "
                f"Futuristic bold typography. Style focus: {estilo}. "
                f"Photorealistic 8k, unreal engine 5, octane render, masterpiece."
            )
            prompts_finales.append(p)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 1. Intentar con Pollinations (PRIMARIO por ser gratuito y estable)
        result_paths = self._intentar_pollinations(prompts_finales, output_dir, base_filename)
        
        # 2. Si falla Pollinations, intentar Gemini (por las dudas)
        if not result_paths:
            print("🍌 [@DisenadorNanoBanana]: Reintentando con motor secundario...")
            result_paths = self._intentar_gemini(prompts_finales, output_dir, base_filename)
                
        if not result_paths:
            print("🛑 Error crítico: No se pudo generar ninguna imagen.")
            return []

        print(f"🍌 [@DisenadorNanoBanana]: ¡{len(result_paths)} pieza(s) lista(s) con estética Cyberpunk!")
        return result_paths
