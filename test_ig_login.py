import os
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()

username = os.getenv("IG_USERNAME")
password = os.getenv("IG_PASSWORD")

print(f"Testing login for: {username}")
client = Client()

try:
    success = client.login(username, password)
    print(f"Login outcome: {success}")
    
    # Pruebo subir la primera imagen que encuentre en el output
    import json
    with open("output/pending_posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    post = data[0]
    img_rel_path = post["imagenes"][0]
    # Convertimos a absoluto para estar 100% seguros
    img_abs_path = os.path.abspath(img_rel_path)
    print(f"Attempting upload of: {img_abs_path}")
    
    media = client.photo_upload(
        path=img_abs_path,
        caption="Test from standalone script - " + post["titulo_imagen"]
    )
    print(f"UPLOAD SUCCESSFUL! Media ID: {media.id}")

except Exception as e:
    print(f"FAILED WITH EXCEPTION: {e}")
