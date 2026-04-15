from flask import Flask, jsonify, send_from_directory
import json
import os
import threading
import time
import requests
import yfinance as yf
import aggregator

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRIEF_FILE = os.path.join(BASE_DIR, "brief.json")
HEADLINES_FILE = os.path.join(BASE_DIR, "headlines.json")

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route("/markets.html")
def markets_page():
    return send_from_directory(BASE_DIR, "markets.html")

@app.route("/widget.html")
def widget():
    return send_from_directory(BASE_DIR, "widget.html")

@app.route("/headlines")
def headlines():
    try:
        with open(os.path.join(BASE_DIR, "headlines.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify([])

@app.route("/markets")
def markets():
    symbols = [
        "GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "USO", "BNO",
        "BTC-USD", "SPY", "QQQ", "XOM", "CVX", "RTX", "LMT", "UAL", "LUV",
        "UUP", "ALI=F", "ZC=F", "HG=F", "DX-Y.NYB", "^TNX", "^VIX",
    ]
    results = {}
    for sym in symbols:
        try:
            info = yf.Ticker(sym).fast_info
            price = round(float(info.last_price), 4)
            prev  = round(float(info.previous_close), 4)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else None
            results[sym] = {"price": price, "change": chg}
        except Exception as e:
            print(f"Error fetching {sym}: {e}")
            results[sym] = {"price": None, "change": None}
    return jsonify(results)

@app.route("/brief")
def brief():
    try:
        with open(BRIEF_FILE, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"summary": None, "generated_at": None})

@app.route("/brief/generate")
def brief_now():
    threading.Thread(target=generate_brief, daemon=True).start()
    return jsonify({"status": "generating — refresh /brief in 15 seconds"})

def generate_brief():
    if not GROQ_API_KEY:
        print("[BRIEF] No GROQ_API_KEY set — skipping")
        return
    from datetime import datetime, timezone
    try:
        with open(HEADLINES_FILE, "r", encoding="utf-8") as f:
            headlines = json.load(f)
    except Exception as e:
        print(f"[BRIEF] Could not read headlines: {e}")
        return
    # Use rolling 24h window, not UTC midnight (more reliable on fresh deploys)
    cutoff_ts = datetime.now(timezone.utc).timestamp() - 24 * 3600
    recent = []
    for h in headlines:
        pub = h.get("published", "")
        try:
            pub_ts = datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp()
            if pub_ts >= cutoff_ts:
                recent.append(h)
        except Exception:
            pass
    # Fall back to all headlines if 24h window is too narrow (e.g. fresh deploy)
    if len(recent) < 10:
        recent = headlines[:100]
    if len(recent) < 5:
        print(f"[BRIEF] Too few headlines ({len(recent)}) — skipping")
        return
    # Build digest grouped by tier
    tiers = {}
    for h in recent:
        t = h.get("tier", "other")
        tiers.setdefault(t, []).append(h["title"])
    digest = "\n\n".join(
        f"[{t.upper()}]\n" + "\n".join(f"- {title}" for title in titles[:15])
        for t, titles in tiers.items()
    )
    prompt = (
        "You are a geopolitical intelligence analyst. Based on these Iran-related news headlines from today, "
        "write a concise strategic brief of 4-6 sentences.\n\n"
        "Cover: (1) most significant development, (2) key official positions/shifts, "
        "(3) market/economic angle if relevant, (4) escalation assessment: LOW / MEDIUM / HIGH / CRITICAL with one sentence of reasoning.\n\n"
        "Be direct and factual. No filler. Senior analyst audience.\n\n"
        f"HEADLINES:\n{digest}\n\nBRIEF:"
    )
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 350, "temperature": 0.4},
            timeout=30
        )
        resp.raise_for_status()
        summary = resp.json()["choices"][0]["message"]["content"].strip()
        result = {
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"),
            "headline_count": len(recent)
        }
        with open(BRIEF_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        print(f"[BRIEF] Generated via Groq — {len(recent)} headlines → {len(summary)} chars")
    except Exception as e:
        print(f"[BRIEF] Error: {e}")

def brief_loop():
    # Wait for aggregator to complete its first full cycle
    time.sleep(120)
    generate_brief()
    while True:
        time.sleep(3600)
        generate_brief()

@app.route("/polymarket")
def polymarket():
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets?limit=50&active=true",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        data = r.json()
        iran_markets = [
            m for m in data
            if m.get("question") and any(k in m["question"].lower()
               for k in ["iran", "nuclear", "sanctions", "tehran", "irgc", "israel"])
        ][:6]
        results = []
        for m in iran_markets:
            try:
                odds = round(float(json.loads(m["outcomePrices"])[0]) * 100)
            except:
                odds = None
            results.append({
                "question": m["question"],
                "odds": odds
            })
        return jsonify(results)
    except Exception as e:
        print(f"Polymarket error: {e}")
        return jsonify([])

if __name__ == "__main__":
    threading.Thread(target=aggregator.run, daemon=True).start()
    threading.Thread(target=brief_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))