#!/usr/bin/env python3
"""
Institutional LinkedIn Autoposter for Aegis Quant & The Macro Ledger
Strictly enforces:
- 6 daily scheduled posts (4 Substack, 2 Aegis Quant Screener)
  Slot 1 (08:00 IST): The Macro Ledger (Macro Tape, Rates, ERP)
  Slot 2 (11:00 IST): Aegis Quant Screener (Volatility Clustering, HV20/30, Quant Risk)
  Slot 3 (14:00 IST): The Macro Ledger (Valuation Mechanics, WACC, Factor Alpha)
  Slot 4 (17:00 IST): Aegis Quant Screener (Volume Dynamics, RVOL Breakouts)
  Slot 5 (19:30 IST): The Macro Ledger (Backtest Biases, Execution Modeling)
  Slot 6 (21:30 IST): The Macro Ledger (Cross-Asset Momentum, Risk Parity)
- Fully idempotent catch-up mechanism: runs safely on 24/7 cloud cron or local scheduler
  without double-posting or missing scheduled slots.
"""

import os
import sys
import ssl
import json
import random
import logging
import argparse
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
log = logging.getLogger("linkedin-autoposter")

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "linkedin_post_history.json"

# Credentials (from environment or defaults)
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "ak_Xcw5h4TCAaKIVZTosuue")
CONNECTED_ACCOUNT_ID = os.getenv("LINKEDIN_CONNECTED_ACCOUNT_ID", "ca_D6c1UFZdkhcq")
USER_ID = "default"
ENTITY_ID = "default"
AUTHOR_URN = "urn:li:person:bsR37USNqa"

SUBSTACK_URL = "https://sabhay1.substack.com"
AEGIS_URL = "https://aegisquant.net"

SLOTS = [
    {
        "slot_num": 1,
        "time_ist": "08:00",
        "target": "The Macro Ledger (Substack)",
        "url": SUBSTACK_URL,
        "category": "macro_rates",
        "cta_text": f"Read the full tape breakdown in our latest Tape Notes edition on The Macro Ledger: {SUBSTACK_URL}"
    },
    {
        "slot_num": 2,
        "time_ist": "11:00",
        "target": "Aegis Quant Screener",
        "url": AEGIS_URL,
        "category": "volatility_risk",
        "cta_text": f"Screen Indian & global equities by historical volatility and quant risk scores on Aegis Quant Screener: {AEGIS_URL}"
    },
    {
        "slot_num": 3,
        "time_ist": "14:00",
        "target": "The Macro Ledger (Substack)",
        "url": SUBSTACK_URL,
        "category": "factor_alpha",
        "cta_text": f"Explore our valuation mechanics and cross-asset factor research on The Macro Ledger: {SUBSTACK_URL}"
    },
    {
        "slot_num": 4,
        "time_ist": "17:00",
        "target": "Aegis Quant Screener",
        "url": AEGIS_URL,
        "category": "volume_rvol",
        "cta_text": f"Filter NSE & BSE equities by institutional RVOL anomalies and breakout metrics on Aegis Quant Screener: {AEGIS_URL}"
    },
    {
        "slot_num": 5,
        "time_ist": "19:30",
        "target": "The Macro Ledger (Substack)",
        "url": SUBSTACK_URL,
        "category": "backtest_execution",
        "cta_text": f"Read our institutional guide to quantitative modeling and execution mechanics on The Macro Ledger: {SUBSTACK_URL}"
    },
    {
        "slot_num": 6,
        "time_ist": "21:30",
        "target": "The Macro Ledger (Substack)",
        "url": SUBSTACK_URL,
        "category": "cross_asset_momentum",
        "cta_text": f"Dive into our systematic capital flow and cross-asset tape notes on The Macro Ledger: {SUBSTACK_URL}"
    }
]

CONTENT_VAULT = {
    "macro_rates": [
        {
            "hook": "Treasury yields testing 5.18% aren't just a hurdle rate problem for equities.\nThey fundamentally distort the cross-asset risk premium and mechanical capital flows.",
            "body": "When risk-free 10-year paper offers 5.18%, the equity risk premium (ERP) compresses to near-two-decade lows. The S&P 500 earnings yield hovering around 4.8% implies investors are accepting negative real compensation for absorbing equity duration risk.\n\nYet, equity indices continue pushing higher on momentum. The divergence is explained by systematic capital flows: corporate buyback execution desks and systematic trend CTAs remain forced buyers, absorbing retail and discretionary outflows. Until liquidity conditions shift or corporate cash reserves face refinancing cliffs, macro valuation metrics lag behind liquidity physics.\n\nTracking the spread between sovereign term premia and cross-asset beta tells you where institutional capital is actually rotating before it appears in consensus commentary.",
            "cta": f"Read the full tape breakdown in our latest Tape Notes edition on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#Macroeconomics", "#TreasuryYields", "#CapitalFlows", "#Equities", "#TheMacroLedger"]
        },
        {
            "hook": "Macroeconomic releases do not move markets in isolation.\nPrice action is driven strictly by the delta between high-frequency economic surprises and existing institutional positioning.",
            "body": "When US 10-Year yields test critical multi-year highs while the US Dollar Index diverges from crude oil, traditional 60/40 asset allocation models face systemic correlation breakdown. During high-inflation regimes, the historical -0.30 correlation between stocks and bonds flips positive, eliminating classical portfolio diversification benefits.\n\nSystematic macro desks do not wait for backward-looking GDP or revision prints. Instead, quantitative frameworks decompose macro surprise indices, cross-asset momentum vectors, and yield curve slope dynamics to dynamically adjust risk budgets across regimes.\n\nBy monitoring real-time breakeven inflation spreads and terminal policy expectations across overnight index swaps (OIS), quants identify cross-asset dislocations weeks before they hit mainstream headlines. If your asset allocation assumes static historical covariance, you are taking unhedged tail risk in an evolving macro regime.",
            "cta": f"Explore our quantitative macro frameworks and Tape Notes on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#MacroTape", "#CrossAsset", "#AssetAllocation", "#SystematicTrading", "#TheMacroLedger"]
        },
        {
            "hook": "The term premium on long-dated sovereign debt is the single most underappreciated variable in modern macro allocation.\nWhen term premia reconstitute, multi-asset equity duration suffers severe multiple compression.",
            "body": "For over a decade of quantitative easing, sovereign term premia were suppressed into deep negative territory. Investors grew accustomed to discounting long-dated tech cash flows at unnaturally low terminal rates.\n\nToday, fiscal issuance deficits and quantitative tightening are forcing private balance sheets to absorb trillions in duration supply. As term premia push back into positive territory, the discount factor applied to distant earnings expands non-linearly.\n\nEquity portfolios holding high price-to-sales ratios without near-term free cash flow yield become highly convex to upward yield curve steepening. Tracking the slope of the 2s10s curve against cross-asset risk appetite provides an essential compass for tactical portfolio rebalancing.",
            "cta": f"Deconstruct the yield curve mechanics and cross-asset impacts on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#YieldCurve", "#MacroEconomics", "#SovereignDebt", "#DurationRisk", "#TheMacroLedger"]
        }
    ],
    "volatility_risk": [
        {
            "hook": "Buying a stock simply because its P/E ratio dropped below 15 is one of the most reliable ways to catch a falling knife in systematic equities.\nValue without volatility adjustment is just uncompensated downside risk.",
            "body": "Across Indian and global equity universes (NSE, BSE, S&P 500), low-multiple stocks experiencing negative relative volume (RVOL < 0.7) and accelerating historical volatility show a 68% probability of continued multiple compression over subsequent quarters. When institutional desks distribute shares, valuation metrics fail as support because liquidity dry-ups accelerate price slippage.\n\nEvaluating stocks through a composite Quantitative Risk Engine changes the math. Combining Wilder's ATR(14), Historical Volatility spreads (HV20 vs HV30), relative volume anomalies (RVOL), and maximum drawdown clustering isolates structural accumulation from institutional liquidation.\n\nFundamental metrics tell you what a company might be worth in equilibrium. Quantitative microstructure and volatility surfaces tell you what market participants are actually paying for liquidity right now.",
            "cta": f"Screen Indian equities with mathematical risk scoring, RVOL metrics, and historical volatility profiles on the Aegis Quant Screener: {AEGIS_URL}",
            "hashtags": ["#QuantitativeFinance", "#SystematicInvesting", "#StockScreener", "#VolatilityAnalysis", "#RiskManagement", "#AegisQuant"]
        },
        {
            "hook": "Most risk management models measure volatility through standard deviation.\nIn fat-tailed equity markets, standard deviation systematically conceals tail-risk kurtosis.",
            "body": "Assuming normal distributions in equity returns leads to catastrophic risk miscalculation. A 4-standard-deviation daily move should theoretically occur once every 126 years in a Gaussian world; in empirical equity data across the NSE and NYSE, 4-sigma gap events occur roughly every 14 to 18 months.\n\nInstitutional quantitative screeners model risk through Historical Volatility spreads (HV20 vs HV30), Wilder's ATR% of stock price, and maximum drawdown persistence. When HV20 sharply exceeds HV30 while price consolidates near support, it signals imminent volatility expansion—a regime where standard stop losses suffer maximum execution slippage.\n\nBy ranking securities across multi-factor volatility surfaces rather than static beta, quants eliminate high-kurtosis risk before entering positions, preserving capital when regime transitions trigger market-wide liquidity shocks.",
            "cta": f"Monitor real-time HV20, HV30, and composite Quant Risk Scores across Indian equities at Aegis Quant: {AEGIS_URL}",
            "hashtags": ["#Volatility", "#TailRisk", "#QuantScreener", "#RiskManagement", "#SystematicTrading", "#AegisQuant"]
        },
        {
            "hook": "Volatility clustering is not market noise; it is the physical fingerprint of institutional liquidity reallocation.\nIgnoring the spread between short-term HV and medium-term HV is why trend trades fail.",
            "body": "Mandelbrot observed that large price changes tend to be followed by large price changes, of either sign. In practical quantitative equity screening, when 20-day historical volatility (HV20) compresses below the 15th percentile of 60-day historical volatility (HV60), an energetic coiled spring is formed.\n\nBreakouts from severe volatility compression regimes exhibit twice the directional persistence of standard momentum signals. Conversely, entering after HV20 has already doubled its baseline exposes the portfolio to mean-reverting chop and adverse execution slippage.\n\nBy screening securities specifically during the pre-expansion consolidation window, systematic investors capture the meat of the move while maintaining mathematically defined, tight volatility stop thresholds.",
            "cta": f"Filter high-probability volatility compression setups across NSE/BSE on Aegis Quant Screener: {AEGIS_URL}",
            "hashtags": ["#VolatilityClustering", "#StockScreener", "#QuantitativeAnalysis", "#AlgorithmicTrading", "#AegisQuant"]
        }
    ],
    "factor_alpha": [
        {
            "hook": "Momentum is among the most pervasive anomalies in financial literature.\nYet when market regimes pivot, momentum crashes with greater velocity than almost any other systematic factor.",
            "body": "Momentum crashes are not random black swans; they are structural liquidity unwinds. During prolonged trends, long momentum portfolios become congested in high-beta names while short baskets concentrate heavily in distressed value equities. When an unexpected macroeconomic catalyst hits, beaten-down value names ignite violent short-covering rallies while crowded winners undergo forced liquidation.\n\nSystematic momentum strategies that fail to orthogonalize momentum against market beta and residual volatility suffer extreme left-tail drawdown events. By dynamically weighting momentum exposures by inverse trailing volatility and hedging factor crowding risk, systematic managers can eliminate up to 42% of factor drawdowns during sharp regime transitions.\n\nSimply ranking stocks by 12-month return is amateur quantitative modeling. True factor durability requires continuous risk decomposition and factor hygiene.",
            "cta": f"Read our complete mathematical analysis of momentum factor construction and risk mitigation on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#FactorInvesting", "#QuantitativeTrading", "#MomentumStrategy", "#RiskManagement", "#TheMacroLedger"]
        },
        {
            "hook": "Discounted cash flow models fail in changing macro regimes not because the mathematics are flawed, but because cost-of-capital assumptions remain static.\nValuation mechanics must adapt dynamically to term structure shifts.",
            "body": "When the weighted average cost of capital (WACC) shifts by 150 basis points due to sovereign bond yield repricing, terminal value calculations for growth equities can contract by upwards of 35%. Yet traditional equity research analysts often leave discount rates unchanged for quarters.\n\nSystematic valuation frameworks link discount rates directly to real-time credit default spreads, sovereign curves, and market-implied equity risk premia. Point-in-time valuation surfaces reveal which market sectors are overpaying for duration and which offer genuine margin of safety under stressed liquidity regimes.\n\nIn our quantitative models, linking cash-flow duration to sovereign hurdle rates separates genuine compounders from capital-destroying balance sheets. Rigorous quantitative valuation is an active state-dependent exercise, not an annual spreadsheet update.",
            "cta": f"Explore our valuation mechanics and cross-asset research on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#ValuationMechanics", "#WACC", "#DiscountRates", "#EquityResearch", "#TheMacroLedger"]
        },
        {
            "hook": "The Value factor has underperformed for long stretches not because valuation doesn't matter, but because traditional book-to-price metrics measure obsolete balance sheet accounting.\nIn knowledge-based economies, intangible capital dominates tangible assets.",
            "body": "Fama and French originally defined Value using book-to-market. In modern markets, capitalizing R&D expenses and intellectual property adjustments fundamentally inverts the Value rank order across S&P 500 and mid-cap equities.\n\nCompanies trading at optically high price-to-book multiples frequently possess massive, uncapitalized operational moats and high cash-flow reinvestment rates. Naive value screeners systematically buy balance sheet distress while shunning high-ROIC compounders.\n\nTrue factor alpha requires dynamic adjustments for intangible amortization, lease capitalization, and cash-flow durability. When value is measured by real cash-flow yields rather than backward accounting book value, the factor alpha reappears with statistical significance.",
            "cta": f"Discover our updated quantitative factor architectures on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#FactorInvesting", "#ValueFactor", "#FinancialModeling", "#QuantResearch", "#TheMacroLedger"]
        }
    ],
    "volume_rvol": [
        {
            "hook": "Over 70% of breakout trading setups fail within three sessions.\nThe reason is structural: price breached a technical resistance level, but liquidity never confirmed institutional commitment.",
            "body": "A breakout occurring on 1.1x normal volume has roughly 50/50 odds of mean-reverting straight back into the consolidation range. However, when price expansion coincides with Relative Volume (RVOL) exceeding 2.5x and the ATR(14) expands below historical volatility threshold ceilings, the empirical persistence of follow-through surges past 63% across liquid equities.\n\nRVOL normalizes volume against its 20-day moving average, stripping out intraday noise and pinpointing genuine institutional footprint. When combined with HV20 volatility contraction prior to the move, it distinguishes high-probability volatility expansions from false retail traps.\n\nStop drawing subjective trendlines on bare charts. Mathematical screeners that rank securities by RVOL anomalies, ATR expansion, and composite quantitative risk scores give you quantifiable statistical edge.",
            "cta": f"Filter NSE and BSE equities by institutional RVOL surges and mathematical risk metrics on Aegis Quant Screener: {AEGIS_URL}",
            "hashtags": ["#SystematicTrading", "#VolumeProfile", "#TechnicalAnalysis", "#QuantTrading", "#StockScreener", "#AegisQuant"]
        },
        {
            "hook": "High trading volume is meaningless unless normalized against the time-of-day distribution.\nA 100,000-share print at 09:20 AM carries a completely different statistical weight than at 01:30 PM.",
            "body": "Intraday volume follows a well-known U-shaped curve: heavy at the open, declining through midday, and surging again into the closing bell. Traditional volume moving averages fail because they treat midday liquidity identically to opening cross volatility.\n\nRelative Volume (RVOL) solves this by comparing cumulative volume at any specific minute of the session against the average volume executed by that exact minute over the preceding 20 trading sessions. When a stock displays an intraday RVOL > 3.0 during midday consolidation, it signals non-standard institutional accumulation or block rebalancing.\n\nQuant screeners equipped with session-aware RVOL engines enable systematic traders to detect institutional positioning hours before closing block prints appear on the tape.",
            "cta": f"Run session-aware RVOL and volume anomaly scans across Indian markets on Aegis Quant: {AEGIS_URL}",
            "hashtags": ["#RVOL", "#Microstructure", "#QuantScreener", "#AlgorithmicTrading", "#AegisQuant", "#Equities"]
        },
        {
            "hook": "Volume at price tells you who won the auction; volume at time merely tells you when the bell rang.\nMicrostructure order flow reveals institutional accumulation before price breaks out.",
            "body": "When a security consolidates inside a tight range, standard technical indicators often read neutral or oversold. Yet, looking deeper at Volume-Weighted Average Price (VWAP) drift and volume skewness reveals whether smart money is absorbing supply or distributing into retail bids.\n\nIf cumulative volume delta slopes upward while price remains pinned below resistance, absorption is occurring. The moment supply exhaustion is reached, a modest volume surge triggers rapid upward price re-rating as liquidity providers pull asks.\n\nScreening for volume skewness combined with RVOL thresholds gives quant traders the statistical edge required to position ahead of momentum runs rather than chasing late.",
            "cta": f"Uncover institutional accumulation patterns with Aegis Quant Screener's real-time microstructure metrics: {AEGIS_URL}",
            "hashtags": ["#OrderFlow", "#Microstructure", "#VolumeAnalysis", "#QuantScreening", "#AegisQuant"]
        }
    ],
    "backtest_execution": [
        {
            "hook": "If your strategy backtest boasts an annualized Sharpe ratio of 2.8 with zero flat years, you haven't discovered the Holy Grail.\nYou've likely just baked in survivorship and lookahead bias.",
            "body": "In quantitative equity research, omitting delisted securities artificially inflates historical returns by 250 to 450 basis points annually. When coupled with idealized fill assumptions, zero market impact models, and unadjusted dividend adjustments, paper strategies boasting +25% CAGR often deliver negative real-world alpha once deployed live.\n\nRobust quantitative research demands strict point-in-time constituent universes, execution lag simulation (T+1 open fills rather than T close), and combinatorial walk-forward cross-validation. An edge that cannot survive aggressive slippage assumptions and transaction costs is not an edge; it is an artifact of overfitted noise.\n\nThe primary objective of systematic backtesting is not to produce an impressive backtest curve to admire; it is an adversarial engineering process designed to systematically break your hypotheses before the live market does.",
            "cta": f"Explore our institutional framework for bias-free backtesting and execution modeling on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#QuantitativeFinance", "#AlgorithmicTrading", "#Backtesting", "#FinancialEngineering", "#TheMacroLedger"]
        },
        {
            "hook": "Overfitting in quantitative trading is like memorizing the answers to last year's exam.\nYou get a perfect score on the practice test, but fail the live paper every single time.",
            "body": "When an analyst tests 200 combinations of moving averages and RSI thresholds to find the single curve that maximized returns over the past 5 years, they haven't discovered an economic principle. They have merely fit parameters to historical noise.\n\nTo combat parameter overfitting, institutional quant teams utilize Combinatorial Purged Cross-Validation (CPCV) and Deflated Sharpe Ratios (DSR). By penalizing performance based on the total number of historical hypotheses tested, DSR computes the true statistical probability that a strategy's observed Sharpe is genuine skill rather than lucky variance.\n\nIf a quantitative model lacks economic intuition and fails under out-of-sample perturbations, it should never be allocated live trading capital.",
            "cta": f"Read our deep dive on statistical deflated Sharpe ratios and cross-validation on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#MachineLearningInFinance", "#Backtesting", "#Overfitting", "#QuantResearch", "#TheMacroLedger"]
        }
    ],
    "cross_asset_momentum": [
        {
            "hook": "Most backtests fail not because the alpha died, but because retail backtesting treats market volatility as a stationary Gaussian distribution.\nMandelbrot proved in 1963 that volatility clusters—yet 90% of algorithmic trading systems still assume independent, identically distributed returns.",
            "body": "When 20-day Historical Volatility (HV20) surges past the 80th percentile relative to HV60, standard stop-losses trigger execution slippage that compounds drawdowns. Volatility-scaled position sizing (e.g. fixed volatility targeting at 12% annualized) dramatically compresses maximum drawdown from -34% to -14.2% across a 15-year equity curve, without reducing terminal Sharpe ratio.\n\nQuants obsessed with optimizing entry indicators (RSI, MACD, Moving Average crossovers) are solving the wrong problem. Your edge is not where you enter; your edge is dynamic volatility-adjusted exposure.\n\nBy systematically cutting gross exposure when volatility regimes spike and increasing leverage during low-volatility drift, systematic models smooth returns and avoid catastrophic left-tail liquidation cascades.",
            "cta": f"Read the complete quantitative research and Tape Notes on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#QuantitativeFinance", "#SystematicTrading", "#AlgorithmicTrading", "#Volatility", "#TheMacroLedger"]
        },
        {
            "hook": "Modern portfolio theory tells you to diversify across asset classes.\nIn liquidity shock events, asset correlations converge toward 1.0, rendering static diversification useless.",
            "body": "During the 2008 GFC, March 2020 COVID selloff, and 2022 inflation shock, traditional correlations between equities, emerging markets, corporate bonds, and commodities vanished as institutional margin calls forced indiscriminate selling across all liquid assets.\n\nSystematic multi-asset allocators protect capital through risk-parity budgeting combined with dynamic trend filters. By targeting equal risk contribution rather than equal dollar allocation, and overlaying time-series momentum (TSMOM) across futures contracts, trend-following CTAs generated positive alpha in 2008 (+18%) and 2022 (+21%) while standard balanced portfolios suffered 20%+ drawdowns.\n\nTrue portfolio diversification is not holding multiple assets that rise together; it is holding orthogonal risk streams that carry positive expected carry across distinct macro regimes.",
            "cta": f"Learn how to build institutional multi-asset trend following and risk parity models on The Macro Ledger: {SUBSTACK_URL}",
            "hashtags": ["#RiskParity", "#TrendFollowing", "#CrossAsset", "#AssetAllocation", "#TheMacroLedger"]
        }
    ]
}


def load_history() -> List[dict]:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Could not load post history: {e}")
            return []
    return []


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def is_slot_already_posted(date_str: str, slot_num: int, history: List[dict] = None) -> bool:
    """Checks if a given slot number has already been successfully posted on a specific date."""
    if history is None:
        history = load_history()
    for item in history:
        if item.get("date_ist") == date_str and item.get("slot_num") == slot_num and item.get("success"):
            return True
    return False


def generate_post_content(slot: Dict[str, Any], history: List[dict] = None) -> Dict[str, Any]:
    cat = slot.get("category", "macro_rates")
    target = slot.get("target", "The Macro Ledger (Substack)")
    options = CONTENT_VAULT.get(cat, CONTENT_VAULT["macro_rates"])
    
    # Avoid reusing recently posted hooks
    recent_hooks = [h.get("text", "")[:45] for h in (history or []) if h.get("success")]
    fresh_options = [opt for opt in options if opt["hook"][:45] not in recent_hooks]
    chosen = random.choice(fresh_options) if fresh_options else random.choice(options)
    
    full_text = f"{chosen['hook']}\n\n{chosen['body']}\n\n{chosen['cta']}\n\n{' '.join(chosen['hashtags'])}"
    words = full_text.split()
    
    return {
        "slot_num": slot.get("slot_num"),
        "time_ist": slot.get("time_ist"),
        "target": target,
        "url": slot.get("url"),
        "category": cat,
        "word_count": len(words),
        "text": full_text
    }


def publish_post_to_composio(post_text: str) -> dict:
    """Executes LinkedIn publish via Composio API endpoint."""
    ctx = ssl._create_unverified_context()
    headers = {
        "x-api-key": COMPOSIO_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "connected_account_id": CONNECTED_ACCOUNT_ID,
        "user_id": USER_ID,
        "entity_id": ENTITY_ID,
        "arguments": {
            "author": AUTHOR_URN,
            "commentary": post_text,
            "visibility": "PUBLIC"
        }
    }
    endpoint = "https://backend.composio.dev/api/v3.1/tools/execute/LINKEDIN_CREATE_LINKED_IN_POST"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=35) as resp:
            res = json.loads(resp.read().decode())
            data = res.get("data", {})
            share_id = data.get("x_restli_id", "")
            link = f"https://www.linkedin.com/feed/update/{share_id}" if share_id else ""
            return {
                "success": res.get("successful", False),
                "share_id": share_id,
                "link": link,
                "raw": res
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        log.error(f"HTTP Error {e.code}: {err_msg}")
        return {"success": False, "error": f"HTTP {e.code}: {err_msg}"}
    except Exception as e:
        log.error(f"Exception during LinkedIn publish: {e}")
        return {"success": False, "error": str(e)}


def execute_slot(slot: Dict[str, Any], dry_run: bool = False) -> bool:
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
    
    log.info(f"Executing Slot #{slot['slot_num']} ({slot['time_ist']} IST) -> Target: {slot['target']}")
    history = load_history()
    
    post_data = generate_post_content(slot, history=history)
    print("\n" + "=" * 65)
    print(f"SLOT #{post_data['slot_num']} | TARGET: {post_data['target']} | WORDS: {post_data['word_count']}")
    print("=" * 65)
    print(post_data["text"])
    print("=" * 65 + "\n")
    
    if dry_run:
        log.info("[DRY RUN] Verification successful. Post not dispatched to LinkedIn.")
        return True
        
    result = publish_post_to_composio(post_data["text"])
    
    entry = {
        "date_ist": date_str,
        "timestamp_ist": timestamp_str,
        "slot_num": post_data["slot_num"],
        "scheduled_time_ist": slot["time_ist"],
        "target": post_data["target"],
        "category": post_data["category"],
        "word_count": post_data["word_count"],
        "text": post_data["text"],
        "success": result.get("success", False),
        "share_id": result.get("share_id", ""),
        "link": result.get("link", ""),
        "error": result.get("error", None)
    }
    save_history(entry)
    
    if result.get("success"):
        log.info(f"✅ Published LIVE to LinkedIn! Share ID: {result.get('share_id')} | Link: {result.get('link')}")
        return True
    else:
        log.error(f"❌ Failed to publish Slot #{slot['slot_num']}: {result.get('error')}")
        return False


def run_catch_up(dry_run: bool = False):
    """
    Scans all 6 slots for today in IST.
    Any slot whose scheduled time has already arrived and has NOT been posted yet today
    is executed immediately.
    """
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    current_minutes = now_ist.hour * 60 + now_ist.minute
    
    log.info(f"Running catch-up engine for {date_str} at {now_ist.strftime('%H:%M:%S IST')}...")
    history = load_history()
    
    pending_slots = []
    for s in SLOTS:
        h, m = map(int, s["time_ist"].split(":"))
        slot_mins = h * 60 + m
        # If the slot time is now or has already passed today
        if slot_mins <= current_minutes:
            if not is_slot_already_posted(date_str, s["slot_num"], history):
                pending_slots.append(s)
            else:
                log.info(f"Slot #{s['slot_num']} ({s['time_ist']} IST - {s['target']}) is ALREADY posted today.")
        else:
            log.info(f"Slot #{s['slot_num']} ({s['time_ist']} IST - {s['target']}) is upcoming later today.")

    if not pending_slots:
        log.info("🎉 All due slots for today are already posted! No catch-up needed.")
        return

    log.info(f"Found {len(pending_slots)} pending due slot(s) for today. Executing in sequence...")
    for s in pending_slots:
        execute_slot(s, dry_run=dry_run)


def show_status():
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    history = load_history()
    
    print("\n" + "=" * 65)
    print(f"AEGIS QUANT LINKEDIN AUTOPOSTER STATUS — {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 65)
    
    today_posts = [p for p in history if p.get("date_ist") == date_str and p.get("success")]
    print(f"Today's Completed Posts: {len(today_posts)} / 6\n")
    
    for s in SLOTS:
        posted = next((p for p in today_posts if p.get("slot_num") == s["slot_num"]), None)
        status_sym = "✅ POSTED" if posted else "⏳ PENDING"
        share_info = f"({posted.get('link')})" if posted else ""
        print(f"Slot #{s['slot_num']} | {s['time_ist']} IST | {s['target']:<28} | {status_sym} {share_info}")
    
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis Quant & Macro Ledger LinkedIn Autoposter")
    parser.add_argument("--slot", type=int, choices=range(1, 7), help="Execute a specific slot number (1-6)")
    parser.add_argument("--catch-up", action="store_true", help="Idempotently post any due slots that haven't posted yet today")
    parser.add_argument("--dry-run", action="store_true", help="Preview post without publishing")
    parser.add_argument("--status", action="store_true", help="Show current posting status for today")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.slot:
        target_slot = next((s for s in SLOTS if s["slot_num"] == args.slot), None)
        execute_slot(target_slot, dry_run=args.dry_run)
    else:
        # Default behavior for crons is catch-up: ensure all due slots are posted
        run_catch_up(dry_run=args.dry_run)
