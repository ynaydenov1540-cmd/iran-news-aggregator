from flask import Flask, jsonify, send_from_directory
import json
import os
import threading
import requests
import yfinance as yf
import aggregator

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))