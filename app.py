import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agents.publicador import PublicadorComunitario
from agents.disenador import DisenadorNanoBanana
from datetime import datetime
from orquestador import generar_pendientes
import threading
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SegurInfo Control Center")

# Estado global para saber si el generador está corriendo
generator_running = False

def run_generator_task():
    global generator_running
    generator_running = True
    try:
        generar_pendientes()
    finally:
        generator_running = False

@app.post("/api/run-generator")
def launch_generator(background_tasks: BackgroundTasks):
    global generator_running
    if generator_running:
        return {"status": "error", "message": "El generador ya está en ejecución."}
    
    background_tasks.add_task(run_generator_task)
    return {"status": "success", "message": "Generador iniciado en segundo plano."}

@app.get("/api/logs")
def get_logs():
    log_path = os.path.join("output", "last_run.log")
    if not os.path.exists(log_path):
        return {"logs": "No hay logs disponibles todavía.", "running": generator_running}
    
    # Leemos las últimas 100 líneas
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return {"logs": "".join(lines[-100:]), "running": generator_running}
    except:
        return {"logs": "Error leyendo logs.", "running": generator_running}

@app.post("/api/reset-state")
def reset_state():
    global generator_running
    generator_running = False
    return {"status": "success", "message": "Motor reiniciado con éxito"}

# Montar las carpetas de salida para que las imágenes sean accesibles vía web
app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = os.path.join("output", "pending_posts.json")

class ApprovalRequest(BaseModel):
    post_id: str
    image_index: int

class StoryRequest(BaseModel):
    post_id: str
    image_index: int

class SaveRequest(BaseModel):
    post_id: str
    caption: str

class RegenRequest(BaseModel):
    post_id: str
    custom_title: Optional[str] = None
    custom_prompt: Optional[str] = None

@app.get("/api/dates")
def get_available_dates():
    """Devuelve una lista única de fechas que tienen noticias registradas."""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        cola = json.load(f)
    # Obtenemos fechas únicas y ordenamos (más reciente primero)
    dates = sorted(list(set(post["fecha"] for post in cola)), reverse=True)
    return dates

@app.get("/api/pending")
def get_pending(date: str = None):
    """Devuelve las noticias filtradas por fecha que están pendientes."""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not date:
        dates = sorted(list(set(post["fecha"] for post in data)), reverse=True)
        if not dates: return []
        date = dates[0]
        
    return [item for item in data if item["fecha"] == date and item.get("estado") == "pendiente"]

@app.get("/api/published")
def get_published(date: str = None):
    """Devuelve las noticias filtradas por fecha que ya fueron publicadas."""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not date:
        dates = sorted(list(set(post["fecha"] for post in data)), reverse=True)
        if not dates: return []
        date = dates[0]
        
    return [item for item in data if item["fecha"] == date and item.get("estado") == "publicado"]

@app.post("/api/save-caption")
def save_caption(req: SaveRequest):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="DB not found")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    post = next((item for item in data if item["id"] == req.post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # 1. Actualizar memoria global
    post["caption_ig"] = req.caption
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    # 2. Sincronizar con el archivo local si existe
    # La ruta se deduce de la fecha y el ID
    local_path = os.path.join("output", post["fecha"], post["id"], "post_metadata.json")
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            local_meta = json.load(f)
        local_meta["caption_ig"] = req.caption
        local_meta["estado_edicion"] = "editado_manualmente"
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(local_meta, f, indent=4, ensure_ascii=False)
            
    return {"status": "success"}

@app.post("/api/regenerate")
def regenerate_images(req: RegenRequest):
    global generator_running
    if generator_running:
        raise HTTPException(status_code=400, detail="El sistema está ocupado. Intente más tarde.")
        
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="DB not found")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    post = next((item for item in data if item["id"] == req.post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Activar estado para los logs
    generator_running = True
    
    # Redirigir stdout para que la consola lo lea
    import sys
    # Usar un log específico para este post para que el dashboard lo pueda leer
    log_path = os.path.join("output", f"{req.post_id}_local.log")
    log_file = open(log_path, "w", encoding="utf-8")
    
    class Logger(object):
        def __init__(self, file, stdout):
            self.file = file
            self.stdout = stdout
        def write(self, text):
            self.file.write(text)
            self.stdout.write(text)
            self.file.flush()
        def flush(self):
            self.file.flush()
            self.stdout.flush()

    original_stdout = sys.stdout
    sys.stdout = Logger(log_file, original_stdout)
    
    try:
        print(f"🔄 [ControlCenter]: Generando/Regenerando imágenes para {req.post_id}...")
        disenador = DisenadorNanoBanana()
        # Reusamos la carpeta pero con un nuevo timestamp para evitar cache del browser
        timestamp_regen = datetime.now().strftime("%H%M%S")
        
        # Obtener o crear carpeta de imágenes
        # El ID es tipo "123456_0", la carpeta es "noticia_123456_0"
        folder_name = f"noticia_{req.post_id}"
        # Buscamos la carpeta en el directorio de la fecha del post
        post_dir = os.path.join("output", post["fecha"], folder_name)
        img_folder = os.path.join(post_dir, "imagenes")
        if not os.path.exists(img_folder): os.makedirs(img_folder)
        
        # 1. Aplicar overrides manuales si vienen del usuario
        if req.custom_title:
            post["titulo_imagen"] = req.custom_title
        if req.custom_prompt:
            post["prompt_visual"] = req.custom_prompt

        nuevas_rutas = disenador.generar_imagenes_opciones(
            prompt_visual=post.get("prompt_visual", "Cyberpunk digital security"),
            titulo_imagen=post.get("titulo_imagen", "ALERTA"),
            output_dir=img_folder,
            base_filename=f"regen_{timestamp_regen}",
            max_images=1 
        )
        
        if nuevas_rutas:
            # En lugar de sobreescribir, agregamos a la lista de opciones
            if "imagenes" not in post: post["imagenes"] = []
            post["imagenes"].extend(nuevas_rutas)
            post["has_images"] = True
            
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # También actualizar el meta local
            local_meta_path = os.path.join(post_dir, "post_metadata.json")
            if os.path.exists(local_meta_path):
                with open(local_meta_path, "w", encoding="utf-8") as f:
                    json.dump(post, f, indent=4, ensure_ascii=False)
                    
            print("✅ [ControlCenter]: Imágenes generadas con éxito.")
            return post
        else:
            print("❌ [ControlCenter]: No se pudieron generar las imágenes.")
            raise HTTPException(status_code=500, detail="Error al generar imágenes")
    finally:
        sys.stdout = original_stdout
        log_file.close()
        generator_running = False

@app.post("/api/approve")
def approve_post(req: ApprovalRequest):
    global generator_running
    if generator_running:
        raise HTTPException(status_code=400, detail="El sistema está ocupado. Intente más tarde.")
        
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="DB not found")
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    post = next((item for item in data if item["id"] == req.post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # Activar estado para los logs
    generator_running = True
    
    # Redirigir stdout para que la consola lo lea
    import sys
    log_path = os.path.join("output", "last_run.log")
    log_file = open(log_path, "w", encoding="utf-8")
    
    class Logger(object):
        def __init__(self, file, stdout):
            self.file = file
            self.stdout = stdout
        def write(self, text):
            self.file.write(text)
            self.stdout.write(text)
            self.file.flush()
        def flush(self):
            self.file.flush()
            self.stdout.flush()

    original_stdout = sys.stdout
    sys.stdout = Logger(log_file, original_stdout)
    
    try:
        image_path = post["imagenes"][req.image_index]
        caption = post["caption_ig"]
        
        print(f"🚀 [ControlCenter]: Iniciando publicación del post {req.post_id}...")
        print(f"📸 Imagen: {image_path}")
        publicador = PublicadorComunitario()
        success = publicador.publicar_en_instagram(image_path, caption)
        
        if success:
            print("✅ [ControlCenter]: Publicación completada con éxito.")
            post["estado"] = "publicado"
            post["imagen_elegida"] = image_path
            with open(DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return {"status": "success", "message": "Publicado en Instagram"}
        else:
            print("❌ [ControlCenter]: Error reportado por el PublicadorComunitario.")
            raise HTTPException(status_code=500, detail="Error en Instagram. Revisa la consola o logs.")
            
    except Exception as e:
        print(f"🛑 Error crítico en /api/approve: {e}")
        raise HTTPException(status_code=500, detail=f"Excepción: {str(e)}")
    finally:
        sys.stdout = original_stdout
        log_file.close()
        generator_running = False

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.post("/api/publish-story")
def publish_story(req: StoryRequest):
    global generator_running
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="DB not found")
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    post = next((item for item in data if item["id"] == req.post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if req.image_index < 0 or req.image_index >= len(post.get("imagenes", [])):
        raise HTTPException(status_code=400, detail="Índice de imagen inválido")
        
    image_path = post["imagenes"][req.image_index]
    link_url = post.get("fuente", "https://thehackernews.com") # Link original
    
    # Marcar como ocupado para logs terminales
    generator_running = True
    log_path = os.path.join("output", "last_run.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"📢 [{datetime.now().strftime('%H:%M:%S')}] Iniciando publicación de Story...\n")
        f.write(f"🔗 Link: {link_url}\n")
    
    try:
        publicador = PublicadorComunitario()
        success = publicador.publicar_en_story(image_path, link_url)
        if success:
            return {"status": "success", "message": "Story publicada!"}
        else:
            raise HTTPException(status_code=500, detail="Error al publicar story")
    finally:
        generator_running = False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
