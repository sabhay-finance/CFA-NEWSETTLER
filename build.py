#!/usr/bin/env python3
"""
CFA SETTLER — GitHub Actions Build Script
Fetches news, extracts full text, and generates a static index.html.
"""

import datetime
import hashlib
import html as html_mod
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

import feedparser
import requests

IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")
MAX_AGE_HOURS = 48
FEED_TIMEOUT = 15
ARTICLE_TIMEOUT = 10

RSS_FEEDS = [
    ("CNBC World Economy",      "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"),
    ("CNBC Finance",            "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
    ("CNBC Top News",           "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Yahoo Finance",           "https://finance.yahoo.com/news/rssindex"),
    ("MarketWatch Top Stories", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("Investing.com News",      "https://www.investing.com/rss/news.rss"),
    ("FT Markets",              "https://www.ft.com/markets?format=rss"),
    ("ECB Press",               "https://www.ecb.europa.eu/rss/press.html"),
    ("Federal Reserve",         "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("Google News Business",    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"),
    ("Economic Times Markets",  "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Economic Times Economy",  "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms"),
    ("Moneycontrol Markets",    "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("LiveMint Money",          "https://www.livemint.com/rss/money"),
    ("LiveMint Markets",        "https://www.livemint.com/rss/markets"),
    ("NDTV Profit",             "https://feeds.feedburner.com/ndtvprofit-latest"),
]

CFA_TOPIC_KEYWORDS = {
    "Quantitative Methods": ["regression", "standard deviation", "probability", "hypothesis test", "correlation", "time value of money", "net present value", "npv", "internal rate of return", "irr", "discount rate", "compounding", "normal distribution", "sampling", "confidence interval", "z-score", "t-test", "bayes", "variance", "monte carlo", "statistical"],
    "Economics": ["gdp", "inflation", "deflation", "cpi", "consumer price", "interest rate", "monetary policy", "fiscal policy", "central bank", "recession", "economic growth", "unemployment", "trade deficit", "trade surplus", "current account", "balance of payments", "supply and demand", "aggregate demand", "aggregate supply", "exchange rate", "purchasing power", "stagflation", "quantitative easing", "rate hike", "rate cut", "repo rate", "federal funds", "rbi policy", "fed meeting", "fomc", "ecb rate", "boe rate", "tariff", "import duty", "export", "free trade", "wto", "economic indicator", "pmi", "manufacturing index", "services index", "wage growth", "cost of living", "disinflation", "hyperinflation"],
    "Financial Statement Analysis": ["earnings", "revenue", "profit", "loss", "balance sheet", "income statement", "cash flow statement", "10-k", "10-q", "annual report", "quarterly result", "ebitda", "eps", "earnings per share", "gross margin", "operating margin", "net income", "depreciation", "amortization", "goodwill", "impairment", "inventory", "receivables", "payables", "working capital", "roe", "roa", "return on equity", "return on assets", "financial ratio", "debt to equity", "current ratio", "quick ratio", "audit", "gaap", "ifrs", "accounting", "restatement", "write-off", "write-down", "provisions", "deferred tax", "fair value", "book value"],
    "Corporate Issuers": ["ipo", "buyback", "share repurchase", "capital structure", "dividend", "merger", "acquisition", "m&a", "takeover", "spin-off", "spinoff", "demerger", "corporate governance", "board of directors", "shareholder", "stakeholder", "proxy vote", "rights issue", "dilution", "leverage", "cost of capital", "wacc", "capital expenditure", "capex", "corporate action", "stock split", "bonus issue", "delisting", "listing", "restructuring", "bankruptcy", "insolvency"],
    "Equity Investments": ["stock market", "equity market", "share price", "market cap", "valuation", "p/e ratio", "price to earnings", "price to book", "sensex", "nifty", "s&p 500", "dow jones", "nasdaq", "ftse", "hang seng", "dax", "bull market", "bear market", "market rally", "market crash", "correction", "sector rotation", "growth stock", "value stock", "small cap", "mid cap", "large cap", "blue chip", "index fund", "stock index", "market breadth", "relative strength", "momentum", "beta", "alpha", "efficient market", "market efficiency", "fundamental analysis", "technical analysis", "stock exchange", "bse", "nse", "nyse"],
    "Fixed Income": ["bond", "treasury", "yield", "coupon", "maturity", "credit rating", "credit spread", "sovereign debt", "government bond", "corporate bond", "municipal bond", "duration", "convexity", "yield curve", "inverted yield curve", "flat yield curve", "credit risk", "default risk", "high yield", "investment grade", "junk bond", "fixed income", "debt market", "gilt", "g-sec", "government securities", "repo", "reverse repo", "basis point", "spread tightening", "spread widening", "callable bond", "convertible bond", "zero coupon", "floating rate", "libor", "sofr", "benchmark rate", "debt ceiling", "bond auction", "treasury auction", "mortgage-backed", "asset-backed", "securitization"],
    "Derivatives": ["options", "futures", "swap", "forward contract", "call option", "put option", "strike price", "expiry", "expiration", "derivatives", "hedging", "speculation", "margin call", "mark to market", "notional value", "black-scholes", "implied volatility", "vix", "volatility index", "credit default swap", "cds", "interest rate swap", "currency swap", "commodity futures", "nifty futures", "index futures", "stock futures", "open interest", "option chain", "straddle", "strangle", "collar", "delta", "gamma", "theta", "vega"],
    "Alternative Investments": ["hedge fund", "private equity", "venture capital", "real estate investment", "reit", "infrastructure fund", "commodity", "gold", "crude oil", "silver", "platinum", "natural gas", "agricultural commodity", "alternative asset", "private debt", "distressed debt", "mezzanine", "fund of funds", "sovereign wealth fund", "cryptocurrency", "bitcoin", "ethereum", "crypto", "digital asset", "nft", "blockchain", "collectible", "wine fund", "art fund", "timberland", "farmland", "infrastructure"],
    "Portfolio Management": ["portfolio", "asset allocation", "diversification", "risk management", "sharpe ratio", "risk-adjusted return", "modern portfolio theory", "efficient frontier", "capital asset pricing", "capm", "systematic risk", "unsystematic risk", "rebalancing", "strategic allocation", "tactical allocation", "benchmark", "tracking error", "active management", "passive management", "etf", "mutual fund", "sip", "systematic investment", "wealth management", "financial planning", "retirement fund", "pension", "endowment", "insurance investment", "risk tolerance", "investment policy", "fiduciary"],
    "Ethical & Professional Standards": ["insider trading", "fraud", "compliance", "regulatory", "sec enforcement", "sebi action", "market manipulation", "conflict of interest", "fiduciary duty", "whistleblower", "code of ethics", "professional conduct", "suitability", "best execution", "front running", "churning", "misrepresentation", "material nonpublic", "mnpi", "fair dealing", "disclosure", "transparency", "anti-money laundering", "aml", "know your customer", "kyc", "sanctions", "penalty", "fine", "ban", "debarment", "investigation", "enforcement action", "consent order"],
}

_COMPILED = {}
for _topic, _kws in CFA_TOPIC_KEYWORDS.items():
    _COMPILED[_topic] = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE) for k in _kws]

EXAM_NOTES = {
    "Economics": "Understand how macroeconomic indicators and policy decisions affect markets — a core CFA economics topic.",
    "Fixed Income": "Bond pricing, yield curves, and credit analysis are heavily tested in Fixed Income.",
    "Derivatives": "Know how derivatives are used for hedging and speculation — key for exam valuation questions.",
    "Equity Investments": "Equity valuation methods and market mechanics are fundamental CFA exam areas.",
    "Financial Statement Analysis": "Analyzing financial statements and ratios is the largest CFA L1 topic by weight.",
    "Corporate Issuers": "Corporate finance decisions (capital structure, dividends, M&A) are core exam material.",
    "Portfolio Management": "Asset allocation and portfolio construction concepts appear throughout the CFA curriculum.",
    "Alternative Investments": "Alternative asset classes and their risk-return profiles are increasingly tested.",
    "Quantitative Methods": "Statistical and quantitative tools underpin valuation and risk analysis on the exam.",
    "Ethical & Professional Standards": "Ethics cases and the Code of Conduct are tested heavily — always the first exam topic.",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("cfa-build")

def fetch_article_content(url):
    if not url: return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=ARTICLE_TIMEOUT, headers=headers, allow_redirects=True)
        resp.raise_for_status()
        html_text = resp.text
        for tag in ["script", "style", "nav", "header", "footer", "aside", "figure"]:
            html_text = re.sub(rf"<{tag}[\s>].*?</{tag}>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html_text, re.DOTALL | re.IGNORECASE)
        clean_paragraphs = []
        for p in paragraphs:
            text = re.sub(r"<[^>]+>", " ", p)
            text = html_mod.unescape(text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 60 and "javascript" not in text.lower():
                clean_paragraphs.append(text)
        content = "\n\n".join(clean_paragraphs[:8])
        if len(content) > 2000: content = content[:2000].rsplit(". ", 1)[0] + "."
        return content
    except Exception:
        return ""

def fetch_articles_parallel(stories, max_workers=10):
    log.info("Fetching full article content for %d stories...", len(stories))
    def _fetch(story): return story["title_hash"], fetch_article_content(story.get("link", ""))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch, s): s for s in stories}
        results = {}
        for future in as_completed(futures, timeout=60):
            try:
                h, content = future.result()
                results[h] = content
            except Exception: pass
    for s in stories:
        c = results.get(s["title_hash"], "")
        s["full_content"] = c if (c and len(c) > len(s.get("summary", ""))) else s.get("summary", "")

def _clean(text):
    if not text: return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def build_site():
    log.info("Building CFA SETTLER site...")
    stories = []
    cutoff = datetime.datetime.now(UTC) - datetime.timedelta(hours=MAX_AGE_HOURS)

    for name, url in RSS_FEEDS:
        try:
            log.info("Fetching: %s", name)
            resp = requests.get(url, timeout=FEED_TIMEOUT, headers={"User-Agent": "CFA-Build/1.0"})
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                title = _clean(getattr(entry, "title", ""))
                if not title: continue
                summary = ""
                for field in ("content", "summary", "description"):
                    val = getattr(entry, field, None)
                    if isinstance(val, list) and val:
                        val = val[0].get("value", "") if isinstance(val[0], dict) else str(val[0])
                    if val:
                        cleaned = _clean(str(val))
                        if len(cleaned) > len(summary): summary = cleaned
                link = getattr(entry, "link", "")
                
                # Parse date
                pub_date = None
                for attr in ("published_parsed", "updated_parsed"):
                    tp = getattr(entry, attr, None)
                    if tp:
                        try: pub_date = datetime.datetime(*tp[:6], tzinfo=UTC); break
                        except Exception: pass
                
                if pub_date and pub_date < cutoff: continue

                stories.append({
                    "title": title, "summary": summary[:1500] if summary else "", "link": link,
                    "pub_date": pub_date, "source": name,
                    "title_hash": hashlib.md5(re.sub(r"[^a-z0-9]", "", title.lower()).encode()).hexdigest(),
                })
        except Exception as exc:
            log.error("Failed %s: %s", name, exc)

    # Deduplicate
    seen, unique = set(), []
    for s in stories:
        if s["title_hash"] in seen: continue
        if any(SequenceMatcher(None, s["title"].lower(), t.lower()).ratio() >= 0.75 for t in [x["title"] for x in unique[-100:]]): continue
        seen.add(s["title_hash"]); unique.append(s)

    unique.sort(key=lambda s: s["pub_date"] or datetime.datetime.min.replace(tzinfo=UTC), reverse=True)
    fetch_articles_parallel(unique[:30])
    for s in unique[30:]: s["full_content"] = s.get("summary", "")

    # Tag
    for s in unique:
        text = s["title"] + " " + s.get("full_content", "") + " " + s.get("summary", "")
        topics = [t for t, pats in _COMPILED.items() if any(p.search(text) for p in pats)]
        s["cfa_topics"] = topics
        s["exam_note"] = EXAM_NOTES.get(topics[0], "") if topics else ""

    # Format Date
    for s in unique:
        if s["pub_date"]:
            s["pub_date_str"] = s["pub_date"].astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
            secs = int((datetime.datetime.now(UTC) - s["pub_date"]).total_seconds())
            s["pub_date_relative"] = "just now" if secs < 60 else f"{secs//60}m ago" if secs < 3600 else f"{secs//3600}h ago" if secs < 86400 else f"{secs//86400}d ago"
        else:
            s["pub_date_str"] = "Date unavailable"
            s["pub_date_relative"] = ""

    general = [{"title": s["title"], "full_content": s["full_content"], "source": s["source"], "pub_date_str": s["pub_date_str"], "pub_date_relative": s["pub_date_relative"]} for s in unique[:20]]
    cfa = [{"title": s["title"], "full_content": s["full_content"], "source": s["source"], "pub_date_str": s["pub_date_str"], "pub_date_relative": s["pub_date_relative"], "cfa_topics": s["cfa_topics"], "exam_note": s["exam_note"]} for s in unique if s["cfa_topics"]][:20]

    data = {
        "general": general,
        "cfa": cfa,
        "updated_at": datetime.datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST"),
        "total_stories": len(unique)
    }

    # Inject into HTML template
    template_path = os.path.join(os.path.dirname(__file__), "template.html")
    output_path = os.path.join(os.path.dirname(__file__), "index.html")
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace placeholder with actual JSON data
    html = html.replace("__NEWS_DATA_PLACEHOLDER__", json.dumps(data))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    log.info("Build complete: index.html generated.")

if __name__ == "__main__":
    build_site()
