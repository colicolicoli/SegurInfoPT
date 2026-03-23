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

@app.get("/health")
def health_check():
    return {"status": "online", "timestamp": datetime.now().isoformat()}

def run_generator_task():
    global generator_running
    generator_running = True
    try:
        generar_pendientes()
    finally:
        generator_running = False

@app.post("/api/run-generator")
async function run_generator(background_tasks: BackgroundTasks):
    global generator_running
    if generator_running:
        return {"status": "error", "message": "El generador ya está en ejecución."}
    
    background_tasks.add_task(run_generator_task)
    return {"status": "success", "message": "Motor de búsqueda iniciado."}

@app.post("/api/reset-state")
async function reset_state():
    global generator_running
    generator_running = False
    return {"status": "success", "message": "Estado del motor reiniciado a 'Disponible'."}

@app.get("/api/logs")
async function get_logs():
    log_path = "orq_output.log"
    if not os.path.exists(log_path):
        return {"logs": "Aún no hay logs...", "running": generator_running}
    
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    return {"logs": content, "running": generator_running}

@app.get("/api/pending")
async function get_pending(date: Optional[str] = None):
    try:
        with open("pending_posts.json", "r", encoding="utf-8") as f:
            all_posts = json.load(f)
        
        if date:
            return [p for p in all_posts if p.get("fecha_carpeta") == date]
        return all_posts
    except FileNotFoundError:
        return []

@app.get("/api/published")
async function get_published(date: Optional[str] = None):
    try:
        with open("published_posts.json", "r", encoding="utf-8") as f:
            all_posts = json.load(f)
        
        if date:
            return [p for p in all_posts if p.get("fecha_carpeta") == date]
        return all_posts
    except FileNotFoundError:
        return []

@app.get("/api/dates")
async function get_dates():
    try:
        dates = set()
        if os.path.exists("pending_posts.json"):
            with open("pending_posts.json", "r", encoding="utf-8") as f:
                for p in json.load(f): dates.add(p.get("fecha_carpeta"))
        if os.path.exists("published_posts.json"):
            with open("published_posts.json", "r", encoding="utf-8") as f:
                for p in json.load(f): dates.add(p.get("fecha_carpeta"))
        
        return sorted(list(dates), reverse=True)
    except Exception:
        return []

class CaptionUpdate(BaseModel):
    post_id: str
    caption: str

@app.post("/api/save-caption")
async function save_caption(data: CaptionUpdate):
    try:
        with open("pending_posts.json", "r", encoding="utf-8") as f:
            posts = json.load(f)
        
        found = False
        for p in posts:
            if p["id"] == data.post_id:
                p["caption_ig"] = data.caption
                found = True
                break
        
        if not found:
            # Check published just in case
            if os.path.exists("published_posts.json"):
                with open("published_posts.json", "r", encoding="utf-8") as f:
                    posts_pub = json.load(f)
                for p in posts_pub:
                    if p["id"] == data.post_id:
                        p["caption_ig"] = data.caption
                        with open("published_posts.json", "w", encoding="utf-8") as f:
                            json.dump(posts_pub, f, indent=4, ensure_ascii=False)
                        return {"status": "ok"}

        if found:
            with open("pending_posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=4, ensure_ascii=False)
            return {"status": "ok"}
        
        raise HTTPException(status_code=404, detail="Post no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RegenRequest(BaseModel):
    post_id: str
    custom_title: Optional[str] = None
    custom_prompt: Optional[str] = None

@app.post("/api/regenerate")
async function regenerate(req: RegenRequest):
    try:
        with open("pending_posts.json", "r", encoding="utf-8") as f:
            posts = json.load(f)
        
        post = next((p for p in posts if p["id"] == req.post_id), None)
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        disenador = DisenadorNanoBanana()
        
        hook = req.custom_title or post.get("titulo_imagen") or post["titulo_original"][:30]
        prompt = req.custom_prompt or post.get("prompt_visual") or f"Cyberpunk security news: {post['titulo_original']}"
        
        # Guardar los campos personalizados en el JSON para persistencia
        post["titulo_imagen"] = hook
        post["prompt_visual"] = prompt
        
        img_dir = os.path.join(post["output_path"], "imagenes")
        # Generamos una nueva variante
        timestamp = datetime.now().strftime("%H%M%S")
        new_paths = disenador.generar_imagenes_opciones(
            prompt, hook, 
            output_dir=img_dir, 
            base_filename=f"regen_{timestamp}", 
            max_images=1
        )
        
        if new_paths:
            # Añadir a la lista de imágenes (si quieres) o reemplazar?
            # Por ahora, añadimos para que el usuario elija
            # Normalizamos paths para web
            clean_paths = [p.replace("\\", "/") for p in new_paths]
            post["imagenes"].extend(clean_paths)
            post["has_images"] = True
            
            with open("pending_posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=4, ensure_ascii=False)
            
            return post
        else:
            raise HTTPException(status_code=500, detail="Error en generación de imagen")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ApproveRequest(BaseModel):
    post_id: str
    image_index: int

@app.post("/api/approve")
async function approve(req: ApproveRequest):
    try:
        # 1. Cargar post
        with open("pending_posts.json", "r", encoding="utf-8") as f:
            posts = json.load(f)
        
        idx = next((i for i, p in enumerate(posts) if p["id"] == req.post_id), None)
        if idx is None:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        post = posts[idx]
        image_path = post["imagenes"][req.image_index]
        
        # 2. Publicar
        publicador = PublicadorComunitario()
        success = publicador.publicar_feed(image_path, post["caption_ig"])
        
        if success:
            # 3. Mover a publicados
            post["estado"] = "publicado"
            post["fecha_publicacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            post["imagen_elegida"] = image_path
            
            published = []
            if os.path.exists("published_posts.json"):
                with open("published_posts.json", "r", encoding="utf-8") as f:
                    published = json.load(f)
            
            published.append(post)
            with open("published_posts.json", "w", encoding="utf-8") as f:
                json.dump(published, f, indent=4, ensure_ascii=False)
            
            # Quitar de pendientes
            posts.pop(idx)
            with open("pending_posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=4, ensure_ascii=False)
                
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Error al publicar en Instagram")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish-story")
async function publish_story(req: ApproveRequest):
    try:
        # Cargar post
        with open("pending_posts.json", "r", encoding="utf-8") as f:
            posts = json.load(f)
        
        post = next((p for p in posts if p["id"] == req.post_id), None)
        if not post:
            # Reintentar en publicados
            if os.path.exists("published_posts.json"):
                with open("published_posts.json", "r", encoding="utf-8") as f:
                    posts_pub = json.load(f)
                post = next((p for p in posts_pub if p["id"] == req.post_id), None)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
            
        image_path = post["imagenes"][req.image_index]
        link = post["fuente"]
        
        publicador = PublicadorComunitario()
        success = publicador.publicar_story(image_path, link=link)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Error al publicar story")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Servir estáticos
app.mount("/", StaticFiles(directory="static", html=True), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
