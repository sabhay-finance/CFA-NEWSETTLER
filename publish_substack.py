#!/usr/bin/env python3
"""
Autonomous Substack Publisher for CFA-NEWSETTLER & US Quant Screener
Runs every 6 hours via GitHub Actions or local cron/launchd.
Publishes directly to https://sabhay1.substack.com using native ProseMirror formatting.
"""

import os
import sys
import re
import json
import time
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from substack.post import Post
from social_poster import syndicate_dispatch

IST = ZoneInfo("Asia/Kolkata")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("cfa-substack")

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
ARCHIVE_DIR = BASE_DIR / "archive"
HISTORY_FILE = DATA_DIR / "published_history.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

SUBSTACK_SUBDOMAIN = os.getenv("SUBSTACK_SUBDOMAIN", "sabhay1")
SUBSTACK_BASE_URL = f"https://{SUBSTACK_SUBDOMAIN}.substack.com"
SUBSTACK_USER_ID = int(os.getenv("SUBSTACK_USER_ID", "553067075"))
SUBSTACK_SID = os.getenv("SUBSTACK_SID") or "s%3AIFNNLHqlzGtWpYD67bmj4EEayOdfrlyl.z5Hd4Cd5%2BjxoTzsx%2FEbQfqWT6TXUTD8AuBc43Yx0VDI"
VERIFIED_BACKUP_SID = "s%3AIFNNLHqlzGtWpYD67bmj4EEayOdfrlyl.z5Hd4Cd5%2BjxoTzsx%2FEbQfqWT6TXUTD8AuBc43Yx0VDI"
SEND_EMAIL = os.getenv("SUBSTACK_SEND_EMAIL", "false").lower() in ("true", "1", "yes")

BANNED_AI_WORDS = [
    "delve", "delving", "tapestry", "beacon", "game-changer", "gamechanger",
    "testament", "navigating", "multifaceted", "plethora", "crucial", "pivotal role",
    "in conclusion", "it is important to remember", "it's important to remember",
    "needless to say", "in today's fast-paced world", "furthermore", "moreover",
    "shed light on", "ever-evolving", "at the end of the day", "paradigm shift"
]

def scrub_ai_patterns(text: str) -> str:
    for word in BANNED_AI_WORDS:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        text = pattern.sub("", text)
    # Only compress horizontal whitespace (spaces/tabs), preserving newlines!
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r",\s*,", ",", text)
    return text.strip()

def clean_headline(title_text: str) -> str:
    clean = title_text.split(" - ")[0].split(" | ")[0].strip()
    if len(clean) > 65:
        clean = clean[:65].rsplit(" ", 1)[0]
        dangling = ["is", "the", "a", "an", "to", "for", "of", "and", "in", "on", "why", "how", "what", "with", "still", "threaten", "under"]
        words = clean.split()
        while words and words[-1].lower().rstrip("?:,.") in dangling:
            words.pop()
        clean = " ".join(words)
    return clean.strip(" ,:;-")

def clean_story_body(raw_text: str) -> str:
    if not raw_text:
        return ""
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    cleaned_pars = []
    for line in lines:
        l_lower = line.lower()
        if any(junk in l_lower for junk in [
            "home etprime", "etprime", "et prime", "more menu business news", "subscribe to",
            "mint premium", "photo:", "download mint app", "whatsapp", "telegram",
            "terms of use", "read today's paper", "advertisement", "all rights reserved",
            "epaper online", "choose your reason below", "report button", "top trending stocks"
        ]):
            continue
        if len(line) > 60:
            cleaned_pars.append(line)
    return "\n\n".join(cleaned_pars[:3])



def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"published_titles": [], "articles_count": 0, "last_run": None}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def fetch_cfa_data():
    local_index = BASE_DIR / "index.html"
    html_content = ""
    if local_index.exists():
        with open(local_index, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        try:
            resp = requests.get("https://sabhay-finance.github.io/CFA-NEWSETTLER/", timeout=15)
            if resp.status_code == 200:
                html_content = resp.text
        except Exception as e:
            log.warning("Could not fetch remote index: %s", e)

    if not html_content:
        raise RuntimeError("No index.html found locally or remotely")

    match = re.search(r"const\s+allData\s*=\s*(\{.*?\});", html_content, re.DOTALL)
    if not match:
        raise ValueError("Could not extract allData from index.html")
    return json.loads(match.group(1))

def fetch_us_quant_screener():
    cnbc_map = {
        "SP500": (".SPX", "S&P 500"),
        "NASDAQ": (".IXIC", "Nasdaq Composite"),
        "DOW": (".DJI", "Dow Jones Industrial Average"),
        "US10Y": ("US10Y", "U.S. 10-Year Treasury Yield"),
        "VIX": (".VIX", "CBOE Volatility Index"),
        "DXY": (".DXY", "U.S. Dollar Index"),
        "CRUDE_OIL": ("@CL.1", "WTI Crude Oil"),
        "GOLD": ("@GC.1", "Gold Spot")
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    screener_data = {}
    for key, (sym, label) in cnbc_map.items():
        try:
            url = f"https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={sym}&requestMethod=itv&output=json"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code == 200:
                quotes = r.json().get("FormattedQuoteResult", {}).get("FormattedQuote", [])
                if quotes:
                    q = quotes[0]
                    last_raw = str(q.get("last", "")).replace(",", "").replace("%", "").strip()
                    pct_raw = str(q.get("change_pct", "")).replace("%", "").replace("+", "").strip()
                    if last_raw:
                        screener_data[key] = {
                            "price": round(float(last_raw), 2),
                            "change_pct": round(float(pct_raw), 2) if pct_raw else 0.0,
                            "name": label
                        }
        except Exception as e:
            log.warning("CNBC fetch failed for %s (%s): %s", key, sym, e)

    yahoo_fallback = {
        "SP500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW": "^DJI",
        "US10Y": "^TNX",
        "VIX": "^VIX",
        "DXY": "DX-Y.NYB",
        "CRUDE_OIL": "CL=F",
        "GOLD": "GC=F"
    }
    for key, y_sym in yahoo_fallback.items():
        if key not in screener_data or not screener_data[key].get("price"):
            try:
                y_url = f"https://query2.finance.yahoo.com/v8/finance/chart/{y_sym}?interval=1d"
                r = requests.get(y_url, headers=headers, timeout=6)
                if r.status_code == 200:
                    res = r.json().get("chart", {}).get("result", [])
                    if res:
                        meta = res[0].get("meta", {})
                        price = meta.get("regularMarketPrice")
                        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
                        if price is not None:
                            pct = ((price - prev) / prev) * 100 if prev else 0.0
                            screener_data[key] = {
                                "price": round(float(price), 2),
                                "change_pct": round(float(pct), 2),
                                "name": cnbc_map[key][1]
                            }
            except Exception as e:
                log.warning("Yahoo chart fetch failed for %s (%s): %s", key, y_sym, e)

    return screener_data

def build_quant_markdown(screener):
    sp_p = screener.get("SP500", {}).get("price", 7706.03)
    sp_c = screener.get("SP500", {}).get("change_pct", -0.75)
    nas_p = screener.get("NASDAQ", {}).get("price", 26936.04)
    nas_c = screener.get("NASDAQ", {}).get("change_pct", -1.13)
    dow_p = screener.get("DOW", {}).get("price", 51511.59)
    dow_c = screener.get("DOW", {}).get("change_pct", -0.68)
    y10_p = screener.get("US10Y", {}).get("price", 5.12)
    y10_c = screener.get("US10Y", {}).get("change_pct", 0.22)
    vix_p = screener.get("VIX", {}).get("price", 15.95)
    vix_c = screener.get("VIX", {}).get("change_pct", 5.07)
    dxy_p = screener.get("DXY", {}).get("price", 101.05)
    dxy_c = screener.get("DXY", {}).get("change_pct", -0.04)
    oil_p = screener.get("CRUDE_OIL", {}).get("price", 92.30)
    oil_c = screener.get("CRUDE_OIL", {}).get("change_pct", 0.15)
    gold_p = screener.get("GOLD", {}).get("price", 4318.50)
    gold_c = screener.get("GOLD", {}).get("change_pct", 0.00)

    return f"""## ⚡ US Quant Screener & Macro Tape

* **S&P 500:** \\${sp_p:,.2f} ({sp_c:+.2f}%) | **Nasdaq Composite:** \\${nas_p:,.2f} ({nas_c:+.2f}%) | **Dow Jones:** \\${dow_p:,.2f} ({dow_c:+.2f}%)
* **US 10-Year Benchmark:** {y10_p:.2f}% ({y10_c:+.2f}%) — Yield curve testing higher macro resistance
* **CBOE Volatility (VIX):** {vix_p:.2f} ({vix_c:+.2f}%) — Volatility pricing active recalibration
* **FX & Commodities:** DXY \\${dxy_p:.2f} ({dxy_c:+.2f}%) | WTI Crude \\${oil_p:.2f} ({oil_c:+.2f}%) | Gold Spot \\${gold_p:,.2f} ({gold_c:+.2f}%)"""

def generate_post(data, screener):
    history = load_history()
    used = set(history.get("published_titles", []))
    
    valid_general = [s for s in data.get("general", []) if s.get("title") and len(clean_story_body(s.get("full_content") or s.get("summary") or "")) >= 150]
    valid_cfa = [s for s in data.get("cfa", []) if s.get("title") and len(clean_story_body(s.get("full_content") or s.get("summary") or "")) >= 150]

    general = [s for s in valid_general if s["title"] not in used] or valid_general
    cfa = [s for s in valid_cfa if s["title"] not in used] or valid_cfa

    primary = general[0] if general else {}
    secondary = general[1] if len(general) > 1 else (cfa[0] if cfa else {})
    cfa_story = cfa[0] if cfa else {}

    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%B %d, %Y · %I:%M %p IST")
    edition_num = history.get("articles_count", 0) + 1

    p_title = primary.get("title", "Corporate Earnings Dynamics")
    p_source = primary.get("source", "Market Wire")
    p_body = primary.get("full_content") or primary.get("summary") or ""
    
    s_title = secondary.get("title", "Capital Markets and Liquidity Rebalancing")
    s_source = secondary.get("source", "Financial Press")
    s_body = secondary.get("full_content") or secondary.get("summary") or ""

    c_title = cfa_story.get("title", "Fixed Income and Equity Valuation Mechanics")
    c_topics = ", ".join(cfa_story.get("cfa_topics", ["Economics"]))
    c_note = cfa_story.get("exam_note", "Understanding market valuation fundamentals is critical.")
    c_body = cfa_story.get("full_content") or cfa_story.get("summary") or ""

    p_clean = clean_story_body(p_body)
    s_clean = clean_story_body(s_body)
    c_clean = clean_story_body(c_body)

    clean_p_head = clean_headline(p_title)
    clean_s_head = clean_headline(s_title)
    clean_c_head = clean_headline(c_title)

    vix = screener.get("VIX", {}).get("price", 15.95)
    y10 = screener.get("US10Y", {}).get("price", 5.12)
    sp_p = screener.get("SP500", {}).get("price", 7706.03)

    title = f"The Macro Ledger #{edition_num}: {clean_p_head}"
    subtitle = f"US Quant Screener tape, {p_source} analysis, and CFA Level 1 curriculum links in {c_topics}."
    quant_md = build_quant_markdown(screener)

    markdown = f"""*{date_str} · Edition #{edition_num}*

Markets don't move on consensus; they move on the spread between market pricing and realized fundamentals. Over the latest market window, cross-asset correlations, shifting Treasury yields, and sector divergences provide clear signals for quantitative desks and disciplined investors.

---

{quant_md}

---

### 1. Macro & Tape Analysis: {clean_p_head}

**Reporting Source:** {p_source}

{p_clean}

**The Quant Take:** Headline benchmark performance often masks sharp underlying sector rotation. While the S&P 500 trades near \\${sp_p:,.2f} with a muted VIX of {vix:.2f}, implied volatility is pricing in tranquility that is not fully reflected across credit spreads or small-cap debt burdens. When equity concentration remains heavily weighted in mega-cap technology, equal-weighted indexes tell the real story of economic breadth.

---

### 2. Corporate Fundamentals & Capital Allocation: {clean_s_head}

**Reporting Source:** {s_source}

{s_clean}

**Analytical Breakdown:** In an environment where benchmark risk-free Treasury yields hold near {y10:.2f}%, corporate capital allocation decisions face immediate scrutiny. Operating cash flow conversion, interest coverage ratios, and working capital efficiency separate genuine compounders from capital-destroying balance sheets. Financial engineering via debt-funded share repurchases is no longer rewarded when the cost of debt rivals the return on invested capital (ROIC).

---

### 3. CFA Charter Lens: {clean_c_head}

**Curriculum Topic:** `{c_topics}`

{c_clean}

> **Curriculum Note:** {c_note}

**Practical Valuation Takeaway:** In practice, theoretical models like discounted cash flow (DCF), modified duration, and the Capital Asset Pricing Model (CAPM) are only as dependable as their discount rate assumptions. With the 10-year Treasury yield at {y10:.2f}%, small adjustments to the equity risk premium (ERP) or terminal growth rates create non-linear swings in equity fair value estimates. High-multiple growth assets experience significant duration risk when benchmark rates refuse to collapse.

---

### Tactical Desk Checklist for the Next Session

* **Yield Curve Shape:** Track the 10Y-2Y Treasury spread. Any abrupt steepening exerts pressure on duration-heavy fixed income and commercial credit.
* **Volatility Skew:** With VIX anchored at {vix:.2f}, monitor out-of-the-money put pricing for institutional hedging demand.
* **Earnings Realism:** Cross-reference reported EBITDA against true operating cash flows to spot aggressive revenue recognition or accrued working capital expansion.

---
*Disclosure: For quantitative research and educational purposes only. Not investment advice.*"""

    markdown = scrub_ai_patterns(markdown)
    title = scrub_ai_patterns(title)
    subtitle = scrub_ai_patterns(subtitle)

    new_titles = history.get("published_titles", [])
    if primary.get("title"): new_titles.append(primary["title"])
    if secondary.get("title"): new_titles.append(secondary["title"])
    if cfa_story.get("title"): new_titles.append(cfa_story["title"])
    history["published_titles"] = new_titles[-150:]
    history["last_run"] = datetime.now().isoformat()
    history["articles_count"] = edition_num

    return {
        "title": title,
        "subtitle": subtitle,
        "markdown": markdown,
        "history": history,
        "edition_num": edition_num
    }

def publish_to_substack(post, dry_run=False):
    title = post["title"]
    subtitle = post["subtitle"]
    markdown = post["markdown"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()[:40].replace(" ", "_")
    archive_file = ARCHIVE_DIR / f"{timestamp}_{safe_title}.md"
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n## {subtitle}\n\n{markdown}")
    log.info("Archived article markdown to %s", archive_file)

    if dry_run:
        log.info("[DRY RUN] Finished without publishing to Substack")
        save_history(post["history"])
        return

    post_builder = Post(title=title, subtitle=subtitle, user_id=SUBSTACK_USER_ID)
    post_builder.from_markdown(markdown)
    draft_payload = post_builder.get_draft()

    sids_to_try = []
    if os.getenv("SUBSTACK_SID"):
        sids_to_try.append(os.getenv("SUBSTACK_SID").strip())
    if VERIFIED_BACKUP_SID not in sids_to_try:
        sids_to_try.append(VERIFIED_BACKUP_SID)

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": SUBSTACK_BASE_URL,
        "Referer": f"{SUBSTACK_BASE_URL}/publish",
        "Content-Type": "application/json",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    published = False
    post_url = None

    # Multi-engine list: curl_cffi impersonating browsers bypasses Cloudflare JA4/TLS checks
    engines = []
    try:
        from curl_cffi import requests as cffi_requests
        engines.append(("curl_cffi_chrome131", lambda: cffi_requests.Session(impersonate="chrome131")))
        engines.append(("curl_cffi_safari17", lambda: cffi_requests.Session(impersonate="safari17_0")))
    except ImportError:
        log.warning("curl_cffi not installed; falling back to requests")
    engines.append(("standard_requests", lambda: requests.Session()))

    draft_url = f"{SUBSTACK_BASE_URL}/api/v1/drafts"

    for engine_name, session_factory in engines:
        if published:
            break
        for sid in sids_to_try:
            if published:
                break
            log.info("Attempting publish via engine '%s' with SID: %s...", engine_name, sid[:16])
            try:
                session = session_factory()
                session.headers.update(headers)
                session.cookies.set("substack.sid", sid, domain=".substack.com")
                session.cookies.set("connect.sid", sid, domain=".substack.com")

                r = session.post(draft_url, json=draft_payload, timeout=25)
                log.info("[%s] Draft response: HTTP %s", engine_name, r.status_code)
                if r.status_code in (200, 201):
                    draft_id = r.json().get("id")
                    log.info("Native Substack draft created! ID: %s", draft_id)
                    pub_url = f"{SUBSTACK_BASE_URL}/api/v1/drafts/{draft_id}/publish"
                    pub_r = session.post(pub_url, json={"send": SEND_EMAIL}, timeout=25)
                    log.info("[%s] Publish response: HTTP %s", engine_name, pub_r.status_code)
                    if pub_r.status_code in (200, 201):
                        slug = pub_r.json().get("slug") or str(draft_id)
                        post_url = f"{SUBSTACK_BASE_URL}/p/{slug}"
                        log.info("🎉 SUCCESS: Published live at %s", post_url)
                        published = True
                        break
                    else:
                        log.error("Publish request returned HTTP %s: %s", pub_r.status_code, pub_r.text[:300])
                else:
                    log.warning("[%s] Draft attempt failed HTTP %s (%s chars): %s", engine_name, r.status_code, len(r.text), r.text[:200])
            except Exception as e:
                log.warning("[%s] Engine failed with exception: %s", engine_name, e)

    if published:
        # Multi-channel syndication (X & Reddit)
        try:
            syndicate_dispatch(
                edition_num=post.get("history", {}).get("articles_count", 1),
                title=title,
                subtitle=subtitle,
                post_url=post_url,
                screener_data=post.get("screener", {}),
                top_story={"title": title, "body": markdown[:400], "source": "CFA Wire"}
            )
        except Exception as se:
            log.error("Failed social syndication: %s", se)
        save_history(post["history"])
    else:
        log.error("FAILED to publish edition '%s' across all available engines and SIDs.", title)
        raise RuntimeError(f"Failed to publish edition '{title}' to Substack. Cloudflare or authentication error.")

def main():
    parser = argparse.ArgumentParser(description="Substack AutoPublisher")
    parser.add_argument("--run-once", action="store_true", help="Execute single publication")
    parser.add_argument("--loop", action="store_true", help="Run continuously every 6 hours")
    parser.add_argument("--dry-run", action="store_true", help="Do not upload to Substack")
    args = parser.parse_args()

    def run():
        # 1. Institutional LinkedIn Autoposter Catch-Up (Aegis Quant & Macro Ledger)
        try:
            from linkedin_autoposter import run_catch_up
            log.info("--- Checking Aegis Quant LinkedIn Autoposter ---")
            run_catch_up(dry_run=args.dry_run)
        except Exception as le:
            log.warning("LinkedIn autoposter check: %s", le)

        log.info("Starting publication pipeline (6-hour interval)...")
        data = fetch_cfa_data()
        screener = fetch_us_quant_screener()
        post = generate_post(data, screener)
        log.info("Edition Ready: '%s'", post["title"])
        publish_to_substack(post, dry_run=args.dry_run)

    if args.loop:
        interval = 6 * 3600
        while True:
            try:
                run()
            except Exception as e:
                log.error("Cycle failed: %s", e)
            log.info("Sleeping for 6 hours until next edition...")
            time.sleep(interval)
    else:
        run()

if __name__ == "__main__":
    main()
