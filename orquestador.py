import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Importar a nuestros 3 Agentes principales (El publicador se usará en la App Web)
from agents.investigador import InvestigadorSegurInfo
from agents.redactor import RedactorFacil
from agents.disenador import DisenadorNanoBanana

def generar_pendientes():
    # Pre-requisitos
    sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv()
    
    # Redirigir salida a log para el dashboard
    log_path = os.path.join("output", "last_run.log")
    log_file = open(log_path, "w", encoding="utf-8")
    
    class Logger(object):
        def __init__(self, file, stdout):
            self.file = file
            self.stdout = stdout
        def write(self, data):
            self.file.write(data)
            self.stdout.write(data)
            self.file.flush()
        def flush(self):
            self.file.flush()
            self.stdout.flush()

    original_stdout = sys.stdout
    sys.stdout = Logger(log_file, original_stdout)

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("🛑 ERROR: Faltan las credenciales de la API de Gemini.")
            return

        print("==================================================")
        print("🚀 INICIANDO MOTOR DE GENERACIÓN: SegurInfo PT")
        print("==================================================")

        # 1. Investigador: Scrapear y procesar (15 noticias)
        investigador = InvestigadorSegurInfo()
        noticias = investigador.investigar_y_procesar(max_items=15)
        
        if not noticias:
            print("\n🛑 Fin del flujo. No se encontraron noticias nuevas.")
            return

        # Directorio de salida diario
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        output_base = os.path.join("output", fecha_hoy)
        os.makedirs(output_base, exist_ok=True)

        # GUARDAR RAW DATA
        with open(os.path.join(output_base, "raw_scraped.json"), "w", encoding="utf-8") as f:
            json.dump(noticias, f, indent=4, ensure_ascii=False)

        # Cargar o inicializar el archivo de pendientes global
        db_path = os.path.join("output", "pending_posts.json")
        pending_db = []
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    pending_db = json.load(f)
            except:
                pending_db = []

        # 2. Redactor: Armar contenido EN LOTE (Mucha mayor eficiencia)
        redactor = RedactorFacil()
        lote_contenido = redactor.redactar_lote(noticias)
        
        if not lote_contenido:
            print("🛑 [@Orquestador]: El redactor no devolvió contenidos. Abortando.")
            return
            
        # Variables para el flujo de guardado
        timestamp_run = datetime.now().strftime("%H%M%S") 
        today_dir = output_base 
        today_str = fecha_hoy 
        puestos_pendientes = pending_db 

        # 3. Procesar resultados y generar imágenes
        for i, item in enumerate(noticias):
            if i >= len(lote_contenido): break
            
            contenido = lote_contenido[i]
            print(f"\n🦾 [Orquestador]: Procesando Noticia {i+1}/{len(noticias)}")
            
            # Diseñador: SOLO PARA LAS TOP 5
            imagenes = []
            has_images = False
            if i < 5:
                print(f"🎨 [Orquestador]: Generando imágenes para noticia destacada...")
                disenador = DisenadorNanoBanana()
                noticia_folder = os.path.join(today_dir, f"noticia_{timestamp_run}_{i}")
                if not os.path.exists(noticia_folder): os.makedirs(noticia_folder)
                
                imagenes = disenador.generar_imagenes_opciones(
                    prompt_visual=contenido['prompt_visual'],
                    titulo_imagen=contenido['titulo_imagen'],
                    output_dir=os.path.join(noticia_folder, "imagenes"),
                    base_filename="opcion",
                    max_images=1 # Generar solo 1 inicialmente para ahorrar cuota
                )
                has_images = True
            else:
                print(f"📝 [Orquestador]: Noticia secundaria. Guardando resumen sin imagen.")
                noticia_folder = os.path.join(today_dir, f"noticia_{timestamp_run}_{i}")
                if not os.path.exists(noticia_folder): os.makedirs(noticia_folder)

            # 4. Guardar Metadata Local
            post_id = f"{timestamp_run}_{i}"
            meta_post = {
                "id": post_id,
                "fecha": today_str,
                "titulo_original": item['titulo_original'],
                "titulo_imagen": contenido['titulo_imagen'],
                "caption_ig": contenido['caption_ig'],
                "prompt_visual": contenido['prompt_visual'],
                "fuente": item['enlace'],
                "categoria": item.get('categoria', 'General'),
                "imagenes": imagenes,
                "has_images": has_images,
                "estado": "pendiente"
            }
            
            with open(os.path.join(noticia_folder, "post_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(meta_post, f, indent=4, ensure_ascii=False)
            
            puestos_pendientes.append(meta_post)

        # Guardar DB actualizada (Global)
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(pending_db, f, indent=4, ensure_ascii=False)
        
        print("\n✅ MOTOR FINALIZADO. Noticias añadidas a la cola.")

    finally:
        sys.stdout = original_stdout
        log_file.close()

if __name__ == "__main__":
    generar_pendientes()
