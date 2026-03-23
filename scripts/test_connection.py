import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_pollinations():
    print("Testing Pollinations AI Connection...")
    api_key = os.getenv("POLLINATIONS_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        res = requests.get("https://image.pollinations.ai/prompt/test", timeout=10)
        if res.status_code == 200:
            print("✅ Pollinations GET OK")
        else:
            print(f"❌ Pollinations GET Error: {res.status_code}")
    except Exception as e:
        print(f"❌ Pollinations GET Exception: {e}")

if __name__ == "__main__":
    test_pollinations()
