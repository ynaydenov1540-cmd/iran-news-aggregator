import feedparser
import requests
import json
import os
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HEADLINES_FILE = os.path.join(BASE_DIR, "headlines.json")

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
    "isfahan", "mashhad", "hormuz", "pezeshkian", "pahlavi",
    "nuclear", "sanctions", "enrichment", "uranium", "jcpoa",
    "hezbollah", "houthi", "missile", "proxy", "strait of hormuz",
    "nuclear deal", "nuclear program", "nuclear talks", "nuclear weapon",
    "us-iran", "israel-iran", "iran talks", "iran deal", "iran nuclear",
    "iaea", "non-proliferation", "atomic", "centrifuge",
    "revolutionary guard", "quds force", "axis of resistance",
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

def fetch_one_feed(feed, tier):
    results = []
    try:
        resp = requests.get(feed["url"], headers={"User-Agent": feedparser.USER_AGENT}, timeout=8)
        parsed = feedparser.parse(resp.content)
        for entry in parsed.entries[:20]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            if is_relevant(title):
                item = {
                    "source": feed["name"],
                    "title": title,
                    "link": link,
                    "published": parse_time(entry),
                    "tier": tier
                }
                if tier == "official":
                    item["pos_score"] = position_score(title)
                results.append(item)
    except Exception as e:
        print(f"Error fetching {feed['name']}: {e}")
    return results

def fetch_from_feeds(feeds, tier):
    headlines = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_one_feed, feed, tier): feed for feed in feeds}
        for f in as_completed(futures):
            headlines.extend(f.result())
    return headlines

REDDIT_ECON_SUBS_SET = {"wallstreetbets", "investing"}

def fetch_reddit():
    headlines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
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
        with open(os.path.join(BASE_DIR, "iran_sources.json"), "r", encoding="utf-8") as f:
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
        with open(os.path.join(BASE_DIR, "telegram_feeds_config.json"), "r", encoding="utf-8") as f:
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
                # Skip non-English posts: if >30% of letters are non-Latin (Cyrillic, Arabic, etc.) drop it
                letters = [c for c in text if c.isalpha()]
                if letters:
                    non_latin = sum(1 for c in letters if ord(c) > 0x024F)
                    if non_latin / len(letters) > 0.3:
                        continue
                # ALL channels must be Iran-relevant — official channels included
                if not any(k in text.lower() for k in IRAN_TELEGRAM_KEYWORDS):
                    continue
                dt_raw = time_el.get("datetime", "") if time_el else ""
                published = (dt_raw[:19] + "Z") if dt_raw else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z")
                link = link_el.get("href", "") if link_el else ""
                tier = "official" if ch.get("view") == "official" else "telegram"
                item = {
                    "source": title,
                    "title": text,
                    "link": link,
                    "published": published,
                    "tier": tier
                }
                if tier == "official":
                    item["pos_score"] = position_score(text)
                headlines.append(item)
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
    with open(HEADLINES_FILE, "w", encoding="utf-8") as f:
        json.dump(headlines, f, ensure_ascii=False, indent=2)
    counts = {}
    for h in headlines:
        counts[h["tier"]] = counts.get(h["tier"], 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in counts.items())
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved {len(headlines)} headlines — {summary}")

# Position-language keywords — used to score and rank official statements
POSITION_KEYWORDS = [
    "condemns","condemned","warns","warned","threatens","threatened","vows","pledged",
    "backs","backs down","supports","supported","opposes","opposed","rejects","rejected",
    "calls for","urges","urged","demands","demanded","insists","insisting",
    "sanctions","sanction","nuclear deal","ceasefire","military","strike","attack",
    "will not","will never","must","must not","should","should not",
    "ready to","prepared to","committed to","determined to",
    "response","retaliation","deterrence","offensive","defensive",
    "agreement","violation","breach","non-compliance","enrichment","uranium",
    "red line","ultimatum","negotiate","talks","deal","treaty","accord",
    "force","action","option","consequence","pressure","escalate","de-escalate",
    "right to","obligation","responsibility","accountability",
]

def position_score(title):
    t = title.lower()
    return sum(1 for k in POSITION_KEYWORDS if k in t)

OFFICIAL_FEEDS = [
    # USA — Google News search + direct RSS
    {"name": "US State Dept",       "url": "https://www.state.gov/rss-feeds/press-releases/"},
    {"name": "US State Dept",       "url": "https://news.google.com/rss/search?q=iran+(warns+OR+urges+OR+sanctions+OR+nuclear+OR+condemns+OR+demands+OR+military)+site:state.gov&hl=en-US&gl=US&ceid=US:en"},
    {"name": "White House",         "url": "https://www.whitehouse.gov/feed/"},
    {"name": "White House",         "url": "https://news.google.com/rss/search?q=iran+(warns+OR+urges+OR+sanctions+OR+nuclear+OR+condemns+OR+military)+site:whitehouse.gov&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Pentagon",            "url": "https://news.google.com/rss/search?q=iran+(threat+OR+military+OR+strike+OR+force+OR+deterrence+OR+warns)+site:defense.gov&hl=en-US&gl=US&ceid=US:en"},
    # UK — direct FCDO Atom feed (most reliable)
    {"name": "UK Foreign Office",   "url": "https://www.gov.uk/search/news-and-communications.atom?keywords=iran&organisations[]=foreign-commonwealth-development-office"},
    {"name": "UK Foreign Office",   "url": "https://www.gov.uk/search/news-and-communications.atom?organisations[]=foreign-commonwealth-development-office"},
    # EU / Europe — direct feeds
    {"name": "EU Council",          "url": "https://www.consilium.europa.eu/en/feed/?feedId=news&mediaTypes=text,audio,video&lang=en"},
    {"name": "EU Council",          "url": "https://news.google.com/rss/search?q=iran+(sanctions+OR+nuclear+OR+condemns+OR+urges+OR+position+OR+statement)+site:consilium.europa.eu&hl=en-US&gl=US&ceid=US:en"},
    {"name": "European Commission", "url": "https://ec.europa.eu/commission/presscorner/api/rss"},
    {"name": "European Commission", "url": "https://news.google.com/rss/search?q=iran+(sanctions+OR+nuclear+OR+condemns+OR+urges+OR+statement)+site:ec.europa.eu&hl=en-US&gl=US&ceid=US:en"},
    {"name": "French MFA",          "url": "https://www.diplomatie.gouv.fr/spip.php?page=backend-dirco&lang=en"},
    {"name": "French MFA",          "url": "https://news.google.com/rss/search?q=iran+(position+OR+condemns+OR+nuclear+OR+sanctions+OR+urges)+site:diplomatie.gouv.fr&hl=en-US&gl=US&ceid=US:en"},
    {"name": "German Foreign Ministry", "url": "https://news.google.com/rss/search?q=iran+(position+OR+condemns+OR+nuclear+OR+sanctions+OR+urges)+site:auswaertiges-amt.de&hl=en-US&gl=US&ceid=US:en"},
    # Russia
    {"name": "Russian MFA",         "url": "https://mid.ru/en/rss/"},
    {"name": "Russian MFA",         "url": "https://news.google.com/rss/search?q=iran+(backs+OR+supports+OR+position+OR+nuclear+OR+warns+OR+rejects)+site:mid.ru&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Kremlin",             "url": "http://en.kremlin.ru/events/president/news/feed"},
    {"name": "Kremlin",             "url": "https://news.google.com/rss/search?q=iran+(backs+OR+supports+OR+nuclear+OR+military+OR+warns)+site:en.kremlin.ru&hl=en-US&gl=US&ceid=US:en"},
    # China
    {"name": "Chinese MFA",         "url": "https://news.google.com/rss/search?q=iran+(position+OR+opposes+OR+supports+OR+nuclear+OR+sanctions+OR+urges)+site:mfa.gov.cn&hl=en-US&gl=US&ceid=US:en"},
    # Israel
    {"name": "Israel MFA",          "url": "https://news.google.com/rss/search?q=iran+(threat+OR+nuclear+OR+warns+OR+condemns+OR+military+OR+attack+OR+strikes)+site:mfa.gov.il&hl=en-US&gl=US&ceid=US:en"},
    {"name": "IDF Spokesperson",    "url": "https://news.google.com/rss/search?q=iran+(threat+OR+military+OR+strike+OR+attack+OR+warns+OR+deterrence)+site:idf.il&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Israel PM Office",    "url": "https://news.google.com/rss/search?q=iran+(threat+OR+nuclear+OR+warns+OR+strike+OR+attack+OR+red+line+OR+military+OR+condemns)+site:pmo.gov.il&hl=en-US&gl=US&ceid=US:en"},
    # Middle East
    {"name": "Saudi MFA",           "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+threat+OR+sanctions+OR+urges+OR+position+OR+warns)+site:mofa.gov.sa&hl=en-US&gl=US&ceid=US:en"},
    {"name": "UAE MFA",             "url": "https://news.google.com/rss/search?q=iran+(position+OR+nuclear+OR+sanctions+OR+threat+OR+warns)+site:mofaic.gov.ae&hl=en-US&gl=US&ceid=US:en"},
    # Iran
    {"name": "Iran MFA",            "url": "https://news.google.com/rss/search?q=(nuclear+OR+sanctions+OR+response+OR+rejects+OR+warns+OR+demands)+site:mfa.ir&hl=en-US&gl=US&ceid=US:en"},
    {"name": "IRNA Official",       "url": "https://en.irna.ir/rss"},
    {"name": "IRNA Official",       "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+sanctions+OR+rejects+OR+warns+OR+demands+OR+response)+site:irna.ir&hl=en-US&gl=US&ceid=US:en"},
    # Asia
    {"name": "India MEA",           "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+sanctions+OR+urges+OR+position+OR+condemns)+site:mea.gov.in&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Pakistan MFA",        "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+urges+OR+position+OR+condemns+OR+backs+OR+relations)+site:mofa.gov.pk&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Japan MOFA",          "url": "https://www.mofa.go.jp/mofaj/rss/en/press.xml"},
    {"name": "Japan MOFA",          "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+sanctions+OR+urges+OR+condemns+OR+concern)+site:mofa.go.jp&hl=en-US&gl=US&ceid=US:en"},
    # Ukraine
    {"name": "Ukraine MFA",         "url": "https://news.google.com/rss/search?q=iran+(weapons+OR+condemns+OR+backs+OR+sanctions+OR+military)+site:mfa.gov.ua&hl=en-US&gl=US&ceid=US:en"},
    # International — direct feeds (most reliable)
    {"name": "IAEA",                "url": "https://www.iaea.org/feeds/topnews.xml"},
    {"name": "IAEA",                "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+enrichment+OR+uranium+OR+compliance+OR+violation+OR+inspections)+site:iaea.org&hl=en-US&gl=US&ceid=US:en"},
    {"name": "UN News",             "url": "https://news.un.org/feed/subscribe/en/news/topic/international-law/feed/rss.xml"},
    {"name": "UN News",             "url": "https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml"},
    {"name": "UN News",             "url": "https://news.google.com/rss/search?q=iran+(nuclear+OR+sanctions+OR+condemns+OR+urges+OR+resolution+OR+military)+site:news.un.org&hl=en-US&gl=US&ceid=US:en"},
    {"name": "NATO",                "url": "https://www.nato.int/cps/en/natohq/news.htm?selectedLocale=en&format=RSS"},
    {"name": "NATO",                "url": "https://news.google.com/rss/search?q=iran+(threat+OR+nuclear+OR+military+OR+warns+OR+deterrence)+site:nato.int&hl=en-US&gl=US&ceid=US:en"},
    # Turkey
    {"name": "Turkish MFA",         "url": "https://news.google.com/rss/search?q=iran+(position+OR+nuclear+OR+condemns+OR+urges+OR+warns+OR+sanctions+OR+mediat)+site:mfa.gov.tr&hl=en-US&gl=US&ceid=US:en"},
]

def run():
    print("Starting Iran War Watch Aggregator...")
    rss_headlines = []
    official_headlines = []
    last_rss = 0
    last_official = 0

    while True:
        try:
            now = time.time()
            # Refresh main RSS every 5 minutes
            if now - last_rss >= 300:
                iran_feeds = load_iran_sources()
                rss_headlines = (
                    fetch_from_feeds(BIG_FEEDS, "big") +
                    fetch_from_feeds(BREAKING_FEEDS + iran_feeds, "breaking")
                )
                last_rss = now

            # Refresh official positions (RSS + Telegram) every 5 minutes independently
            if now - last_official >= 300:
                official_headlines = (
                    fetch_from_feeds(OFFICIAL_FEEDS, "official") +
                    fetch_telegram()
                )
                last_official = now

            all_headlines = rss_headlines + official_headlines
            seen = set()
            unique = []
            for h in all_headlines:
                if h["title"] not in seen:
                    seen.add(h["title"])
                    unique.append(h)
            unique.sort(key=lambda x: x["published"], reverse=True)
            print(f"[CYCLE] RSS: {len(rss_headlines)}, Total unique: {len(unique)}")
            save(unique)

        except Exception as e:
            print(f"[ERROR] Main loop: {e}")

        time.sleep(30)

if __name__ == "__main__":
    run()