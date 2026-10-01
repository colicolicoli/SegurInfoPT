import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# Lista de feeds RSS centrados en Ciberseguridad y Tecnología
RSS_FEEDS = [
    "https://blog.segu-info.com.ar/feeds/posts/default?alt=rss",
    "https://www.welivesecurity.com/la-es/feed/",
    "https://unaaldia.hispasec.com/feed"
]

def fetch_latest_news(hours=24):
    """Obtiene las noticias de las últimas 'hours' horas de los feeds RSS dados."""
    time_threshold = datetime.now() - timedelta(hours=hours)
    latest_news = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Intentar parsear la fecha de publicación
                published_time = None
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    published_time = datetime(*entry.updated_parsed[:6])
                
                # Filtrar por tiempo (si la fecha es válida o nula para no perder datos)
                if published_time and published_time >= time_threshold:
                    latest_news.append({
                        "title": entry.title,
                        "link": entry.link,
                        "summary": remove_html_tags(entry.summary if hasattr(entry, 'summary') else ""),
                        "published_at": published_time.isoformat(),
                        "source": feed.feed.title if hasattr(feed, 'feed') and hasattr(feed.feed, 'title') else feed_url
                    })
        except Exception as e:
            print(f"Error parseando feed {feed_url}: {e}")
            
    return latest_news

def remove_html_tags(text):
    """Limpia las etiquetas HTML del texto para pasarlo limpio a la IA."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)

if __name__ == "__main__":
    news = fetch_latest_news()
    print(f"Noticias encontradas en las últimas 24hs: {len(news)}")
    for n in news:
        print(f"- {n['title']} ({n['source']})")
