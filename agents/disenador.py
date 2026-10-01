import os
import requests
import urllib.parse
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Endpoints según documentación oficial de Pollinations
POST_URL = "https://gen.pollinations.ai/v1/images/generations"
GET_BASE = "https://image.pollinations.ai"

class DisenadorNanoBanana:
    def __init__(self):
        self.api_key = os.environ.get("POLLINATIONS_API_KEY")
        if self.api_key:
            print(f"✅ [@Disenador - v3.2]: API Key detectada (...{self.api_key[-4:]}) | {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"⚠️ [@Disenador - v3.2]: Sin API Key | {datetime.now().strftime('%H:%M:%S')}")

    def _get_headers(self):
        """Headers con auth si hay API key."""
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _agregar_texto_sobre_imagen(self, image_path, titulo_imagen):
        """Superpone texto con diseño inteligente: separa palabras destacando keywords (marcas/productos)."""
        try:
            img = Image.open(image_path).convert("RGBA")
            w, h = img.size
            print(f"📐 [Pillow] Imagen: {w}x{h}. Transformando: '{titulo_imagen}'")

            # ── 1. Análisis de Keywords (marcas, productos, alertas) ──────────
            keywords_resaltar = ["FBI", "MICROSOFT", "TELEGRAM", "MALWARE", "VIRUS", "ALERTA", "MAC", "MOVIL", "CORREO"]
            palabras = titulo_imagen.upper().replace("?", "").replace("¿", "").split()
            
            lineas_render = []
            current_line = []
            
            # Agrupamos palabras en líneas (máximo 3-4 palabras por línea para que quede grande)
            for i, p in enumerate(palabras):
                is_key = any(k in p for k in keywords_resaltar)
                current_line.append({"text": p, "is_key": is_key})
                if len(current_line) >= 2 or is_key or i == len(palabras) - 1:
                    lineas_render.append(current_line)
                    current_line = []

            # ── 2. Selección de Estilo Cyberpunk ──────────────────────────────
            ESTILOS = [
                {"nombre": "Neon Cyan", "color": (255, 255, 255), "glow": (0, 240, 255, 60), "bg": (0, 10, 40, 180), "pos_y": 0.70},
                {"nombre": "Glitch Magenta", "color": (255, 255, 255), "glow": (255, 0, 180, 70), "bg": (20, 0, 20, 180), "pos_y": 0.65, "glitch": True},
                {"nombre": "Alert Red", "color": (255, 240, 0), "glow": (255, 30, 0, 80), "bg": (60, 0, 0, 190), "pos_y": 0.40},
                {"nombre": "Terminal Green", "color": (0, 255, 100), "glow": (0, 255, 80, 60), "bg": (0, 20, 5, 200), "pos_y": 0.10},
            ]
            estilo = random.choice(ESTILOS)
            print(f"🎨 [Pillow] Estilo: {estilo['nombre']}")

            # ── 3. Renderizado de cada línea ──────────────────────────────────
            draw = ImageDraw.Draw(img)
            y_cursor = h * estilo["pos_y"]
            padding_v = int(h * 0.02)
            
            # Cargamos fuentes (Normal y Keyword) compatibles con macOS, Linux y Windows
            font_candidates = [
                "/System/Library/Fonts/Supplemental/Impact.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Impact.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "C:/Windows/Fonts/impact.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ]
            font_path = next((f for f in font_candidates if os.path.exists(f)), None)
            if not font_path:
                font_path = "Arial"  # Pillow resolverá por nombre de sistema si está disponible
            
            # Capa base para overlays
            overlay_total = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay_total)

            for linea in lineas_render:
                # Calculamos el ancho total de la línea para centrarla
                line_text = " ".join([p["text"] for p in linea])
                
                # Tamaño base por línea
                base_size = int(h * 0.075)
                f_normal = ImageFont.truetype(font_path, base_size)
                f_key = ImageFont.truetype(font_path, int(base_size * 1.35)) # 35% más grande las keys
                
                # Medimos cada palabra
                parts = []
                total_w = 0
                space_w = f_normal.getlength(" ")
                
                for p_obj in linea:
                    f = f_key if p_obj["is_key"] else f_normal
                    bbox = f.getbbox(p_obj["text"])
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    parts.append({"text": p_obj["text"], "w": tw, "h": th, "font": f, "is_key": p_obj["is_key"]})
                    total_w += tw
                
                total_w += space_w * (len(linea) - 1)
                x_cursor = (w - total_w) / 2
                max_h = max([p["h"] for p in parts])
                
                # Dibujamos fondo para la línea
                pad = int(base_size * 0.3)
                ov_draw.rounded_rectangle(
                    [x_cursor - pad, y_cursor - pad, x_cursor + total_w + pad, y_cursor + max_h + pad],
                    radius=5, fill=estilo["bg"]
                )

                # Dibujamos cada palabra
                for p_idx, p_data in enumerate(parts):
                    # 1. Glow si es keyword o según estilo
                    capas = 8 if p_data["is_key"] else 4
                    for c in range(capas, 0, -1):
                        off = c * 1.5
                        g_color = estilo["glow"] if not p_data["is_key"] else (255, 255, 0, 40) if estilo["nombre"]=="Alert Red" else estilo["glow"]
                        ov_draw.text((x_cursor-off, y_cursor), p_data["text"], font=p_data["font"], fill=g_color)
                        ov_draw.text((x_cursor+off, y_cursor), p_data["text"], font=p_data["font"], fill=g_color)
                        ov_draw.text((x_cursor, y_cursor-off), p_data["text"], font=p_data["font"], fill=g_color)
                        ov_draw.text((x_cursor, y_cursor+off), p_data["text"], font=p_data["font"], fill=g_color)

                    # 2. Texto final
                    text_color = estilo["color"] if not p_data["is_key"] else (255, 255, 255) if estilo["nombre"]!="Neon Cyan" else (255, 255, 0)
                    ov_draw.text((x_cursor, y_cursor), p_data["text"], font=p_data["font"], fill=text_color + (255,))
                    
                    x_cursor += p_data["w"] + space_w

                y_cursor += max_h + padding_v * 2

            img = Image.alpha_composite(img, overlay_total)
            img.convert("RGB").save(image_path, "JPEG", quality=92)
            print(f"✅ [Pillow] Diseño multi-tamaño aplicado en {os.path.basename(image_path)}")
            return True
        except Exception as e:
            print(f"❌ [Pillow] Error dinámico: {e}")
            import traceback; traceback.print_exc()
            return False

    def _generar_via_post(self, prompt, full_path, width, height, model="flux"):
        """
        POST /v1/images/generations (OpenAI-compatible)
        El campo para dimensiones es 'size': 'WIDTHxHEIGHT' según la doc oficial.
        """
        import base64
        seed = random.randint(1, 999999)
        payload = {
            "prompt": prompt,
            "model": model,
            "size": f"{width}x{height}",   # ← correcto según docs (no width/height separados)
            "seed": seed,
            "nologo": True,
            "enhance": False,
            "response_format": "b64_json"
        }
        print(f"📡 [POST] model={model} | size={width}x{height}")
        try:
            res = requests.post(POST_URL, headers=self._get_headers(), json=payload, timeout=90)
            print(f"📥 Status: {res.status_code}")
            if res.status_code == 200:
                data = res.json()
                if 'data' in data and data['data']:
                    item = data['data'][0]
                    if 'b64_json' in item:
                        img_data = base64.b64decode(item['b64_json'])
                    elif 'url' in item:
                        img_data = requests.get(item['url'], timeout=30).content
                    else:
                        return False
                    with open(full_path, "wb") as f:
                        f.write(img_data)
                    with Image.open(full_path) as chk:
                        rw, rh = chk.size
                    print(f"💾 [POST] ✅ {rw}x{rh} ({len(img_data):,} bytes)")
                    return True
            else:
                print(f"⚠️ POST Error {res.status_code}: {res.text[:120]}")
        except Exception as e:
            print(f"❌ POST Excepción: {e}")
        return False

    def _generar_via_get(self, prompt, full_path, width, height, model="flux"):
        """
        GET /image/{prompt} con width y height como query params.
        """
        seed = random.randint(1, 999999)
        encoded = urllib.parse.quote(prompt[:250])
        url = f"{GET_BASE}/prompt/{encoded}?model={model}&width={width}&height={height}&seed={seed}&nologo=true"
        print(f"📡 [GET] model={model} | {width}x{height} | {url[:100]}...")
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=90)
            ct = res.headers.get("content-type", "")
            print(f"📥 Status: {res.status_code} | Content-Type: {ct}")
            if res.status_code == 200 and "image" in ct:
                with open(full_path, "wb") as f:
                    f.write(res.content)
                with Image.open(full_path) as chk:
                    rw, rh = chk.size
                print(f"💾 [GET] ✅ {rw}x{rh} ({len(res.content):,} bytes)")
                return True
            else:
                print(f"⚠️ GET Error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"❌ GET Excepción: {e}")
        return False

    def _intentar_pollinations(self, prompt, output_dir, base_filename, index=0, model="flux"):
        """Genera imagen via Pollinations con el modelo indicado (flux o zimage)."""
        import time
        full_path = os.path.join(output_dir, f"{base_filename}_{index}.jpg")

        # POST primero (más confiable para dimensiones exactas), GET como fallback
        estrategias = [
            lambda: self._generar_via_post(prompt, full_path, 864, 1080, model),
            lambda: self._generar_via_get(prompt, full_path, 864, 1080, model),
        ]

        for i, estrategia in enumerate(estrategias):
            print(f"\n🤖 [V3.2] {model.upper()} | Intento {i+1}/{len(estrategias)}...")
            if estrategia():
                return full_path
            time.sleep(2)

        return None

    def _intentar_gemini(self, prompt, output_dir, base_filename, index=0):
        """Genera imagen via Gemini Imagen 3.0 (requiere GEMINI_API_KEY con acceso Imagen)."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️ [Gemini] Sin GEMINI_API_KEY. Saltando motor Gemini.")
            return None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            print(f"🌐 [Gemini] Generando con imagen-3.0-generate-001...")
            result = client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="4:5",
                    output_mime_type="image/jpeg"
                )
            )
            full_path = os.path.join(output_dir, f"{base_filename}_{index}.jpg")
            for img_res in result.generated_images:
                with open(full_path, "wb") as f:
                    f.write(img_res.image.image_bytes)
                with Image.open(full_path) as chk:
                    rw, rh = chk.size
                print(f"💾 [Gemini] ✅ {rw}x{rh}")
                return full_path
        except Exception as e:
            print(f"❌ [Gemini] Error: {e}")
        return None

    def generar_imagenes_opciones(self, prompt_visual, titulo_imagen, output_dir="output/images", base_filename="post", max_images=1, motor="pollinations_flux"):
        """Genera imágenes con el motor seleccionado y superpone texto cyberpunk con Pillow.

        Motores disponibles:
        - 'pollinations_flux'   → Flux Schnell (gratis, rápido)
        - 'pollinations_zimage' → Z-Image Turbo 2x upscaling (gratis, mejor calidad)
        - 'gemini_imagen'       → Gemini Imagen 3.0 (requiere GEMINI_API_KEY pago)
        """
        print(f"🍌 [@DisenadorNanoBanana v3.2]: Motor='{motor}' | {max_images} imagen(es) para '{titulo_imagen}'...")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        estilos = [
            "cinematic cyberpunk atmosphere, neon lights, dark streets, holographic screens, rain, volumetric fog",
            "digital data streams, matrix code, electric blue and magenta, abstract circuits, glitch effects",
            "hacker lair, multiple monitors, dark room, neon glow, dramatic shadows, tech aesthetic"
        ]
        random.shuffle(estilos)

        result_paths = []
        for i in range(max_images):
            estilo = estilos[i % len(estilos)]
            # Por defecto (Flux o Gemini), la imagen es pura sin texto, para usar Pillow
            prompt_plano = f"Dramatic digital artwork. {prompt_visual}. {estilo}. NO text, NO watermarks. 8K quality."
            
            # Para Z-Image (o si el usuario quiere probar texto nativo de la IA)
            prompt_con_texto_ia = f"Dramatic digital artwork. {prompt_visual}. {estilo}. Include HUGE, bold, clear 3D typography text that says '{titulo_imagen}'. Include 3D logos if brands are mentioned. High quality, intense, sharp edges. 8K."

            path = None

            if motor == "pollinations_flux":
                path = self._intentar_pollinations(prompt_plano, output_dir, base_filename, index=i, model="flux")
            elif motor == "pollinations_zimage":
                path = self._intentar_pollinations(prompt_con_texto_ia, output_dir, base_filename, index=i, model="zimage")
            elif motor == "gemini_imagen":
                path = self._intentar_gemini(prompt_plano, output_dir, base_filename, index=i)
                if not path:
                    print("↩️ Gemini falló. Usando Pollinations flux como fallback...")
                    path = self._intentar_pollinations(prompt_plano, output_dir, base_filename, index=i, model="flux")
            else:
                print(f"⚠️ Motor '{motor}' desconocido. Usando flux por defecto.")
                path = self._intentar_pollinations(prompt_plano, output_dir, base_filename, index=i, model="flux")

            if path:
                if motor != "pollinations_zimage":
                    # Usamos Pillow para Flux y Gemini
                    self._agregar_texto_sobre_imagen(path, titulo_imagen)
                else:
                    print(f"✅ [NativeIA] Texto y logos renderizados nativamente por Z-Image en {os.path.basename(path)}")
                result_paths.append(path)
            else:
                print(f"🛑 Todos los intentos fallaron para imagen {i}.")

        if not result_paths:
            print("🛑 Error crítico: No se generó ninguna imagen.")
            return []

        print(f"🍌 ¡{len(result_paths)} imagen(es) lista(s) con motor '{motor}'!")
        return result_paths
