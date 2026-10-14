import os
import re
import random
import time
import base64
from datetime import datetime, timezone
import requests

# 1. Configuration
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
GH_TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
FORCE_POST = os.environ.get("FORCE_POST", "").lower() == "true"

if not WP_URL or not WP_USERNAME or not WP_APP_PASSWORD:
    print("Error: Missing WordPress configuration (WP_URL, WP_USERNAME, or WP_APP_PASSWORD).")
    exit(1)

# Reliable LiteSpeed REST API endpoint
wp_api_endpoint = f"{WP_URL}/?rest_route=/wp/v2/posts"
clean_password = WP_APP_PASSWORD.replace(" ", "")
credentials = f"{WP_USERNAME}:{clean_password}"
token = base64.b64encode(credentials.encode()).decode("utf-8")

headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Purge default demo posts if any remain in WordPress
try:
    print("Checking for default demo posts to purge...")
    demo_check = requests.get(f"{wp_api_endpoint}&per_page=50", headers=headers, timeout=15)
    if demo_check.status_code == 200:
        demo_kws = ["clarity", "lessons learned", "creative living", "uncharted waters", "simple joys", "slowing down", "creative roadblocks", "daily habits", "hello world"]
        for p in demo_check.json():
            p_title = p.get("title", {}).get("rendered", "").lower()
            p_id = p.get("id")
            if any(kw in p_title for kw in demo_kws) or p_id in [1, 14, 16, 18, 20, 22, 24, 26, 28]:
                del_url = f"{WP_URL}/?rest_route=/wp/v2/posts/{p_id}&force=true"
                requests.delete(del_url, headers=headers, timeout=10)
                print(f"Purged demo post #{p_id}: {p.get('title', {}).get('rendered', '')}")
except Exception as e:
    print(f"Demo purge note: {e}")

# Check if 5 posts were already published today (UTC date)
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
if not FORCE_POST:
    try:
        recent_res = requests.get(f"{wp_api_endpoint}&per_page=15", headers=headers, timeout=15)
        if recent_res.status_code == 200:
            posts = recent_res.json()
            today_posts = [p for p in posts if p.get("date_gmt", "")[:10] == today_str]
            if len(today_posts) >= 5:
                print(f"5 blog posts already published today ({today_str}). Daily quota reached. Exiting cleanly.")
                exit(0)
            else:
                print(f"Published {len(today_posts)}/5 posts today. Proceeding with post #{len(today_posts) + 1}...")
    except Exception as e:
        print(f"Date check warning: {e}")

# 2. Pick a Topic
TOPICS_FILE = "topics.txt"
USED_TOPICS_FILE = "used_topics.txt"

topics = []
if os.path.exists(TOPICS_FILE):
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

if not topics:
    selected_topic = "Bivouac Erg Chegaga: Guide Complet du Séjour Saharien"
else:
    selected_topic = topics[0]

print(f"\n==========================================")
print(f"Selected Topic: {selected_topic}")
print(f"==========================================\n")

# 3. Content Generation
article_html = ""
article_excerpt = ""

is_french = any(w in selected_topic.lower() for w in ["dunes de", "excursion", "bivouac", "maroc", "désert", "desert chegaga", "prix", "meilleure", "dormir", "nuit", "comment", "guide complet", "randonnée", "traversée", "incontournables"])
lang_str = "French (Français)" if is_french else "English"

system_prompt = (
    f"You are an expert Morocco travel journalist and Sahara desert expedition guide writing for 'Irriki Tourism' (https://irrikitourism.com), "
    f"based in Foum Zguid, Lake Iriki, and Erg Chegaga in southern Morocco. "
    f"Write an engaging, authoritative, 900-word SEO-optimized travel blog post in {lang_str} that focuses 100% on the exact title provided. "
    f"Format in clean semantic HTML using <p>, <h2>, <h3>, <ul>, <li>, and <strong> tags (do NOT include <h1> or markdown code fences). "
    f"Naturally mention Irriki Tourism's authentic offerings: 4x4 desert expeditions to Erg Chegaga & Lake Iriki from Foum Zguid, "
    f"traditional Berber bivouac camp under the stars, sunset camel trekking, sandboarding, and direct booking via WhatsApp (+212 715 131 709 / https://irrikitourism.com/#packages). "
    f"The very first <p> paragraph MUST be a compelling 2-sentence summary specifically tailored to the topic so it also serves as the meta description/excerpt."
)
user_prompt = f"Write a comprehensive, SEO-optimized travel guide in {lang_str} titled: '{selected_topic}'."

# Attempt 1: GitHub Models Inference API
if not article_html and GH_TOKEN:
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=GH_TOKEN
        )
        for model in ["gpt-4o-mini", "gpt-4o"]:
            try:
                print(f"Attempting GitHub Models generation with: {model}...")
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7
                )
                content = resp.choices[0].message.content.strip()
                if len(content) > 400:
                    article_html = content
                    print("GitHub Models AI generation successful!")
                    break
            except Exception as e:
                print(f"GitHub Model {model} note: {e}")
    except Exception as e:
        print(f"OpenAI client init note: {e}")

# Attempt 2: Pollinations OpenAI-compatible AI endpoint
if not article_html:
    try:
        print("Attempting Pollinations AI generation...")
        poll_res = requests.post(
            "https://text.pollinations.ai/openai",
            headers={"Content-Type": "application/json"},
            json={
                "model": "openai",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            },
            timeout=45
        )
        if poll_res.status_code == 200:
            data = poll_res.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if len(content) > 400:
                article_html = content
                print("Pollinations AI generation successful!")
    except Exception as e:
        print(f"Pollinations AI note: {e}")

if article_html and not article_excerpt:
    article_html = re.sub(r"^```(?:html)?\s*", "", article_html)
    article_html = re.sub(r"\s*```$", "", article_html).strip()
    first_p = re.search(r"<p>(.*?)</p>", article_html, re.DOTALL | re.IGNORECASE)
    if first_p:
        clean_p = re.sub(r"<[^>]+>", "", first_p.group(1)).strip()
        if len(clean_p) > 40:
            article_excerpt = clean_p[:240]

# Fallback: Rich Sahara Travel Guide Generator
if not article_html or not article_excerpt:
    article_excerpt = f"Planifiez votre aventure inoubliable dans le Sahara marocain avec notre guide complet pour {selected_topic}. Conseils de l'équipe locale d'Irriki Tourism à Foum Zguid et au lac Iriki."
    article_html = f"""
<p>Partir à la conquête des dunes dorées et des grands espaces sauvages du Sahara marocain est une expérience hors du commun. Dans ce guide consacré à <strong>{selected_topic}</strong>, notre équipe locale d'experts chez <a href="https://irrikitourism.com/">Irriki Tourism</a> vous dévoile tous les secrets pour réussir votre expédition au départ de Foum Zguid vers l'Erg Chegaga et le lac Iriki.</p>
<h2>Pourquoi Choisir l'Erg Chegaga et Foum Zguid ?</h2>
<p>Situé entre l'Anti-Atlas et les plus hautes vagues de sable du Maroc, le désert de l'Erg Chegaga est réputé pour sa nature sauvage préservée du tourisme de masse. L'accès par Foum Zguid vous fait traverser le mythique lac asséché d'Iriki, célèbre pour ses fossiles et ses pistes historiques du Paris-Dakar.</p>
<ul>
    <li><strong>Expéditions 4x4 Hors-Piste:</strong> Franchissez les plateaux désertiques et les dunes géantes avec nos chauffeurs sahariens natifs de la région.</li>
    <li><strong>Bivouac sous les Étoiles:</strong> Passez la nuit dans notre campement de tentes berbères traditionnelles avec dîner marocain au coin du feu et musique nomade.</li>
    <li><strong>Coucher de Soleil et Sandboarding:</strong> Grimpez sur les crêtes de sable à dos de dromadaire ou dévalez les pentes dorées en sandboard.</li>
</ul>
<h2>Nos Formules de Circuits et Bivouac à Erg Chegaga</h2>
<ol>
    <li><strong>Circuit 1 Journée (150&euro; standard / 120&euro; groupe 4+):</strong> Traversée de Foum Zguid, Ajermia, lac Iriki et coucher de soleil sur les grandes dunes.</li>
    <li><strong>Formule 2 Jours / 1 Nuit (160&euro; standard / 130&euro; groupe 4+):</strong> Safari 4x4, nuit féerique en bivouac sous la Voie lactée et petit-déjeuner face aux dunes.</li>
    <li><strong>Aventure 3 Jours / 2 Nuits (230&euro; standard / 190&euro; groupe 4+):</strong> Randonnée chamelière approfondie, oasis secrètes et immersion totale chez les nomades.</li>
</ol>
<p>Pour réserver votre expédition personnalisée, consultez nos <a href="https://irrikitourism.com/#packages">Packs Irriki Tourism</a> ou contactez notre guide directement par <a href="https://wa.me/212715131709">WhatsApp (+212 715 131 709)</a>.</p>
"""

# Embed authentic Sahara photo
sahara_pool = [
    ("https://irrikitourism.com/wp-content/uploads/2025/04/pexels-tomas-malik-793526-1703312-scaled.jpg", "Les grandes dunes dorées de l'Erg Chegaga"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/lac-iriqui.jpg", "Traversée du lac Iriki en 4x4"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/0c.jpg", "Immersion dans le désert marocain avec Irriki Tourism"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/1c01d87e253f9de742180a3b3e3ab5b1.jpg", "Bivouac traditionnel berbère sous les étoiles"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/Camel-Trekking-Tour.png", "Randonnée à dos de dromadaire au coucher du soleil"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/Quad-biking-marrakech.jpg", "Safari quad et 4x4 dans les dunes de Chegaga"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/stars.jpg", "Nuit étoilée et ciel pur du Sahara au bivouac")
]
chosen_img, img_alt = random.choice(sahara_pool)
photo_html = f'<figure style="margin: 2rem 0; text-align: center;"><img src="{chosen_img}" alt="{img_alt}" style="width: 100%; border-radius: 1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);" /><figcaption style="font-size: 0.85rem; color: #78716c; margin-top: 0.5rem; font-style: italic;">{img_alt} - Irriki Tourism</figcaption></figure>'

if "<h2>" in article_html:
    parts = article_html.split("<h2>", 1)
    article_html = parts[0] + photo_html + "<h2>" + parts[1]
else:
    article_html += photo_html

post_data = {
    "title": selected_topic,
    "content": article_html.strip(),
    "excerpt": article_excerpt.strip(),
    "status": "publish",
    "format": "standard"
}

print(f"\nPosting article to WordPress: {wp_api_endpoint}...")
res = requests.post(wp_api_endpoint, headers=headers, json=post_data, timeout=30)
print(f"WordPress Response Status Code: {res.status_code}")

if res.status_code in [200, 201]:
    post_info = res.json()
    print(f"\nSUCCESS! Post is LIVE at: {post_info.get('link', '')}")
    if topics:
        remaining_topics = topics[1:]
        with open(TOPICS_FILE, "w", encoding="utf-8") as f:
            for t in remaining_topics:
                f.write(t + "\n")
        with open(USED_TOPICS_FILE, "a", encoding="utf-8") as f:
            f.write(selected_topic + "\n")
        print("Updated topics list successfully.")
else:
    print(f"Error publishing post: {res.text}")
    exit(1)
