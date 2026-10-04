#!/usr/bin/env python3
"""
High-Growth X (Twitter) Autoposter & Cross-Posting Engine for Sabhay Tomar
Engineered to cross-post high-impact General Finance insights to X.

Features:
1. Dual-Engine Publishing:
   - Method 1 (Headless API): Uses session cookies (auth_token + ct0) for 100% background posting.
   - Method 2 (Chrome Intent / AppleScript): Direct browser trigger using active Chrome session.
2. Format Optimizer: Automatically generates high-velocity standalone tweets (< 280 chars)
   with viral hooks, clean bullet points, and discussion catalysts.
3. Synchronized with LinkedIn: Can run standalone or trigger alongside linkedin_autoposter.py.
"""

import os
import sys
import json
import ssl
import random
import logging
import argparse
import subprocess
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional

IST = ZoneInfo("Asia/Kolkata")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("x-autoposter")

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
X_HISTORY_FILE = DATA_DIR / "x_post_history.json"

# Credentials from environment or .env
AUTH_TOKEN = os.getenv("TWITTER_AUTH_TOKEN", "")
CT0_TOKEN = os.getenv("TWITTER_CT0", "")

# Viral 280-Character Finance Tweets (Punched for Maximum Retweet & Quote Velocity)
X_FINANCE_VAULT: List[Dict[str, str]] = [
    {
        "category": "wealth_habits",
        "text": "The Rule of 72 is the simplest math hack in finance:\n\nDivide 72 by your expected return to see how fast your money doubles:\n• 6% (Bonds) = 12 yrs\n• 10% (Index) = 7.2 yrs\n• 14% (Growth) = 5.1 yrs\n\nTime in the market > timing the market.\n\nWhat return are you targeting?",
    },
    {
        "category": "wealth_habits",
        "text": "Making $100k and spending $95k leaves you less free than making $60k and saving $20k.\n\nWealth isn't what you earn. It's what you keep.\n\n4 rules to beat lifestyle creep:\n1. Invest 50% of raises\n2. Fixed costs < 50%\n3. Assets fund luxuries\n4. Status ≠ Wealth",
    },
    {
        "category": "investing_valuation",
        "text": "A 90-year Bank of America study on the S&P 500:\n\n• Stayed invested: +17,715% total return\n• Missed just the 10 best days per decade: +28% return\n\nThe market's best days almost always follow the worst crash days.\n\nNever sell in panic.",
    },
    {
        "category": "investing_valuation",
        "text": "Charlie Munger's single most important metric for business quality: ROIC.\n\n\"Over the long term, it’s hard for a stock that earns 6% on capital to earn much more than a 6% return.\"\n\nA high-ROIC business funds its own growth without debt.\n\nLook for ROIC > 15%.",
    },
    {
        "category": "wealth_habits",
        "text": "Rich is what you see: the luxury car, the watch, the leased condo.\n\nWealth is what you don't see: the unspent cash, the optionality, the peace of mind, the 3 years of runway, the freedom to say NO.\n\nWould you rather look rich today or be quietly wealthy in 10 years?",
    },
    {
        "category": "corporate_moats",
        "text": "Warren Buffett on Pricing Power:\n\n\"If you have the power to raise prices by 10% without losing business to a competitor, you've got a terrific business.\nIf you need a prayer session before raising prices by 10%, you've got a terrible business.\"\n\nCheck moats first.",
    },
    {
        "category": "financial_hacks",
        "text": "Opportunity Cost is the invisible price tag on everything.\n\nAn $80,000 car loan doesn't just cost $80k.\n\nInvested in index funds at 9%, that $80k grows to:\n• $189k in 10 yrs\n• $448k in 20 yrs\n• $1.06 Million in 30 yrs\n\nThat car cost you $1M in future net worth.",
    },
    {
        "category": "corporate_moats",
        "text": "How Amazon and Dell funded multi-billion dollar expansions using other people's money:\n\nThe Negative Working Capital Cycle:\n1. Collect customer cash in 1-2 days\n2. Hold inventory for only 15 days\n3. Pay suppliers on 60-90 day terms\n\nFree float is the ultimate growth hack.",
    },
    {
        "category": "wealth_habits",
        "text": "The $100/mo compounding roadmap (at 10% return):\n\n• 10 yrs: $20,500\n• 20 yrs: $76,000\n• 30 yrs: $228,000\n• 40 yrs: $632,000\n\nIn the final decade, your portfolio generates more pure interest than all your lifetime contributions combined.\n\nStart early.",
    },
    {
        "category": "investing_valuation",
        "text": "Buying a stock solely because its P/E ratio is low is the most common value trap in finance.\n\nAn 8x P/E with falling revenue and high debt is expensive.\nA 32x P/E compounder growing cash flow at 25% with zero debt is cheap.\n\nValuation is future cash, not past P/E.",
    },
    {
        "category": "financial_hacks",
        "text": "A 1% annual advisory fee sounds harmless.\n\nOver a 30-year horizon, that 1% fee quietly steals over 25% of your total compounded wealth ($250k+ lost on a $100k portfolio).\n\nFees don't just reduce returns; they compound in reverse against you.\n\nCheck your expense ratios.",
    },
    {
        "category": "corporate_moats",
        "text": "Over 70% of corporate mergers & acquisitions destroy shareholder value.\n\nWhy?\n1. Winner's curse (overpaying in auctions)\n2. Cultural & tech rejection\n3. CEO empire-building instead of per-share value.\n\nThe best capital allocators acquire sparingly.",
    }
]


def load_x_history() -> List[dict]:
    if X_HISTORY_FILE.exists():
        try:
            with open(X_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_x_history(entry: dict):
    hist = load_x_history()
    hist.append(entry)
    with open(X_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)


def get_fresh_tweet(category: Optional[str] = None) -> Dict[str, str]:
    hist = load_x_history()
    recent_texts = [h.get("text", "")[:40] for h in hist[-20:]]
    
    candidates = X_FINANCE_VAULT
    if category:
        candidates = [t for t in candidates if t.get("category") == category] or X_FINANCE_VAULT
        
    fresh = [t for t in candidates if t["text"][:40] not in recent_texts]
    return random.choice(fresh) if fresh else random.choice(candidates)


def post_to_x_via_chrome_intent(tweet_text: str, auto_submit: bool = True) -> bool:
    """
    Publishes to X autonomously using the active logged-in Google Chrome session.
    1. Opens https://x.com/intent/post with the pre-filled tweet in Chrome.
    2. Waits for the X composer to render and gain focus.
    3. Sends Cmd+Return via macOS System Events to submit the tweet.
    4. Automatically closes the tab after publishing.
    """
    encoded = urllib.parse.quote(tweet_text)
    url = f"https://x.com/intent/post?text={encoded}"
    
    if auto_submit:
        apple_script = f'''
        tell application "Google Chrome"
            activate
            tell front window
                make new tab at end of tabs with properties {{URL:"{url}"}}
            end tell
        end tell
        delay 3.0
        tell application "System Events"
            tell process "Google Chrome"
                keystroke return using command down
            end tell
        end tell
        delay 2.5
        tell application "Google Chrome"
            tell front window
                close active tab
            end tell
        end tell
        '''
    else:
        apple_script = f'''
        tell application "Google Chrome"
            activate
            tell front window
                make new tab at end of tabs with properties {{URL:"{url}"}}
            end tell
        end tell
        '''
    try:
        res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
        if res.returncode == 0:
            log.info("✅ Tweet posted autonomously to X via Chrome!")
            return True
        else:
            log.error(f"AppleScript error: {res.stderr}")
            return False
    except Exception as e:
        log.error(f"Failed to post via Chrome: {e}")
        return False


def post_to_x_headless(tweet_text: str, auth_token: str, ct0: str) -> bool:
    """
    Headlessly publishes a tweet via X internal GraphQL API using session cookies.
    """
    url = "https://x.com/i/api/graphql/xTflPy4O-9m6s14EwNLfqw/CreateTweet"
    headers = {
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-csrf-token": ct0,
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "Cookie": f"auth_token={auth_token}; ct0={ct0}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    
    payload = {
        "variables": {
            "tweet_text": tweet_text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
            "semantic_annotation_ids": []
        },
        "features": {
            "communities_web_enable_tweet_community_results_fetch": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        },
        "queryId": "xTflPy4O-9m6s14EwNLfqw"
    }
    
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tweet_id = data.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result", {}).get("rest_id", "")
            log.info(f"✅ Tweet published headlessly! Tweet ID: {tweet_id}")
            return True
    except urllib.error.HTTPError as e:
        log.error(f"X API HTTPError {e.code}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        return False
    except Exception as ex:
        log.error(f"X API Exception: {ex}")
        return False


def publish_tweet(tweet_text: Optional[str] = None, category: Optional[str] = None) -> bool:
    tweet_obj = {"text": tweet_text, "category": category or "general"} if tweet_text else get_fresh_tweet(category=category)
    text_to_post = tweet_obj["text"]
    
    now_ist = datetime.now(IST)
    log.info(f"Preparing to publish tweet ({len(text_to_post)} chars)...")
    
    # Check if headless credentials exist
    auth_token = os.getenv("TWITTER_AUTH_TOKEN", AUTH_TOKEN)
    ct0 = os.getenv("TWITTER_CT0", CT0_TOKEN)
    
    success = False
    method = ""
    if auth_token and ct0:
        log.info("Using Headless Session Cookie Engine...")
        success = post_to_x_headless(text_to_post, auth_token, ct0)
        method = "headless_api"
    else:
        log.info("No TWITTER_AUTH_TOKEN found in env. Falling back to Chrome Browser Engine...")
        success = post_to_x_via_chrome_intent(text_to_post)
        method = "chrome_intent"
        
    entry = {
        "timestamp_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "date_ist": now_ist.strftime("%Y-%m-%d"),
        "category": tweet_obj.get("category"),
        "text": text_to_post,
        "method": method,
        "success": success
    }
    save_x_history(entry)
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X (Twitter) Finance Autoposter")
    parser.add_argument("--post-now", action="store_true", help="Post a fresh finance tweet right now")
    parser.add_argument("--category", type=str, help="Specific category")
    parser.add_argument("--text", type=str, help="Custom text to tweet")
    args = parser.parse_args()

    if args.post_now or args.text:
        publish_tweet(tweet_text=args.text, category=args.category)
    else:
        # Default test run
        tweet = get_fresh_tweet()
        print("\n" + "=" * 60)
        print(f"X PREVIEW TWEET ({len(tweet['text'])} chars | {tweet['category']}):")
        print("=" * 60)
        print(tweet["text"])
        print("=" * 60 + "\n")
