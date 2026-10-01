import os
import glob
import random
import subprocess
from datetime import datetime
from instagrapi import Client
from instagrapi.types import StoryLink

class PublicadorComunitario:
    def __init__(self):
        self.username = os.environ.get("IG_USERNAME")
        self.password = os.environ.get("IG_PASSWORD")
        self.client = Client()

    def publicar_en_instagram(self, image_path, caption):
        """Conecta a Instagram y publica la imagen en el feed del usuario."""
        if not self.username or not self.password:
            print("🛑 [@PublicadorComunitario]: Faltan credenciales IG_USERNAME o IG_PASSWORD en el archivo .env.")
            return False
            
        print("📢 [@PublicadorComunitario]: Iniciando sesión en Instagram...")
        client = Client() # Fresh client per upload to avoid session issues in long-running app
        try:
            # Login
            client.login(self.username, self.password)
            
            # Asegurar ruta absoluta
            abs_image_path = os.path.abspath(image_path)
            
            print(f"📢 [@PublicadorComunitario]: Subiendo {abs_image_path} al Feed...")
            # Subir Imagen
            media = client.photo_upload(
                path=abs_image_path,
                caption=caption
            )
            
            print(f"✅ [@PublicadorComunitario]: ¡Post publicado! (Media ID: {media.id})")
            return True
            
        except Exception as e:
            error_msg = f"🛑 [@PublicadorComunitario]: Error crítico al publicar en Instagram.\n🔍 DETALLE TÉCNICO: {str(e)}"
            print(error_msg)
            
            # Guardar error en un archivo para fácil lectura
            with open("output/instagram_error.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
            
            return False

    def _crear_video_story_con_musica(self, image_path, duracion=15):
        """
        Si hay pistas de audio en assets/audio/cyberpunk, genera un video MP4 vertical (1080x1920)
        de 15 segundos con la imagen y una pista musical rotativa con fade-out al final.
        Devuelve la ruta absoluta del archivo .mp4, o None si no hay pistas disponibles.
        """
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        # Buscar carpetas posibles de audio
        posibles_rutas = [
            os.path.join("assets", "audio", "cyberpunk"),
            os.path.join("agent", "assets", "audio", "cyberpunk"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "cyberpunk"))
        ]
        
        audio_files = []
        for r in posibles_rutas:
            if os.path.exists(r):
                for ext in ("*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg"):
                    audio_files.extend(glob.glob(os.path.join(r, ext)))
                if audio_files:
                    break

        if not audio_files:
            print("ℹ️ [@PublicadorComunitario]: No se encontraron canciones en assets/audio/cyberpunk. Subiendo como imagen estática.")
            return None

        # Rotación aleatoria de canciones
        audio_elegido = random.choice(audio_files)
        nombre_track = os.path.basename(audio_elegido)
        print(f"🎵 [@PublicadorComunitario]: Pista cyberpunk seleccionada (rotativa): '{nombre_track}'")

        # Directorio de salida para videos de historias
        stories_dir = os.path.join("output", "stories")
        os.makedirs(stories_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = os.path.abspath(os.path.join(stories_dir, f"story_{timestamp}.mp4"))

        # Renderizar video vertical 1080x1920 con audio y fade out en los últimos 2 segundos
        cmd = [
            ffmpeg_exe, '-y',
            '-loop', '1', '-i', os.path.abspath(image_path),
            '-i', os.path.abspath(audio_elegido),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k', '-ar', '44100',
            '-af', f'afade=t=out:st={duracion - 2}:d=2',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',
            '-t', str(duracion),
            '-pix_fmt', 'yuv420p',
            video_path
        ]

        print(f"🎬 [@PublicadorComunitario]: Renderizando video de historia de {duracion}s con FFmpeg...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            print(f"✅ [@PublicadorComunitario]: Video musical generado con éxito ({os.path.getsize(video_path) // 1024} KB)")
            # Generar thumbnail exacto del primer frame con ffmpeg para instagrapi
            thumb_path = f"{video_path}.jpg"
            thumb_cmd = [
                ffmpeg_exe, '-y',
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                thumb_path
            ]
            subprocess.run(thumb_cmd, capture_output=True)
            return video_path, thumb_path
        else:
            print(f"⚠️ [@PublicadorComunitario]: No se pudo renderizar el video, usando imagen fija: {res.stderr[:150]}")
            return None, None

    def publicar_en_story(self, image_path, link_url):
        """Publica la historia con sticker de Link y música cyberpunk rotativa si hay canciones disponibles."""
        if not self.username or not self.password:
            print("🛑 [@PublicadorComunitario]: Faltan credenciales IG_USERNAME o IG_PASSWORD.")
            return False
            
        print("📢 [@PublicadorComunitario]: Iniciando sesión para Story...")
        client = Client()
        try:
            # Asegurar variable de entorno para MoviePy/FFmpeg
            try:
                import imageio_ffmpeg
                os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass

            client.login(self.username, self.password)
            link = StoryLink(webUri=link_url)

            # Intentar generar video con música
            video_path, thumb_path = self._crear_video_story_con_musica(image_path)
            
            if video_path:
                from pathlib import Path
                print(f"📢 [@PublicadorComunitario]: Subiendo Story en VIDEO con música Cyberpunk y Link Sticker...")
                thumbnail_arg = Path(thumb_path) if thumb_path and os.path.exists(thumb_path) else None
                media = client.video_upload_to_story(
                    path=Path(video_path),
                    thumbnail=thumbnail_arg,
                    links=[link]
                )
            else:
                abs_image_path = os.path.abspath(image_path)
                print(f"📢 [@PublicadorComunitario]: Subiendo Story con imagen fija: {abs_image_path}")
                media = client.photo_upload_to_story(
                    path=abs_image_path,
                    links=[link]
                )
            
            print(f"✅ [@PublicadorComunitario]: ¡Story publicada con éxito! (Media ID: {media.id})")
            return True
            
        except Exception as e:
            error_msg = f"🛑 [@PublicadorComunitario]: Error en Story: {str(e)}"
            print(error_msg)
            return False
