import os
import sys
import requests
import urllib.parse
from PIL import Image
from io import BytesIO

# Configurar salida para soportar emojis en consola Windows
sys.stdout.reconfigure(encoding='utf-8')

def generate_image_pollinations(visual_prompt, filename="output_image.jpg"):
    """
    Usa la API pública y gratuita de Pollinations.ai para generar una imagen 
    basada en el prompt visual en inglés o español. No requiere API Key.
    """
    print(f"🎨 Generando imagen para: '{visual_prompt[:50]}...'")
    
    # Pollinations.ai funciona pasando el prompt directamente en la URL
    encoded_prompt = urllib.parse.quote(visual_prompt)
    
    # Agregamos parámetros de tamaño
    # width=1080 & height=1080 es el tamaño ideal para Instagram
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Abrimos la imagen y la guardamos
        image = Image.open(BytesIO(response.content))
        
        output_dir = "output/images"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        full_path = os.path.join(output_dir, filename)
        image.save(full_path)
        print(f"✅ Imagen generada y guardada en: {full_path}")
        return full_path
        
    except Exception as e:
        print(f"⚠️ Error al generar la imagen: {e}")
        return None

if __name__ == "__main__":
    # Prueba rápida
    test_prompt = "Una ilustración flat design de un ladrón digital usando un uniforme de guardia viejo frente a un robot dormido con luces de neon."
    generate_image_pollinations(test_prompt, "prueba_guardia.jpg")
