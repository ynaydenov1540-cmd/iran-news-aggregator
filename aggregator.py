import feedparser
import requests
import json
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BIG_FEEDS = [
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "CNN", "url": "http://rss.cnn.com/rss/edition_world.rss"},
    {"name": "Google News", "url": "https://news.google.com/rss/search?q=iran&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Financial Times", "url": "https://www.ft.com/world?format=rss"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/iran/rss"},
    {"name": "Reuters", "url": "https://feeds.reuters.com/reuters/topNews"},
    {"name": "Foreign Policy", "url": "https://foreignpolicy.com/feed"},
]

BREAKING_FEEDS = [
    # US / UK
    {"name": "AP News", "url": "https://news.google.com/rss/search?q=iran+site:apnews.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "NPR World", "url": "https://feeds.npr.org/1004/rss.xml"},
    {"name": "Fox News", "url": "https://moxie.foxnews.com/google-publisher/world.xml"},
    {"name": "The Telegraph", "url": "https://www.telegraph.co.uk/rss.xml"},
    {"name": "Middle East Eye", "url": "https://www.middleeasteye.net/rss"},
    {"name": "The Nation", "url": "https://www.thenation.com/feed"},
    # Middle East
    {"name": "Arab News", "url": "https://www.arabnews.com/rss.xml"},
    {"name": "Al Arabiya", "url": "https://english.alarabiya.net/tools/mrss"},
    {"name": "Saudi Press Agency", "url": "https://www.spa.gov.sa/en/rss"},
    {"name": "Arabian Business", "url": "https://www.arabianbusiness.com/rss"},
    {"name": "Saudi Gazette", "url": "https://www.saudigazette.com.sa/rss.xml"},
    {"name": "The National UAE", "url": "https://www.thenationalnews.com/rss.xml"},
    {"name": "Gulf News", "url": "https://gulfnews.com/rss"},
    {"name": "Khaleej Times", "url": "https://www.khaleejtimes.com/rss"},
    {"name": "Gulf Daily News", "url": "https://news.google.com/rss/search?q=iran+site:gulf-daily-news.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Daily Tribune Bahrain", "url": "https://news.google.com/rss/search?q=iran+site:dt.bh&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Times of Oman", "url": "https://news.google.com/rss/search?q=iran+site:timesofoman.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Jordan Times", "url": "https://news.google.com/rss/search?q=iran+site:jordantimes.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Roya News", "url": "https://en.roya.news/feed"},
    {"name": "Anadolu Agency", "url": "https://www.aa.com.tr/en/rss/default"},
    # Iran specific / state media
    {"name": "Iran International", "url": "https://www.iranintl.com/en/rss"},
    {"name": "Iran International", "url": "https://news.google.com/rss/search?q=iran+site:iranintl.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Radio Farda", "url": "https://www.radiofarda.com/api/zpqioyhmmv"},
    {"name": "Radio Farda", "url": "https://news.google.com/rss/search?q=iran+site:radiofarda.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Tehran Times", "url": "https://news.google.com/rss/search?q=iran+site:tehrantimes.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Press TV", "url": "https://news.google.com/rss/search?q=iran+site:presstv.ir&hl=en-US&gl=US&ceid=US:en"},
    # Russian perspective (via Google News)
    {"name": "TASS", "url": "https://news.google.com/rss/search?q=iran+site:tass.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "RT", "url": "https://news.google.com/rss/search?q=iran+site:rt.com&hl=en-US&gl=US&ceid=US:en"},
    # Europe
    {"name": "Euronews", "url": "https://feeds.feedburner.com/euronews/en/news/"},
    {"name": "Deutsche Welle", "url": "https://rss.dw.com/xml/rss-en-world"},
    {"name": "France 24", "url": "https://www.france24.com/en/rss"},
    {"name": "Brussels Times", "url": "https://www.brusselstimes.com/feed"},
    {"name": "Notes from Poland", "url": "https://notesfrompoland.com/feed"},
    {"name": "TVP World", "url": "https://tvpworld.com/feed"},
    {"name": "Novinite", "url": "https://www.novinite.com/rss"},
    {"name": "Novinite Bulgaria", "url": "https://www.novinite.com/rss"},
    {"name": "Slovak Spectator", "url": "https://spectator.sme.sk/rss"},
    {"name": "POLITICO Europe", "url": "https://www.politico.eu/feed/"},
    {"name": "Yle News", "url": "https://yle.fi/news/feed/rss"},
    {"name": "The Local Sweden", "url": "https://www.thelocal.se/feed"},
    {"name": "El Pais", "url": "https://news.google.com/rss/search?q=iran+site:elpais.com&hl=en-US&gl=US&ceid=US:en"},
    # Asia / Pacific — via Google News search (direct RSS dead/blocked)
    {"name": "Reuters", "url": "https://news.google.com/rss/search?q=iran+site:reuters.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "South China Morning Post", "url": "https://news.google.com/rss/search?q=iran+site:scmp.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Der Spiegel", "url": "https://news.google.com/rss/search?q=iran+site:spiegel.de&hl=en-US&gl=US&ceid=US:en"},
    {"name": "NHK World", "url": "https://news.google.com/rss/search?q=iran+site:nhk.or.jp&hl=en-US&gl=US&ceid=US:en"},
    {"name": "The Hindu", "url": "https://news.google.com/rss/search?q=iran+site:thehindu.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Korea Herald", "url": "https://news.google.com/rss/search?q=iran+site:koreaherald.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Dawn", "url": "https://news.google.com/rss/search?q=iran+site:dawn.com&hl=en-US&gl=US&ceid=US:en"},
    # OSINT / Investigative
    {"name": "Bellingcat", "url": "https://www.bellingcat.com/feed/"},
    # Additional US / Global
    {"name": "Al Jazeera", "url": "https://news.google.com/rss/search?q=iran+site:aljazeera.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Google News", "url": "https://news.google.com/rss/search?q=iran+diplomatic&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Newsweek", "url": "https://news.google.com/rss/search?q=iran+site:newsweek.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "The Hill", "url": "https://news.google.com/rss/search?q=iran+site:thehill.com&hl=en-US&gl=US&ceid=US:en"},
]

REDDIT_SUBS = [
    "worldnews", "geopolitics", "iran", "israel", "CombatFootage",
    "wallstreetbets", "investing",
    "CredibleDefense", "NeutralNews", "news", "IsraelPalestine", "europe", "iraq", "lebanon",
    "journalism", "UAE", "worldpolitics", "MiddleEast",
    "Tehran", "TelAviv", "baghdad", "dubai", "Bahrain",
    "politics", "TheFrontlineExchange",
]

KEYWORDS = [
    "iran", "tehran", "irgc", "khamenei", "persian", "iranian", "nuclear",
    "sanctions", "isfahan", "mashhad", "hormuz",
    "hegseth", "pezeshkian", "netanyahu", "pahlavi", "mojtaba",
]

IRAN_TELEGRAM_KEYWORDS = [
    "iran", "tehran", "irgc", "khamenei", "persian", "iranian",
    "isfahan", "mashhad", "hormuz", "pezeshkian", "pahlavi", "mojtaba",
    "nuclear", "sanctions", "enrichment", "uranium", "jcpoa",
    "hezbollah", "houthi", "missile", "tabriz", "proxy", "strait",
    "middle east", "gulf", "security council", "diplomacy",
]

def is_relevant(text):
    return any(k in text.lower() for k in KEYWORDS)

def parse_time(entry):
    for field in ["published", "updated"]:
        val = entry.get(field, "")
        if val:
            try:
                return parsedate_to_datetime(val).strftime("%Y-%m-%dT%H:%M:00Z")
            except:
                pass
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z")

def fetch_from_feeds(feeds, tier):
    headlines = []
    for feed in feeds:
        try:
            try:
                resp = requests.get(feed["url"], headers={"User-Agent": feedparser.USER_AGENT}, timeout=10)
                parsed = feedparser.parse(resp.content)
            except:
                continue
            for entry in parsed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                if is_relevant(title):
                    headlines.append({
                        "source": feed["name"],
                        "title": title,
                        "link": link,
                        "published": parse_time(entry),
                        "tier": tier
                    })
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")
    return headlines

REDDIT_ECON_SUBS_SET = {"wallstreetbets", "investing"}

def fetch_reddit():
    headlines = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for sub in REDDIT_SUBS:
        try:
            if sub in REDDIT_ECON_SUBS_SET:
                url = f"https://www.reddit.com/r/{sub}/search.json?q=iran+OR+nuclear+OR+war+OR+oil+OR+sanctions&sort=new&t=week&limit=25&restrict_sr=1"
            else:
                url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            posts = r.json().get("data", {}).get("children", [])
            for post in posts:
                p = post.get("data", {})
                title = p.get("title", "").strip()
                link = "https://reddit.com" + p.get("permalink", "")
                created = p.get("created_utc", 0)
                published = datetime.utcfromtimestamp(created).strftime("%Y-%m-%dT%H:%M:00Z") if created else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z")
                headlines.append({
                        "source": f"r/{sub}",
                        "title": title,
                        "link": link,
                        "published": published,
                        "tier": "social"
                    })
        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")
    return headlines

def load_iran_sources():
    try:
        with open("iran_sources.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        existing_names = {feed["name"] for feed in BIG_FEEDS + BREAKING_FEEDS}
        extra = []
        for country in data.get("countries", []):
            for src in country.get("sources", []):
                if src.get("language", "").upper() != "EN":
                    continue
                if src.get("requires_translation", False):
                    continue
                name = src.get("name", "")
                if name in existing_names:
                    continue
                url = src.get("rss_url", "").strip()
                if not url.startswith("http"):
                    url = "https://" + url
                extra.append({"name": name, "url": url})
                print(f"  + {name}: {url}")
                existing_names.add(name)
        return extra
    except Exception as e:
        print(f"Could not load iran_sources.json: {e}")
        return []

def fetch_telegram():
    headlines = []
    try:
        with open("telegram_feeds_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Could not load telegram_feeds_config.json: {e}")
        return []
    headers = {"User-Agent": feedparser.USER_AGENT}
    for ch in config.get("channels", []):
        if not ch.get("enabled", True):
            continue
        if ch.get("language", "en") != "en":
            continue
        username = ch.get("username", "")
        title = ch.get("title", username)
        if not username:
            continue
        try:
            r = requests.get(f"https://t.me/s/{username}", headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for msg in soup.find_all("div", class_="tgme_widget_message")[-20:]:
                text_el = msg.find(class_="tgme_widget_message_text")
                time_el = msg.find("time")
                link_el = msg.find("a", class_="tgme_widget_message_date")
                if not text_el:
                    continue
                text = text_el.get_text(" ", strip=True)[:280]
                if not any(k in text.lower() for k in IRAN_TELEGRAM_KEYWORDS):
                    continue
                dt_raw = time_el.get("datetime", "") if time_el else ""
                published = (dt_raw[:19] + "Z") if dt_raw else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z")
                link = link_el.get("href", "") if link_el else ""
                headlines.append({
                    "source": title,
                    "title": text,
                    "link": link,
                    "published": published,
                    "tier": "telegram"
                })
        except Exception as e:
            print(f"Error fetching Telegram @{username}: {e}")
    return headlines

def fetch_all():
    iran_feeds = load_iran_sources()
    all_headlines = (
        fetch_from_feeds(BIG_FEEDS, "big") +
        fetch_from_feeds(BREAKING_FEEDS + iran_feeds, "breaking") +
        fetch_reddit() +
        fetch_telegram()
    )
    seen = set()
    unique = []
    for h in all_headlines:
        if h["title"] not in seen:
            seen.add(h["title"])
            unique.append(h)
    unique.sort(key=lambda x: x["published"], reverse=True)
    return unique

def save(headlines):
    with open("headlines.json", "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)
    counts = {}
    for h in headlines:
        counts[h["tier"]] = counts.get(h["tier"], 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in counts.items())
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved {len(headlines)} headlines — {summary}")

OFFICIAL_FEEDS = [
    {"name": "UK Foreign Office", "url": "https://www.gov.uk/search/news-and-communications.atom?keywords=iran&organisations[]=foreign-commonwealth-development-office"},
    {"name": "US State Dept",     "url": "https://news.google.com/rss/search?q=iran+site:state.gov&hl=en-US&gl=US&ceid=US:en"},
    {"name": "EU Council",        "url": "https://news.google.com/rss/search?q=iran+site:consilium.europa.eu&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Ukraine MFA",       "url": "https://news.google.com/rss/search?q=iran+site:mfa.gov.ua&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Russian MFA",       "url": "https://news.google.com/rss/search?q=iran+site:mid.ru&hl=en-US&gl=US&ceid=US:en"},
    {"name": "French MFA",        "url": "https://news.google.com/rss/search?q=iran+site:diplomatie.gouv.fr/en&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Saudi MFA",         "url": "https://news.google.com/rss/search?q=iran+site:mofa.gov.sa&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Kremlin",           "url": "https://news.google.com/rss/search?q=iran+site:en.kremlin.ru&hl=en-US&gl=US&ceid=US:en"},
    {"name": "IAEA",              "url": "https://news.google.com/rss/search?q=iran+site:iaea.org&hl=en-US&gl=US&ceid=US:en"},
]

def run():
    print("Starting Iran War Watch Aggregator...")
    rss_headlines = []
    last_rss = 0

    while True:
        try:
            now = time.time()
            # Refresh RSS + Telegram every 5 minutes
            if now - last_rss >= 300:
                iran_feeds = load_iran_sources()
                rss_headlines = (
                    fetch_from_feeds(BIG_FEEDS, "big") +
                    fetch_from_feeds(BREAKING_FEEDS + iran_feeds, "breaking") +
                    fetch_from_feeds(OFFICIAL_FEEDS, "telegram") +
                    fetch_telegram()
                )
                last_rss = now

            # Always fetch fresh Reddit (every 60s)
            reddit_headlines = fetch_reddit()

            all_headlines = rss_headlines + reddit_headlines
            seen = set()
            unique = []
            for h in all_headlines:
                if h["title"] not in seen:
                    seen.add(h["title"])
                    unique.append(h)
            unique.sort(key=lambda x: x["published"], reverse=True)
            print(f"[CYCLE] RSS: {len(rss_headlines)}, Reddit: {len(reddit_headlines)}, Total unique: {len(unique)}")
            save(unique)

        except Exception as e:
            print(f"[ERROR] Main loop: {e}")

        time.sleep(30)

if __name__ == "__main__":
    run()