import os
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
            
            # Asegurar ruta absoluta (clave para Windows)
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

    def publicar_en_story(self, image_path, link_url):
        """Publica la imagen en Stories con un sticker de Link."""
        if not self.username or not self.password:
            print("🛑 [@PublicadorComunitario]: Faltan credenciales IG_USERNAME o IG_PASSWORD.")
            return False
            
        print("📢 [@PublicadorComunitario]: Iniciando sesión para Story...")
        client = Client()
        try:
            client.login(self.username, self.password)
            abs_image_path = os.path.abspath(image_path)
            
            print(f"📢 [@PublicadorComunitario]: Subiendo Story con Link: {link_url}")
            
            # StoryLink es el sticker clickable
            link = StoryLink(webUri=link_url)
            
            # Subir Story
            media = client.photo_upload_to_story(
                path=abs_image_path,
                links=[link]
            )
            
            print(f"✅ [@PublicadorComunitario]: ¡Story publicada! (Media ID: {media.id})")
            return True
            
        except Exception as e:
            print(f"🛑 [@PublicadorComunitario]: Error en Story: {str(e)}")
            return False
