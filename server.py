from flask import Flask, jsonify, send_from_directory
import json
import os
import threading
import time
import requests
import yfinance as yf
import aggregator

try:
    import anthropic
    ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
except Exception:
    ANTHROPIC_CLIENT = None

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

def generate_brief():
    if not ANTHROPIC_CLIENT:
        print("[BRIEF] No Anthropic API key — skipping")
        return
    try:
        with open(HEADLINES_FILE, "r", encoding="utf-8") as f:
            headlines = json.load(f)
    except:
        return
    from datetime import datetime, timezone
    cutoff_dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_str = cutoff_dt.strftime("%Y-%m-%dT")
    recent = [h for h in headlines if h.get("published", "") >= cutoff_str]
    if len(recent) < 5:
        return
    # Build digest: group by tier, pick top headlines
    tiers = {}
    for h in recent:
        t = h.get("tier","other")
        if t not in tiers: tiers[t] = []
        tiers[t].append(h["title"])
    digest_parts = []
    for tier, titles in tiers.items():
        digest_parts.append(f"[{tier.upper()}]\n" + "\n".join(f"- {t}" for t in titles[:15]))
    digest = "\n\n".join(digest_parts)
    prompt = f"""You are a geopolitical intelligence analyst. Based on the following news headlines from the last 24 hours about Iran, write a concise strategic brief of 4-6 sentences maximum.

Cover: (1) the most significant development today, (2) key official positions and any shifts, (3) market/economic angle if relevant, (4) your escalation assessment (low/medium/high/critical) with one sentence of reasoning.

Be direct and factual. No filler. Write for a senior analyst audience.

HEADLINES:
{digest}

BRIEF:"""
    try:
        msg = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = msg.content[0].text.strip()
        result = {
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z"),
            "headline_count": len(recent)
        }
        with open(BRIEF_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        print(f"[BRIEF] Generated — {len(recent)} headlines → {len(summary)} chars")
    except Exception as e:
        print(f"[BRIEF] Error: {e}")

def brief_loop():
    time.sleep(30)  # wait for aggregator first cycle
    while True:
        generate_brief()
        time.sleep(3600)  # regenerate every hour

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