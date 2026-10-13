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

wp_api_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
clean_password = WP_APP_PASSWORD.replace(" ", "")
credentials = f"{WP_USERNAME}:{clean_password}"
token = base64.b64encode(credentials.encode()).decode("utf-8")

headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Check if a post was already published today (UTC date) so multiple cron slots guarantee 1 post/day
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
if not FORCE_POST:
    try:
        recent_res = requests.get(f"{wp_api_endpoint}?per_page=1", headers=headers, timeout=15)
        if recent_res.status_code == 200 and len(recent_res.json()) > 0:
            latest_post_date = recent_res.json()[0].get("date_gmt", "")[:10]
            if latest_post_date == today_str:
                print(f"A blog post was already published today ({today_str}). Exiting cleanly.")
                exit(0)
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
    selected_topic = "Ultimate Sahara Desert Tour from Foum Zguid to Lake Iriki"
else:
    selected_topic = topics[0]

print(f"\nProcessing Topic: '{selected_topic}'")

# Organic randomized delay (10 to 45 seconds)
delay_seconds = random.randint(10, 45)
print(f"Applying organic delay of {delay_seconds} seconds...")
time.sleep(delay_seconds)

article_html = None
article_excerpt = None

CUSTOM_TOPIC_GUIDES = {
    "Best Sahara Desert Tour from Foum Zguid (2026 Complete Guide)": {
        "excerpt": "Planning a Sahara desert adventure in southern Morocco? Discover why Foum Zguid and Lake Iriki offer the most authentic 4x4, camel trekking, and Berber camp experience in 2026.",
        "content": """
<p>Located at the southern edge of the Anti-Atlas mountains, <strong>Foum Zguid</strong> is the premier gateway to the untouched expanses of the Moroccan Sahara. Unlike crowded commercial dunes, embarking on the <strong>Best Sahara Desert Tour from Foum Zguid</strong> with <a href="https://irrikitourism.com/#packages">Irriki Tourism</a> takes you along legendary Paris-Dakar tracks across stony hamadas, fossil-rich plateaus, and the vast salt flats of <strong>Lake Iriki</strong> to golden sand dunes.</p>
<h2>Why Start Your Sahara Expedition in Foum Zguid?</h2>
<ul>
    <li><strong>Authentic Unspoiled Wilderness:</strong> Experience total desert silence across Iriki National Park without mass tourism crowds.</li>
    <li><strong>Diverse Landscapes in One Journey:</strong> Traverse dramatic rocky plateaus, prehistoric trilobite fossil beds, the dry salt lake of Iriki, and towering golden dunes.</li>
    <li><strong>Genuine Nomadic &amp; Berber Hospitality:</strong> Share traditional Moroccan mint tea, fresh sand-baked bread (Mella), and slow-cooked tagines around the campfire.</li>
</ul>
<h2>Top Tour Packages from Foum Zguid</h2>
<p>Whether you have a single day or several nights, <a href="https://irrikitourism.com/#packages">Irriki Tourism</a> offers tailored desert packages:</p>
<ol>
    <li><strong>IRIKI 1-Day Experience (150&euro; / 120&euro; group):</strong> Full-day 4x4 adventure from Foum Zguid via Ajermia and dry Lake Iriki to the dunes for sandboarding and sunset views.</li>
    <li><strong>Iriki 2-Day / 1-Night Experience (160&euro; / 130&euro; group):</strong> Combine prehistoric rock carvings and fossil discovery with a 4x4 dune safari and an overnight stay with warm traditional meals.</li>
    <li><strong>Iriki 3-Day / 2-Night Camel &amp; Oasis Adventure (230&euro; / 190&euro; group):</strong> Multi-day camel trek deep into the dunes, sleeping under the Sahara stars and camping near a hidden desert oasis.</li>
</ol>
<p>Ready to plan your departure? Contact our local Foum Zguid guides directly via <a href="https://wa.me/212715131709">WhatsApp (+212 715 131 709)</a> or explore our packages at <a href="https://irrikitourism.com/">irrikitourism.com</a>!</p>
"""
    },
    "Lake Iriki National Park: 4x4 Off-Road Expedition & Fossil Hunting Guide": {
        "excerpt": "Explore the shimmering salt flats, prehistoric marine fossils, and towering sand dunes of Lake Iriki National Park on a guided 4x4 off-road expedition with Irriki Tourism.",
        "content": """
<p>Stretching between the Draa River valley and the foothills of the Anti-Atlas near Foum Zguid, <strong>Lake Iriki National Park</strong> is one of southern Morocco's most dramatic natural wonders. Once a vast prehistoric sea and later a seasonal wetland, the dry lakebed of <strong>Iriki</strong> now blends endless white-gold salt flats with rolling Sahara dunes.</p>
<h2>What You Will See on a Lake Iriki 4x4 Expedition</h2>
<ul>
    <li><strong>Prehistoric Trilobite &amp; Orthoceras Fossils:</strong> Millions of years ago, the Sahara lay beneath the Paleozoic ocean. Along the rocky ridges between Foum Zguid and Ajermia, you can spot ancient marine fossils embedded directly in the stone.</li>
    <li><strong>The Endless Mirror of Dry Lake Iriki:</strong> Crossing the flat chott (dry salt lake) in a 4x4 offers surreal desert mirages and 360-degree horizons.</li>
    <li><strong>Golden Dunes &amp; Sunset Sandboarding:</strong> At the edge of Lake Iriki rise untouched dunes ideal for sandboarding, camel rides, and golden-hour photography.</li>
</ul>
<h2>Book Your Guided 4x4 Expedition</h2>
<p>All <a href="https://irrikitourism.com/#packages">Irriki Tourism</a> 4x4 tours are led by experienced native Sahara drivers born in the region. Book your 1-day, 2-day, or 3-day excursion today at <a href="https://irrikitourism.com/">irrikitourism.com</a> or message us on <a href="https://wa.me/212715131709">WhatsApp</a>.</p>
"""
    }
}

if selected_topic in CUSTOM_TOPIC_GUIDES:
    article_excerpt = CUSTOM_TOPIC_GUIDES[selected_topic]["excerpt"]
    article_html = CUSTOM_TOPIC_GUIDES[selected_topic]["content"].strip()

system_prompt = (
    "You are an expert Morocco travel writer and Sahara desert expedition guide writing for 'Irriki Tourism' (https://irrikitourism.com), "
    "based in Foum Zguid / Lake Iriki, southern Morocco. "
    "Write an engaging, practical, 900-word SEO-optimized travel blog post in English that focuses 100% on the exact title provided. "
    "Format in clean semantic HTML using <p>, <h2>, <h3>, <ul>, <li>, and <strong> tags (do NOT include <h1> or markdown code fences). "
    "Naturally mention Irriki Tourism's offerings where relevant: 4x4 desert tours from Foum Zguid, Lake Iriki excursions, camel trekking, "
    "quad biking, sandboarding, stargazing, and traditional Berber desert camp (1-Day tour 150€, 2-Day tour 160€, 3-Day tour 230€, WhatsApp +212 715 131 709). "
    "The very first <p> paragraph MUST be a compelling 2-sentence summary specifically tailored to the topic."
)
user_prompt = f"Write a comprehensive, SEO-optimized Morocco Sahara travel guide titled: '{selected_topic}'."

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
    article_excerpt = f"Plan your unforgettable Moroccan Sahara adventure with our complete guide to {selected_topic}. Discover local tips from Irriki Tourism in Foum Zguid & Lake Iriki."
    article_html = f"""
<p>Venturing into the golden dunes and vast salt flats of southern Morocco is a bucket-list journey for travelers seeking raw natural beauty and cultural authenticity. In this detailed Sahara travel guide to <strong>{selected_topic}</strong>, our local desert team at <a href="https://irrikitourism.com/">Irriki Tourism</a> shares everything you need to know before setting off from Foum Zguid toward Lake Iriki.</p>
<h2>What Makes Lake Iriki &amp; Foum Zguid So Special?</h2>
<p>Situated between the Anti-Atlas mountains and the great Erg Chigaga dune sea, the Lake Iriki region combines dramatic rocky hamadas, ancient prehistoric fossil beds, and tranquil golden sand dunes far from mass-tourism routes.</p>
<ul>
    <li><strong>4x4 Off-Road Desert Expeditions:</strong> Follow historic rally tracks across dry Lake Iriki with experienced native Sahara drivers.</li>
    <li><strong>Sunset Camel Trekking &amp; Sandboarding:</strong> Ride across the dunes at golden hour or carve down steep desert slopes on a sandboard.</li>
    <li><strong>Authentic Berber Bivouac Camp:</strong> Sleep in cozy traditional Berber tents (1 to 4 guests per tent) with all Moroccan meals included and crystal-clear Sahara stargazing.</li>
</ul>
<h2>Choose Your Ideal Sahara Tour Package</h2>
<ol>
    <li><strong>IRIKI 1-Day Experience (150&euro; standard / 120&euro; group of 4+):</strong> A full day exploring Foum Zguid, Ajermia, dry Lake Iriki, and sunset dunes.</li>
    <li><strong>Iriki 2-Day / 1-Night Experience (160&euro; standard / 130&euro; group of 4+):</strong> Ancient rock carvings, overnight desert hospitality, and a thrilling 4x4 dune safari.</li>
    <li><strong>Iriki 3-Day / 2-Night Adventure (230&euro; standard / 190&euro; group of 4+):</strong> Deep Sahara camel trekking, oasis camping, and panoramic desert viewpoints.</li>
</ol>
<p>Ready to experience the magic of the Moroccan Sahara? Visit <a href="https://irrikitourism.com/#packages">Irriki Tourism Packages</a> or message our team directly on <a href="https://wa.me/212715131709">WhatsApp (+212 715 131 709)</a> to customize your trip!</p>
"""

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
