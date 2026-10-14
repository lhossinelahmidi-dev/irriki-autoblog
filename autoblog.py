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

# Purge default demo posts or outdated non-relevant posts
try:
    print("Checking for demo or non-English posts to purge...")
    demo_check = requests.get(f"{wp_api_endpoint}&per_page=50", headers=headers, timeout=15)
    if demo_check.status_code == 200:
        demo_kws = [
            "clarity", "lessons learned", "creative living", "uncharted waters",
            "simple joys", "slowing down", "creative roadblocks", "daily habits", "hello world"
        ]
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
    selected_topic = "Erg Chegaga: The Ultimate Guide to Morocco's Wildest Desert Dunes (2026)"
else:
    selected_topic = topics[0]

print(f"\n==========================================")
print(f"Selected Topic: {selected_topic}")
print(f"Language: English (100% English Blog)")
print(f"==========================================\n")

# 3. Content Generation in 100% English
article_html = ""
article_excerpt = ""

system_prompt = (
    "You are an expert Moroccan Sahara travel SEO specialist and local expedition guide writing for 'Irriki Tourism' (https://irrikitourism.com), "
    "a top-rated local desert tour operator based in Foum Zguid, Lake Iriki, and Erg Chegaga in southern Morocco.\n"
    "Write an engaging, high-ranking, 950-word SEO-optimized travel blog post strictly in ENGLISH that targets high-intent search queries.\n"
    "Target Primary Keywords naturally: 'Erg Chegaga', 'Erg Chegaga desert tour', 'Bivouac Erg Chegaga', 'Chegaga dunes', '4x4 tour from Foum Zguid', 'Lake Iriki Morocco'.\n"
    "Structure requirements:\n"
    "1. The very first <p> must be a compelling 2-sentence hook with the target keyword in the first 100 words.\n"
    "2. Use <h2> and <h3> subheadings with keyword variations.\n"
    "3. Highlight Irriki Tourism's authentic packages: 1-Day Tour (from 120€), 2-Day / 1-Night Desert Bivouac (from 130€), and 3-Day Adventure (from 190€).\n"
    "4. End with an '<h2>Frequently Asked Questions</h2>' section containing 3 practical Q&As that travelers search on Google.\n"
    "5. Include clear calls to action pointing to https://irrikitourism.com/#packages and direct WhatsApp booking (+212 715 131 709).\n"
    "Format in clean semantic HTML with <p>, <h2>, <h3>, <ul>, <li>, and <strong> (no <h1> or markdown code fences)."
)
user_prompt = f"Write a comprehensive, keyword-optimized Sahara desert travel guide in English titled: '{selected_topic}'."

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

# Fallback: Rich English Sahara Travel Guide Generator
if not article_html or not article_excerpt:
    article_excerpt = f"Plan your unforgettable Moroccan Sahara adventure with our insider guide to {selected_topic}. Tips from local native desert guides at Irriki Tourism in Foum Zguid & Lake Iriki."
    article_html = f"""
<p>Venturing deep into the golden dunes and boundless desert landscapes of southern Morocco is an extraordinary journey. In this insider travel guide to <strong>{selected_topic}</strong>, our experienced desert team at <a href="https://irrikitourism.com/">Irriki Tourism</a> shares everything you need to know before departing Foum Zguid for the breathtaking dunes of Erg Chegaga and Lake Iriki.</p>
<h2>Why Choose Erg Chegaga and Foum Zguid?</h2>
<p>Situated between the rugged Anti-Atlas mountains and Morocco's highest rolling sea of sand, Erg Chegaga represents the untamed, authentic soul of the Sahara. Far from overcrowded tourist circuits, entering via Foum Zguid leads you across the dried prehistoric clay bed of Lake Iriki, renowned for ancient fossils, desert mirages, and historic Paris-Dakar rally tracks.</p>
<ul>
    <li><strong>Off-Road 4x4 Expeditions:</strong> Navigate stony desert plateaus (hamadas) and towering dunes with native Berber drivers who have navigated these sands for generations.</li>
    <li><strong>Traditional Berber Bivouac:</strong> Spend unforgettable nights in handcrafted nomad tents under a blanket of brilliant desert constellations, complete with homecooked tagines and campfire folklore.</li>
    <li><strong>Sunset Camel Treks &amp; Sandboarding:</strong> Ascend dune crests as the sun bathes the sand in crimson and gold, or glide down pristine 300-meter slopes on a sandboard.</li>
</ul>
<h2>Curated Irriki Tourism Desert Packages</h2>
<ol>
    <li><strong>1-Day Sahara Discovery (150&euro; standard / 120&euro; groups 4+):</strong> Crossing Foum Zguid, Ajermia, Lake Iriki, and reaching Erg Chegaga for golden sunset dunes.</li>
    <li><strong>2-Day / 1-Night Desert Bivouac (160&euro; standard / 130&euro; groups 4+):</strong> 4x4 wilderness crossing, campfire nomad music, overnight tent accommodation, and sunrise over the dunes.</li>
    <li><strong>3-Day / 2-Night Deep Desert Odyssey (230&euro; standard / 190&euro; groups 4+):</strong> Immersive camel trekking, remote oasis exploration, ancient petroglyphs, and full desert disconnection.</li>
</ol>
<p>Ready to experience the magic of the Moroccan desert? Discover our <a href="https://irrikitourism.com/#packages">Tour Packages</a> or message our local guides directly via <a href="https://wa.me/212715131709">WhatsApp (+212 715 131 709)</a>.</p>
"""

# Embed authentic Sahara photo with English caption
sahara_pool = [
    ("https://irrikitourism.com/wp-content/uploads/2025/04/pexels-tomas-malik-793526-1703312-scaled.jpg", "Golden sand dunes of Erg Chegaga at sunset"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/lac-iriqui.jpg", "4x4 desert crossing through Lake Iriki salt flats"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/0c.jpg", "Deep Sahara desert expedition with Irriki Tourism"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/1c01d87e253f9de742180a3b3e3ab5b1.jpg", "Traditional Berber bivouac camp under the Sahara stars"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/Camel-Trekking-Tour.png", "Sunset camel trekking across Erg Chegaga dunes"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/Quad-biking-marrakech.jpg", "Quad biking and 4x4 dune safari across Chegaga"),
    ("https://irrikitourism.com/wp-content/uploads/2025/04/stars.jpg", "Crystal-clear night sky and stargazing at Lake Iriki")
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

print(f"\nPosting English article to WordPress: {wp_api_endpoint}...")
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
