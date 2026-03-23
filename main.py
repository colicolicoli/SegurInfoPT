import os
import json
from datetime import datetime
from scraper import fetch_latest_news
from processor import process_news_with_ai
from image_gen import generate_image_pollinations

OUTPUT_DIR = "output"

def save_to_markdown(news_item, ai_content, index, run_date, image_path=None):
    """Guarda el resultado en un archivo Markdown legible localmente."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    date_str = run_date.strftime("%Y-%m-%d")
    filename = f"{OUTPUT_DIR}/{date_str}_noticia_{index}.md"
    
    md_content = f"# Noticia: {news_item['title']}\n"
    md_content += f"**Fuente:** {news_item['source']} | **Fecha original:** {news_item['published_at']}\n"
    md_content += f"**Categoría:** {ai_content['category']}\n\n"
    
    md_content += f"## Resumen Simplificado\n{ai_content['summary']}\n\n"
    
    md_content += f"## 🐦 X (Twitter) Thread\n"
    for i, tweet in enumerate(ai_content['x_thread']):
        # Reemplazar placeholder con link real si lo hay
        t_text = tweet.replace("[Link]", news_item['link']).replace("[URL]", news_item['link'])
        md_content += f"**Tweet {i+1}:** {t_text}\n\n"
        
    md_content += f"## 📸 Instagram Caption\n{ai_content['instagram_caption']}\n\n"
    
    md_content += f"## 🎨 Generación de Imagen (Visual Prompt)\n"
    md_content += f"> {ai_content['instagram_visual_prompt']}\n\n"
    
    if image_path:
        md_content += f"**🖼️ Imagen generada:** guardada en local `{image_path}`\n\n"
    
    md_content += f"---\n*Generado automáticamente por el Agente SegurInfo para Todos*\n"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Guardado en: {filename}")

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Iniciando Agente 'SegurInfo para todos'...")
    
    # 1. Obtener noticias de las últimas 24hs
    news_list = fetch_latest_news(hours=24)
    print(f"Se encontraron {len(news_list)} noticias recientes.")
    
    if not news_list:
        print("No hay noticias nuevas para procesar.")
        return

    # Aquí podríamos agregar un paso de curación/filtrado para seleccionar solo la MEJOR noticia,
    # Por ahora procesaremos 1 como máximo para no saturar la cuota gratuita.
    max_to_process = min(1, len(news_list))
    today = datetime.now()
    
    for i in range(max_to_process):
        item = news_list[i]
        print(f"\nProcesando Noticia {i+1}/{max_to_process}: {item['title']}")
        
        # 2. Procesar con Gemini
        ai_result = process_news_with_ai(item)
        
        if ai_result:
            # 3. Generar la imagen gratuita
            img_filename = f"{today.strftime('%Y-%m-%d')}_img_{i+1}.jpg"
            img_path = generate_image_pollinations(ai_result['instagram_visual_prompt'], filename=img_filename)
        
            # 4. Guardar el Output Local
            save_to_markdown(item, ai_result, i+1, today, image_path=img_path)
        else:
            print("No se pudo procesar la noticia. Revisar API Key o conexión.")

if __name__ == "__main__":
    main()
