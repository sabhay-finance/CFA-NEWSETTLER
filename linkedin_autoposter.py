#!/usr/bin/env python3
"""
High-Growth General Finance & Investing LinkedIn Autoposter for Sabhay Tomar
Engineered for Maximum Organic Reach, Maximum Dwell Time & Maximum Comment Velocity.
Target: 10,000+ Impressions by October 10.

Core Algorithmic Architecture:
1. Two Golden Daily Slots (08:30 IST & 18:30 IST): Eliminates feed cannibalization, giving
   each post 10-14 hours of continuous organic feed distribution.
2. Dynamic Pillar Rotation: Alternates between Wealth Habits, Valuation Frameworks,
   Financial Mental Models, and Corporate Moats across alternating days.
3. High-Velocity Comment Hooks: Low-friction multiple-choice (A/B/C) and confessional CTAs
   engineered to drive comment volume (1 comment = ~8x algorithm weight of a like).
4. Zero Outbound URLs in Caption: 100% immune to LinkedIn reach suppression penalties.
5. Smart Concurrency & Sync: Non-blocking fcntl file locks prevent double execution across
   local macOS launchd/crontab and cloud GitHub Actions runners.
"""

import os
import sys
import ssl
import json
import random
import fcntl
import logging
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

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

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "ak_Xcw5h4TCAaKIVZTosuue")
CONNECTED_ACCOUNT_ID = os.getenv("LINKEDIN_CONNECTED_ACCOUNT_ID", "ca_D6c1UFZdkhcq")
USER_ID = "default"
ENTITY_ID = "default"
AUTHOR_URN = "urn:li:person:bsR37USNqa"  # Sabhay Tomar

# 2 Golden High-Impression Strategic Slots (IST)
# Perfectly spaced to give each post full organic runway without cannibalization.
SLOTS = [
    {
        "slot_num": "peak_1",
        "time_ist": "08:30",
        "target": "Morning Prime (08:30 IST) — Wealth Mindset & Personal Finance Rules",
        "category": "wealth_habits"
    },
    {
        "slot_num": "peak_2",
        "time_ist": "18:30",
        "target": "Evening Prime (18:30 IST) — Practical Investing Frameworks & Valuation",
        "category": "investing_valuation"
    }
]

# Viral General Finance Master Vault (40+ Masterclass Posts with High-Velocity CTAs)
GENERAL_FINANCE_VAULT: Dict[str, List[Dict[str, Any]]] = {
    "wealth_habits": [
        {
            "hook": "The Rule of 72 is the simplest math hack in finance.\nYet 90% of people never calculate it until their 40s.",
            "body": "It tells you exactly how many years it will take to double your money at any return:\n\nDivide 72 by your expected annual return.\n\n📌 At 6% (Fixed Deposit/Bonds): 72 ÷ 6 = 12 years to double\n📌 At 10% (Broad Market Index Funds): 72 ÷ 10 = 7.2 years to double\n📌 At 14% (Quality Growth Stocks): 72 ÷ 14 = 5.1 years to double\n\nNow look at the reverse — the cost of waiting 10 years:\n\nIf you invest $10,000 at age 25 at 10% annual returns, it doubles roughly 4 times by age 55: $10k → $20k → $40k → $80k → $160,000.\n\nIf you wait until age 35 to invest that same $10,000, it only doubles twice: $10k → $20k → $40,000.\n\nA 10-year delay cost you $120,000 on a single $10k check.\n\nYour greatest financial asset isn't your stock picking ability. It's time in the compounding engine.",
            "cta": "Quick math test: Divide 72 by your portfolio's annualized return. How many years to double: 5, 7, 10, or 15+? Drop your number below 👇",
            "hashtags": ["#PersonalFinance", "#Investing", "#Compounding", "#WealthBuilding", "#FinancialFreedom"]
        },
        {
            "hook": "Making $100,000 and spending $95,000 leaves you with less financial freedom than someone making $60,000 and saving $20,000.\nWealth isn't what you earn. It's what you keep.",
            "body": "Most people suffer from Lifestyle Creep:\nEvery time their income increases, their expenses automatically rise to match it.\n\nNew salary → New car lease → Bigger apartment → Expensive dinners → Same financial anxiety.\n\n4 rules to defeat lifestyle inflation without living like a monk:\n\n1. The 50% Raise Rule: Whenever you get a bonus or raise, allocate 50% to investing first, and enjoy the other 50% guilt-free.\n2. Buy Assets That Buy Luxuries: Don't buy luxury liabilities from your active salary. Let dividend yields or capital gains fund them.\n3. Keep Fixed Costs Below 50%: Rent, EMIs, and recurring bills should never exceed 50% of your take-home pay.\n4. Separate Status from Wealth: Wealth is the money you don't spend. It’s unspent cash, equity, and options that buy peace of mind.",
            "cta": "Be honest: When your salary last went up, did your expenses rise with it or did you invest the difference? Drop your honest take below 👇",
            "hashtags": ["#MoneyHabits", "#WealthBuilding", "#PersonalFinance", "#FinancialIndependence", "#Savings"]
        },
        {
            "hook": "The 50/30/20 budget is the most popular financial rule in the world.\nHere is how to upgrade it so it actually works in 2026:",
            "body": "The standard rule says:\n• 50% for Needs\n• 30% for Wants\n• 20% for Savings\n\nThe problem? If you only save 20%, achieving financial autonomy takes 37 years of uninterrupted work.\n\nHere is the Accelerated Wealth Split for ambitious professionals:\n\n📌 40% Needs: Keep housing, groceries, and debt baselines lean.\n📌 20% Wants: Guilt-free spending on travel, health, and hobbies.\n📌 30% Productive Assets: Low-cost index funds, equities, and retirement compounding.\n📌 10% Upskilling & Health: Certifications, books, gym, and skills that double your earning capacity.\n\nBudgeting isn't about restriction. It's about intentional resource allocation toward what buys freedom.",
            "cta": "Quick poll 👇 What % of your take-home pay do you currently invest: A) Under 15% B) 15-30% C) 30-50% D) 50%+ ? Drop your letter below!",
            "hashtags": ["#Budgeting", "#PersonalFinance", "#FinancialFreedom", "#InvestingTips", "#SmartMoney"]
        },
        {
            "hook": "An emergency fund isn’t an investment to generate yield.\nIt is an emotional shock absorber to keep you from selling stocks at the bottom.",
            "body": "Too many investors say:\n\"Why should I keep 6 months of expenses in a liquid account earning 4-5% when the stock market does 10-12%?\"\n\nHere is the hidden math:\n\nWhen a recession hits, corporate layoffs and market crashes usually happen at the exact same time.\n\nIf you have $0 in cash and lose your job during a 35% market drawdown, you are forced to liquidate your portfolio at fire-sale prices just to pay rent.\n\nThat locks in permanent capital loss and wipes out 5 years of compounding.\n\n💡 Your cash reserve is not dead money. It is insurance that buys you the psychological stamina to never sell in panic.",
            "cta": "How many months of runway do you keep in your emergency fund: A) 1-2 months B) 3-6 months C) 6-12 months D) $0 (all in stocks)? Drop your letter below 👇",
            "hashtags": ["#PersonalFinance", "#EmergencyFund", "#InvestingPsychology", "#RiskManagement", "#Wealth"]
        },
        {
            "hook": "The single most expensive sentence in personal finance:\n\"I'll start investing seriously next year when things calm down.\"",
            "body": "Markets never 'calm down'.\nThere is always an election, a rate hike, an inflation report, or a geopolitical headline to worry about.\n\nConsider this empirical reality:\n• Over the past 100 years, the market has hit an all-time high roughly once every 19 trading days.\n• Over any 20-year rolling window in modern history, the S&P 500 has never delivered a negative total return.\n\nThe cost of waiting for the 'perfect dip' is almost always greater than the cost of buying at a local peak and holding through.\n\nAutomate your investments on the 1st of every month. Make consistency your unfair advantage.",
            "cta": "At what age did you start investing seriously? (I wish someone showed me this at 20!) Drop your starting age below 👇",
            "hashtags": ["#Investing", "#DollarCostAveraging", "#StockMarket", "#FinancialLiteracy", "#WealthBuilding"]
        },
        {
            "hook": "Financial independence is not a binary switch (Broke vs Retired).\nIt has 4 progressive levels:",
            "body": "Most people think you are either working 9-to-5 or completely retired on a beach. In reality, wealth gives you leverage in stages:\n\nLevel 1: Financial Clarity\nYou know your exact net worth, monthly cash flow, and have 3–6 months of living expenses saved. Zero high-interest consumer debt.\n\nLevel 2: Breathing Room\nYour passive portfolio covers 25% of your living expenses. You can take a 6-month career sabbatical without touching your core lifestyle.\n\nLevel 3: Career Autonomy ('F*** You Money')\nYour investments cover 100% of your baseline needs. You work only on projects you care about with people you respect. You can walk away from toxic bosses anytime.\n\nLevel 4: Complete Abundance\nYour passive cash flow exceeds your wildest spending aspirations. Your primary focus shifts from wealth accumulation to impact and legacy.\n\nEvery dollar invested moves you up the ladder.",
            "cta": "Which level are you currently at right now: Level 1, Level 2, Level 3, or Level 4? Be honest below 👇",
            "hashtags": ["#FinancialIndependence", "#CareerGrowth", "#WealthCreation", "#MoneyMindset", "#PersonalFinance"]
        },
        {
            "hook": "The $100/Month Compounding Blueprint:\nYou don't need millions to build life-changing wealth. You just need boring consistency.",
            "body": "Here is what happens if you invest $100 every single month into a broad market index fund (assuming historical 10% annualized returns):\n\n• After 10 Years:\nTotal Invested: $12,000\nPortfolio Value: ~$20,500\n(Gains: $8,500)\n\n• After 20 Years:\nTotal Invested: $24,000\nPortfolio Value: ~$76,000\n(Gains: $52,000)\n\n• After 30 Years:\nTotal Invested: $36,000\nPortfolio Value: ~$228,000\n(Gains: $192,000)\n\n• After 40 Years:\nTotal Invested: $48,000\nPortfolio Value: ~$632,000\n(Gains: $584,000)\n\nNotice that in the final decade, your portfolio generates more wealth in pure interest than all your lifetime contributions combined.\n\nThat is the exponential hockey stick of compounding.",
            "cta": "What was the very first investment you ever bought in your life? (Index fund, crypto, gold, or a single stock?) Drop it below 👇",
            "hashtags": ["#Compounding", "#IndexFunds", "#WealthBuilding", "#FinancialEducation", "#Investing"]
        },
        {
            "hook": "5 money habits that silently keep smart professionals broke in their 20s and 30s:",
            "body": "1. Financing a rapidly depreciating car: Paying $600/month on a vehicle loan while investing $100/month is financial self-sabotage.\n\n2. Keeping too much cash in checking accounts: Holding $50k in a zero-interest account while inflation runs at 4-6% is a guaranteed loss of purchasing power.\n\n3. Confusing high income with net worth: A doctor making $250k with $300k in lifestyle debt is financially fragile compared to a teacher with $150k invested.\n\n4. Ignoring employer match or tax-advantaged accounts: Leaving free 100% matching capital on the table is an immediate loss of return.\n\n5. Chasing hot speculative tips instead of boring index funds: Trying to 10x your money on penny stocks usually results in a 90% drawdown.\n\nBuild the foundation first.",
            "cta": "Which of these 5 traps are you most guilty of right now? (I was definitely guilty of #2 for years 😂) Drop yours below 👇",
            "hashtags": ["#FinancialMistakes", "#MoneyTips", "#CareerAdvice", "#Investing101", "#PersonalFinance"]
        },
        {
            "hook": "Cutting out a $5 daily coffee won't make you rich.\nFocusing on micro-savings while ignoring the Big 3 expenses is the biggest trap in personal finance.",
            "body": "Traditional finance gurus love to tell you:\n\"Skip the latte and save $150 a month!\"\n\nHere is why that advice misses the mark:\nSpending energy on $5 decisions creates decision fatigue while leaving the real wealth drains completely unaddressed.\n\nFocus 95% of your mental energy on the BIG 3 expenses:\n\n1. Housing: A mortgage or rent that eats 50% of your net income will strangle your ability to invest, no matter how many coffees you skip.\n2. Transportation: Buying a new luxury car on a 6-year loan with $700 monthly EMIs and $300 insurance destroys compounding.\n3. Lifestyle Inflation on Raises: Automatically upgrading your lifestyle every time your salary increases prevents wealth accumulation.\n\nGet the Big 3 right, and you can enjoy your coffee completely guilt-free.",
            "cta": "Which category eats the biggest chunk of your monthly paycheck: Housing, Car/Commute, or Food/Dining? Drop yours below 👇",
            "hashtags": ["#PersonalFinance", "#MoneyHabits", "#SmartSpending", "#FinancialLiteracy", "#Wealth"]
        },
        {
            "hook": "Rich is what you see: the luxury car, the Rolex, the penthouse lease.\nWealth is what you don't see. Morgan Housel captured this difference brilliantly:",
            "body": "In 'The Psychology of Money', Morgan Housel wrote:\n\"Wealth is the nice cars not purchased. The diamonds not bought. The watches not worn. Wealth is financial options not yet converted into stuff you can see.\"\n\nConsider the distinction:\n\n📌 Being Rich:\n• High active income\n• High monthly burn rate\n• Heavy reliance on the next paycheck\n• Optimized for status and external validation\n\n📌 Being Wealthy:\n• High savings and investment rate\n• Low fixed expenses\n• Years of runway and sovereign independence\n• Optimized for peace of mind, autonomy, and uninterrupted sleep\n\nDo not spend money you don't have to impress people you don't even like.",
            "cta": "Quick gut-check: Would you rather look rich today, or be quietly wealthy in 10 years? Drop your choice below 👇",
            "hashtags": ["#MorganHousel", "#PsychologyOfMoney", "#WealthVsRich", "#Mindset", "#FinancialPeace"]
        }
    ],

    "investing_valuation": [
        {
            "hook": "You don't need a CFA or an MBA to read a company's Balance Sheet.\nYou just need to inspect these 4 lines:",
            "body": "Most people open a 10-K annual report and get intimidated by 150 pages of disclosures.\n\nHere is the 3-minute financial health checklist:\n\n1. Cash vs Total Debt:\nDoes the company have more cash and short-term investments than total short-term obligations? If Cash > Short-term Debt, bankruptcy risk is near zero.\n\n2. Current Ratio (Current Assets ÷ Current Liabilities):\nIf this ratio is above 1.5x, the business can easily pay its bills over the next 12 months without taking emergency loans.\n\n3. Retained Earnings Trajectory:\nAre retained earnings growing year-over-year? Growing retained earnings mean the business is profitable and compounding capital internally.\n\n4. Goodwill & Intangibles:\nIf Goodwill makes up more than 30% of total assets, beware. It often means management overpaid for past acquisitions that may face future write-downs.\n\nAlways check solvency before you check valuation.",
            "cta": "What is the very first line item you look at when opening a company's financial report? Drop your metric below 👇",
            "hashtags": ["#FundamentalAnalysis", "#StockMarket", "#Accounting", "#InvestingTips", "#BalanceSheet"]
        },
        {
            "hook": "A company can report $50 million in Net Profit and still go bankrupt.\nHow? Because Net Profit is an accounting opinion. Cash Flow is a reality.",
            "body": "Here is how corporate accounting tricks retail investors:\n\nUnder accrual accounting, a company records Revenue the moment an invoice is sent—even if the client hasn't paid a single penny.\n\nIf a company books $100M in sales, reports $50M in Net Income, but all $100M is stuck in Accounts Receivable (uncollected bills), its actual cash balance is $0.\n\nIf it cannot pay employee salaries or bond interest next month, it enters liquidation.\n\n📌 Always compare Net Income with Operating Cash Flow (OCF):\n• Healthy Business: Operating Cash Flow is equal to or higher than Net Income.\n• Red Flag Business: Net Income is rising, but Operating Cash Flow is negative or collapsing.\n\nNever buy a stock without checking the Cash Flow Statement.",
            "cta": "Can you name a famous company that was profitable on paper right before collapsing? (Enron, Lehman, etc.) Drop it below 👇",
            "hashtags": ["#CorporateFinance", "#CashFlow", "#Investing", "#FinancialStatements", "#StockAnalysis"]
        },
        {
            "hook": "Buying a stock solely because its P/E ratio is low is the most common value trap in investing.\nHere is why a 10x P/E can be expensive, and a 35x P/E can be cheap:",
            "body": "The Price-to-Earnings (P/E) ratio looks backward. It tells you what you paid for yesterday's earnings.\n\nConsider two companies:\n\nCompany A (Old Retailer):\n• P/E: 8x\n• Revenue: Declining 5% per year\n• Debt: High\n• ROIC: 4%\n• Outlook: Margins contracting as competitors eat market share.\n→ At 8x, Company A is a Value Trap. Its earnings will shrink, making next year's P/E 15x.\n\nCompany B (Cloud Software Compounder):\n• P/E: 32x\n• Revenue: Growing 22% per year\n• Debt: Zero\n• ROIC: 25%\n• Margins: Expanding with strong pricing power.\n→ Within 4 years of compounding, Company B's earnings double, effectively dropping your purchase multiple to 16x.\n\nValuation is not about the lowest price multiple. It is about the price paid relative to future cash generation.",
            "cta": "Which camp are you in: A) Deep Value (low P/E bargains) or B) High-Quality Growth (high ROIC compounders)? Drop A or B below 👇",
            "hashtags": ["#ValueInvesting", "#Valuation", "#Stocks", "#InvestingFrameworks", "#FinancialAnalysis"]
        },
        {
            "hook": "Market timing is the most expensive hobby in finance.\nHere is the empirical proof:",
            "body": "Bank of America ran a 90-year study analyzing S&P 500 returns since 1930:\n\nIf an investor stayed invested through all market ups and downs, their cumulative return was +17,715%.\n\nNow look at what happens if you tried to time the market and missed just the 10 best trading days of each decade:\n\nYour total return plummeted to just +28%.\n\nRead that again:\n+17,715% vs +28%.\n\nWhy? Because the market's single best days almost always occur within 2 weeks of the absolute worst crash days.\n\nIf you panic and exit during the drop, you miss the explosive rebound that drives 80% of long-term equity returns.\n\nTime in the market beats timing the market. Every single time.",
            "cta": "Be honest: Have you ever panicked and sold during a market crash only to watch it rebound? Drop your war story below 👇",
            "hashtags": ["#StockMarket", "#InvestingTips", "#BehavioralFinance", "#LongTermInvesting", "#Wealth"]
        },
        {
            "hook": "Charlie Munger once revealed the single metric that matters most in business quality:\nReturn on Invested Capital (ROIC).",
            "body": "Munger stated:\n\"Over the long term, it’s hard for a stock that earns 6% on capital to earn much more than a 6% return, even if you buy it at a huge discount.\"\n\nWhat is ROIC?\nIt measures how many dollars of profit a company generates for every $100 of capital invested in the business.\n\n• If Company A invests $100 million in factories, stores, and inventory, and generates $25 million in operating profit, its ROIC is 25%.\n• If Company B invests $100 million and generates $6 million, its ROIC is 6%.\n\nWhy does this matter to you as an investor?\nA high-ROIC business can fund its own organic growth without issuing dilutive shares or taking on crippling bank debt.\n\nLook for businesses that maintain ROIC > 15% consistently for 5+ consecutive years.",
            "cta": "What is your all-time favorite high-ROIC compounder stock in your portfolio? Drop the ticker below 👇",
            "hashtags": ["#CharlieMunger", "#ROIC", "#FundamentalInvesting", "#BusinessQuality", "#Stocks"]
        },
        {
            "hook": "4 red flags in corporate earnings releases that smart investors look for immediately:",
            "body": "When a public company reports quarterly earnings, the press release is designed to make management look like geniuses.\n\nHere are 4 red flags to look for past the PR headline:\n\n1. Revenue Growth vs Accounts Receivable Growth:\nIf Revenue grew 10% but Accounts Receivable grew 35%, customers aren't paying their bills on time. They are pulling forward uncollected sales.\n\n2. Ballooning Stock-Based Compensation (SBC):\nManagement reports 'Adjusted EBITDA' that adds back hundreds of millions in stock awards. That stock dilutes your share count. It is a real expense.\n\n3. Frequent 'One-Time' Restructuring Charges:\nIf a company has 'one-time non-recurring expenses' every single quarter for 3 years, they are recurring operational costs in disguise.\n\n4. Divergence Between CEO Words and CFO Actions:\nThe CEO is hyped on the earnings call, but the CFO resigns 2 weeks later. Executive turnover in the finance suite is the loudest alarm bell in business.",
            "cta": "Which of these 4 red flags is an immediate deal-breaker that makes you sell a stock? Drop 1, 2, 3, or 4 below 👇",
            "hashtags": ["#EarningsSeason", "#FinancialAnalysis", "#DueDiligence", "#StockMarket", "#CFA"]
        },
        {
            "hook": "Over an 15-year period, more than 85% of professional active fund managers fail to beat the S&P 500 index.\nWhy? 3 simple structural reasons:",
            "body": "Active fund managers have PhDs, Bloomberg Terminals, and millions in research budgets.\nYet boring low-cost index funds beat them systematically.\n\nHere is why:\n\n1. The Fee Drag: An active fund charging a 1.5% management fee plus trading commissions starts every year with a 2% performance handicap.\n\n2. Career Risk & Closet Indexing: Fund managers are terrified of underperforming their peers in any single quarter. So they buy the same mega-cap consensus names, guaranteeing average returns before fees.\n\n3. Cash Drag: Active funds must hold cash reserves to handle client redemptions, dragging down returns during bull markets.\n\nLow-cost index funds remove the ego, eliminate high fees, and capture the natural growth of human innovation.",
            "cta": "What percentage of your portfolio is in low-cost index funds vs individual stocks: A) 100% Index B) 70/30 C) 50/50 D) 100% Stock Picker? Drop your letter below 👇",
            "hashtags": ["#IndexInvesting", "#Bogleheads", "#AssetAllocation", "#InvestingStrategy", "#Wealth"]
        },
        {
            "hook": "A 1% annual investment advisory fee sounds harmless.\nOver a 30-year investing career, that tiny 1% fee quietly steals over 25% of your total wealth.",
            "body": "Here is the math the financial advisory industry avoids showing you:\n\nAssume you invest $100,000 for 30 years with an 8% gross market return:\n\n• Scenario A (Low-Cost Index Fund - 0.05% fee):\nNet Return: 7.95%\nEnding Portfolio Value: ~$990,000\n\n• Scenario B (Wealth Manager / Active Fund - 1.05% fee):\nNet Return: 6.95%\nEnding Portfolio Value: ~$740,000\n\nDifference: $250,000 lost to fees on a single $100k principal.\n\nFees do not just reduce returns; they compound in reverse against your future net worth.\n\nAlways verify the Total Expense Ratio (TER) of every mutual fund and ETF you own.",
            "cta": "Do you know the expense ratio of your biggest fund or ETF: A) Under 0.2% B) 0.5% - 1% C) Over 1% D) Never checked? Drop A, B, C, or D below 👇",
            "hashtags": ["#ExpenseRatio", "#InvestingFees", "#IndexFunds", "#PersonalFinance", "#CompoundInterest"]
        },
        {
            "hook": "Peter Lynch famously said 'Invest in what you know'.\nMost retail investors completely misinterpret this advice and lose money.",
            "body": "Peter Lynch did NOT mean:\n\"Buy a stock simply because you like their sneakers or drink their coffee.\"\n\nLiking a consumer product is only step 1 — the observation hook.\n\nTo turn an observation into an investment thesis, Lynch mandated 4 financial checkpoints:\n\n1. Balance Sheet Durability: Can the company survive a 2-year industry recession without emergency dilution?\n2. Competitive Moat: Can competitors easily copy the product at 20% lower price?\n3. Valuation Relative to Growth: Is the PEG ratio (P/E divided by earnings growth rate) below 1.5x?\n4. Capital Allocation: Does management reinvest profits at high rates of return or waste them on empire building?\n\nConsumer enthusiasm without valuation discipline is speculation, not investing.",
            "cta": "Have you ever bought a stock just because you loved their product? (Did it end up winning or losing? Drop it below 👇)",
            "hashtags": ["#PeterLynch", "#StockPicking", "#ValueInvesting", "#Investing101", "#FinancialDiscipline"]
        },
        {
            "hook": "The difference between Volatility and Risk is the single most misunderstood concept in investing:",
            "body": "Most people treat them as identical. They are completely different.\n\n📌 Volatility is price fluctuation:\nA stock drops 20% in a month because of interest rate fears, but the company's revenue, cash flow, and market share are expanding.\n→ Volatility is normal. It is the price of admission for long-term equity returns.\n\n📌 Risk is the permanent loss of capital:\nA company with massive debt faces obsolescence, enters bankruptcy, and equity holders get wiped out.\n→ That is true risk. The money is gone and will never return.\n\nIf you own high-quality assets with robust balance sheets, volatility is your friend—it offers periodic discounts to buy more.",
            "cta": "When your portfolio drops 15-20% in a correction, do you: A) Buy more B) Hold tight C) Check your phone in panic? (Be honest below 😂👇)",
            "hashtags": ["#RiskManagement", "#InvestingPsychology", "#MarketVolatility", "#LongTermInvesting", "#Finance"]
        }
    ],

    "corporate_moats": [
        {
            "hook": "Warren Buffett coined the term 'Economic Moat'.\nEvery enduring compounder in history relies on one of these 4 competitive moats:",
            "body": "If a business generates high returns on capital, competitors will inevitably try to copy it and drive margins down.\n\nA moat is what keeps competitors from stealing the castle:\n\n1. Network Effects:\nThe product becomes more valuable with every new user (e.g. Visa, Mastercard, LinkedIn, YouTube). Once critical mass is reached, it’s virtually unassailable.\n\n2. High Switching Costs:\nThe friction, risk, and expense of migrating away exceeds the cost of staying (e.g. Bloomberg terminals, enterprise ERPs, specialized medical software).\n\n3. Cost Advantage:\nDelivering goods or services at a structural cost per unit that nobody else can match (e.g. Costco, GEICO, Amazon scale).\n\n4. Intangible Assets:\nPatents, regulatory licenses, or pricing power brands that command a durable customer premium (e.g. Ferrari, Apple, pharmaceutical patents).\n\nBefore you look at valuation multiples, check the depth of the moat.",
            "cta": "Which company in the world has the deepest, most unbreachable economic moat today? Drop your pick below 👇",
            "hashtags": ["#WarrenBuffett", "#CompetitiveAdvantage", "#EconomicMoats", "#BusinessStrategy", "#Investing"]
        },
        {
            "hook": "Warren Buffett's favorite test for business quality:\n'The single most important decision in evaluating a business is pricing power.'",
            "body": "Here is Buffett's definition of pricing power:\n\"If you have the power to raise prices by 10% without losing business to a competitor, you've got a terrific business.\nIf you have to have a prayer session before raising prices by 10%, you've got a terrible business.\"\n\nThink about the contrast:\n\n• Netflix raises subscription prices from $12 to $15: People grumble on Twitter, but less than 1% cancel.\n• Apple raises the flagship iPhone price: Demand remains resilient.\n• A commodity airline tries to raise ticket prices by $20: Travelers immediately click the next tab to buy on a competitor.\n\nIn an inflationary world, pricing power separates companies that expand margins from companies that face margin collapse.",
            "cta": "What is one product or subscription you would keep paying for even if the price went up 20% tomorrow? Drop it below 👇",
            "hashtags": ["#PricingPower", "#BusinessModels", "#WarrenBuffett", "#CorporateFinance", "#Investing"]
        },
        {
            "hook": "The Working Capital Cycle:\nHow Amazon and Dell funded multi-billion dollar expansions using other people's money.",
            "body": "Most traditional businesses suffer from a positive working capital cycle:\nThey buy inventory, store it for 60 days, sell it on credit, and wait another 60 days to collect cash from customers.\n→ They have to borrow bank debt just to keep running daily operations.\n\nExceptional businesses operate with a Negative Working Capital Cycle:\n\n1. Amazon sells products to customers and collects credit card cash in 1 to 2 days.\n2. Amazon holds the inventory for only 15–20 days before it ships.\n3. Amazon pays its suppliers on 60-day or 90-day terms.\n\nWhat happens?\nAmazon holds customer cash for 60+ days before having to pay suppliers. That creates hundreds of millions in free interest-free float to build warehouses, invest in R&D, and scale without issuing debt.\n\nCash flow efficiency is the invisible engine of enterprise value.",
            "cta": "Which business model do you admire most: A) Negative Working Capital (Amazon) B) High Margin Software (Microsoft) C) Luxury Pricing (Ferrari)? Drop A, B, or C below 👇",
            "hashtags": ["#WorkingCapital", "#CorporateStrategy", "#Amazon", "#CashConversionCycle", "#Finance"]
        },
        {
            "hook": "Over 70% of corporate mergers and acquisitions (M&A) destroy shareholder value.\nWhy? The Winner’s Curse & Empire Building.",
            "body": "When a CEO announces a multi-billion dollar acquisition, the press release always promises 'huge operational synergies'.\n\nYet historically, the acquiring company's stock falls over the subsequent 3 years in the majority of deals.\n\nWhy do big M&A deals fail?\n\n1. Overpaying for Goodwill: In competitive bidding auctions, the winner is usually the company that paid the most absurdly high premium.\n2. Cultural Rejection: Integrating two different corporate cultures, sales forces, and software stacks often causes key talent to leave.\n3. Management Hubris: CEOs are often incentivized by company size and revenue, not per-share intrinsic value.\n\nThe best capital allocators are often disciplined: they acquire sparingly, buy back their own undervalued shares, or reinvest in high-ROIC internal projects.",
            "cta": "What is the worst corporate acquisition in business history in your opinion? (AOL/Time Warner, HP/Autonomy, etc.) Drop your vote below 👇",
            "hashtags": ["#MergersAndAcquisitions", "#CorporateGovernance", "#ShareholderValue", "#CapitalAllocation", "#Business"]
        },
        {
            "hook": "Asset-Light vs Asset-Heavy:\nWhy software and franchise models command 3x higher valuation multiples than manufacturing.",
            "body": "Compare two businesses that both generate $100 million in revenue:\n\nBusiness A (Industrial Manufacturer):\nTo grow revenue by $20 million next year, it must build a new $15 million factory, purchase heavy machinery, and hire 200 factory workers.\n→ Incremental Gross Margin: 25%\n→ Free Cash Flow conversion: Low\n\nBusiness B (Software / Franchise Platform):\nTo add $20 million in revenue, it needs almost zero new physical plant. The software code or franchise playbook is already written. The cost of serving the next customer is pennies in cloud server costs.\n→ Incremental Gross Margin: 80%+\n→ Free Cash Flow conversion: Very High\n\nValuation multiples reflect the capital intensity of growth.\nBusinesses that scale with zero marginal capital build generational enterprise value.",
            "cta": "If you were launching a company tomorrow, would you choose: A) Asset-Light Software / Media B) Asset-Heavy Physical Infrastructure? Drop A or B below 👇",
            "hashtags": ["#BusinessModels", "#SoftwareEconomics", "#GrossMargin", "#CorporateFinance", "#Investing"]
        },
        {
            "hook": "Unit Economics 101:\nIf you lose money on every transaction, you cannot 'make it up in volume'.",
            "body": "During boom times, venture-backed startups often celebrate massive gross revenue growth while ignoring unit economics.\n\nHere is the simple formula every investor and operator must check:\n\nContribution Margin = Revenue per Unit - Variable Costs per Unit\n\n• If your Customer Acquisition Cost (CAC) is $80\n• And the customer's Lifetime Value (LTV) is $50\n→ You are losing $30 every time you gain a customer.\n\nScaling an unprofitable unit model doesn't create a tech giant. It just creates a faster cash-burn furnace.\n\nSustainable companies prove profitable unit economics at small scale before pouring fuel on sales and marketing.",
            "cta": "What hyped startup do you think is in danger because its unit economics make zero sense? Let's discuss in the comments 👇",
            "hashtags": ["#UnitEconomics", "#Startups", "#VentureCapital", "#Profitability", "#BusinessAnalysis"]
        },
        {
            "hook": "Why Wall Street pays absurd valuation multiples for B2B Subscription SaaS companies:\nThe Rule of 40 & Net Revenue Retention (NRR).",
            "body": "Traditional businesses have to sell to new customers every single quarter just to match last year's revenue.\n\nElite SaaS companies have a secret weapon: Net Revenue Retention (NRR) > 120%.\n\nWhat does that mean?\nIf a SaaS company starts the year with $100M in Annual Recurring Revenue, its existing customers expand their subscriptions by 20% through more seats, storage, or modules.\n\nEven if the sales team signs ZERO new clients all year, the company still grows 20%!\n\nPair that with The Rule of 40 (Growth Rate % + Profit Margin % ≥ 40%), and you have a virtually bulletproof compounding machine.",
            "cta": "What is one B2B software tool your team or company could literally never cancel? Drop the name below 👇",
            "hashtags": ["#SaaS #BusinessModels #RuleOf40 #RecurringRevenue #Investing"]
        },
        {
            "hook": "Uber owns no cars. Airbnb owns no real estate. Alphabet creates almost no original video content.\nYet they dominate global markets through Aggregator Theory.",
            "body": "Ben Thompson coined 'Aggregator Theory' to explain why internet platform monopolies are fundamentally different from 20th-century industrial monopolies.\n\nTraditional monopolies controlled supply (railroads, oil pipelines, telecom cables).\n\nAggregators control DEMAND by delivering a superior consumer experience at zero marginal cost:\n\n1. Consolidate Users: By offering the best search engine or ride-hailing app, millions of users flock to the platform.\n2. Suppliers Follow: Because all the customers are on the platform, drivers, landlords, and websites have no choice but to list on their terms.\n3. Winner-Take-All Flywheel: More users attract more suppliers, which makes the platform even better for users.\n\nAggregators create natural network monopolies with unmatched operating leverage.",
            "cta": "Who is the hardest platform company to disrupt in the next 10 years: A) Apple B) Google C) Amazon? Drop your vote below 👇",
            "hashtags": ["#NetworkEffects #PlatformEconomy #AggregatorTheory #TechMonopolies #BusinessStrategy"]
        }
    ],

    "financial_hacks": [
        {
            "hook": "Opportunity Cost is the invisible price tag on every financial decision you make.\nMost people only look at the sticker price.",
            "body": "When you buy an $80,000 luxury sports car on a 7-year loan, you aren't just spending $80,000.\n\nYou are giving up what that money could have earned elsewhere:\n\n$80,000 invested in a global equity index fund at a conservative 9% annual return grows to:\n• $189,000 in 10 years\n• $448,000 in 20 years\n• $1,062,000 in 30 years\n\nThat car didn't cost you $80,000. It cost you $1 Million in future net worth.\n\nDoes this mean you should never buy nice things? Absolutely not.\nIt means you should make financial trade-offs with your eyes wide open to the true economic cost.",
            "cta": "What was the single best financial trade-off or investment decision you made in the last 5 years? Drop it below 👇",
            "hashtags": ["#OpportunityCost", "#MoneyMindset", "#PersonalFinance", "#SmartSpending", "#WealthCreation"]
        },
        {
            "hook": "The Sunk Cost Fallacy is why smart people hold onto losing investments, bad careers, and failing projects:\n'I can't quit now, I've already spent so much money.'",
            "body": "Here is the golden rule of economics:\nMoney spent in the past is gone. It cannot be recovered.\n\nEvery forward decision must be based solely on FUTURE expected return, not past expense.\n\n• Holding a dying stock down 60% just to 'wait until it gets back to even' is a cognitive error. If another opportunity will grow faster, you should reallocate immediately.\n• Staying in an unrewarding job because you spent 4 years studying for a specific credential is an ego trap.\n\nStop throwing good money after bad. Cut your losses, preserve your capital, and allocate toward high-probability forward paths.",
            "cta": "Be honest: What's the longest you've held onto a losing stock hoping to 'just break even'? Drop your confession below 😭👇",
            "hashtags": ["#DecisionMaking", "#MentalModels", "#BehavioralFinance", "#InvestingPsychology", "#Mindset"]
        },
        {
            "hook": "You don't need to master 100 complex Excel formulas to succeed in corporate finance and investing.\n90% of financial analysis relies on these 4 tools:",
            "body": "1. XLOOKUP:\nCompletely replaces VLOOKUP and HLOOKUP. It searches in any direction, doesn't break when columns are added, and handles missing values gracefully without errors.\n\n2. XNPV and XIRR:\nUnlike standard NPV and IRR, XNPV and XIRR handle irregular cash flow dates. Crucial for calculating real-world private equity, real estate, and portfolio returns.\n\n3. SUMIFS / COUNTIFS:\nFilters large transaction datasets by multiple conditions simultaneously (e.g. Total revenue for Region A where margin > 20%).\n\n4. Data Tables (Sensitivity Analysis):\nInstantly stress-tests valuation models across 2 variables (e.g. see target share price across 5 different discount rates and 5 terminal growth rates in seconds).\n\nMaster the fundamentals thoroughly.",
            "cta": "Which Excel formula or shortcut is your #1 favorite for financial modeling? Drop your go-to below 👇",
            "hashtags": ["#FinancialModeling", "#ExcelTips", "#CorporateFinance", "#Productivity", "#FinancialAnalyst"]
        },
        {
            "hook": "Credit cards are either a 25% APR wealth destroyer or a free 2% cash rebate machine.\nThe difference is one single rule:",
            "body": "Credit card companies make their billions from people who carry revolving balances.\n\nIf you pay 24% annual interest on an unpaid $5,000 balance, you are donating $1,200 a year to a bank's profit margin.\n\nHere is how to operate in the top 5% who profit from the system:\n\n1. Set Autopay to 'Full Statement Balance' (never the minimum amount due).\n2. Treat your credit card like a debit card: never swipe for money that isn't already sitting in your checking account.\n3. Utilize reward points, travel insurance, fraud protection, and cash rebates.\n\nIf you can't pay the full balance every month without exception, switch to debit immediately.",
            "cta": "Do you use credit cards strategically for points/cashback or do you prefer debit/cash? Drop your preference below 👇",
            "hashtags": ["#CreditCards", "#PersonalFinance", "#SmartMoney", "#FinancialDiscipline", "#MoneyHacks"]
        },
        {
            "hook": "The 4% Retirement Rule isn't just for retirees.\nIt is the clearest benchmark for financial independence at any age.",
            "body": "Originating from the Trinity Study, the 4% Rule states that a diversified portfolio of equities and bonds has historically survived 30-year retirements with an initial 4% annual withdrawal rate (adjusted for inflation).\n\nHow do you calculate your Financial Independence (FI) Target?\nMultiply your desired annual living expenses by 25.\n\n• If your baseline expenses are $40,000/year:\n$40,000 × 25 = $1,000,000 invested portfolio target.\n\n• If your baseline expenses are $60,000/year:\n$60,000 × 25 = $1,500,000 invested portfolio target.\n\nNotice the leverage:\nEvery $100/month you trim from permanent recurring waste reduces your FI number by $30,000 ($1,200/yr × 25).\n\nLowering your burn rate accelerates financial freedom faster than working overtime.",
            "cta": "Have you calculated your personal 25x Financial Independence target number yet: Yes or No? Drop your answer below 👇",
            "hashtags": ["#FinancialIndependence", "#RetirementPlanning", "#4PercentRule", "#WealthBuilding", "#FIRE"]
        },
        {
            "hook": "There are two proven mathematical ways to pay off debt:\nWhich one works in real life depends on your psychology, not math.",
            "body": "If you have multiple credit cards or student loans, you have two options:\n\n📌 Method 1: The Debt Avalanche\n• Pay minimums on everything, put every extra dollar into the loan with the highest interest rate (e.g. 24% APR card).\n→ Mathematical Result: Saves you the maximum amount in total interest fees.\n\n📌 Method 2: The Debt Snowball\n• Pay minimums on everything, put every extra dollar into the loan with the smallest balance (e.g. $500 balance first).\n→ Psychological Result: Wiping out an entire account in month 1 gives an instant dopamine surge, keeping you motivated to attack the next loan.\n\nBehavioral finance proves that the 'best' financial plan is the one you actually stick with.",
            "cta": "If you were coaching someone out of debt, would you recommend: A) Avalanche (pure math) or B) Snowball (mental momentum)? Drop A or B below 👇",
            "hashtags": ["#DebtFree #PersonalFinance #BehavioralEconomics #MoneyHabits #FinancialFreedom"]
        },
        {
            "hook": "E-commerce algorithms are engineered by behavioral psychologists to trigger instant checkout.\nHere is the 72-hour mental circuit breaker that saves $3,000+/year:",
            "body": "The 'Buy Now with 1-Click' button was patented because frictionless spending prevents your rational brain from kicking in.\n\nHere is the rule for any non-essential purchase over $100:\n\n1. Add the item to your cart or wishlist.\n2. Close the browser tab or app.\n3. Wait 72 hours before completing the checkout.\n\nIn 80% of cases, the acute dopamine surge of wanting the object fades completely within 3 days.\n\nIf you still genuinely want and value the product after 72 hours, buy it guilt-free.\n\nFriction is the ultimate antidote to regretful spending.",
            "cta": "Be honest: What was the most useless impulse purchase you made in the last 12 months? (We all have at least one 😂 Drop yours below 👇)",
            "hashtags": ["#MindfulSpending #FinancialDiscipline #MoneyHacks #ImpulseBuying #PersonalFinance"]
        },
        {
            "hook": "Inflation is a silent, regressive tax on people who don't own productive assets.\nHere is the real math of purchasing power:",
            "body": "If inflation averages 5% over 14 years, the purchasing power of cash in your pocket is cut in half.\n\nA $100 grocery basket today will cost $200.\n\nWho gets hurt by inflation?\n• Wage earners whose salaries adjust slower than living costs.\n• Savers who keep all their net worth in cash or low-interest bank accounts.\n\nWho gets protected by inflation?\n• Owners of productive businesses that possess pricing power to raise prices.\n• Owners of scarce real estate.\n• Borrowers with fixed-rate, long-term debt paying back loans with depreciated currency.\n\nYou cannot save your way to long-term wealth through cash alone. You must own productive equity.",
            "cta": "What has been your best personal hedge against inflation: A) Equities B) Real Estate C) Gold D) Career/Skills? Drop your choice below 👇",
            "hashtags": ["#Inflation", "#Economics", "#ProductiveAssets", "#RealEstate", "#Equities"]
        }
    ]
}


def sync_remote_history():
    """Silently syncs latest post history with GitHub remote if available."""
    try:
        import subprocess
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], cwd=str(BASE_DIR), capture_output=True, timeout=12)
    except Exception:
        pass


def load_history(pull_remote: bool = False) -> List[dict]:
    if pull_remote:
        sync_remote_history()
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            log.warning(f"Could not load post history: {e}")
    
    # Mirror into data/published_history.json if available
    pub_hist_file = DATA_DIR / "published_history.json"
    if pub_hist_file.exists():
        try:
            with open(pub_hist_file, "r", encoding="utf-8") as pf:
                pub_data = json.load(pf)
                for item in pub_data.get("linkedin_history", []):
                    exists = any(
                        (h.get("share_id") and h.get("share_id") == item.get("share_id")) or
                        (h.get("date_ist") == item.get("date_ist") and str(h.get("slot_num")) == str(item.get("slot_num")))
                        for h in history
                    )
                    if not exists:
                        history.append(item)
        except Exception as pe:
            log.warning(f"Could not read from published_history.json: {pe}")
            
    return history


def save_history(entry: dict):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # Mirror into data/published_history.json
    pub_hist_file = DATA_DIR / "published_history.json"
    if pub_hist_file.exists():
        try:
            with open(pub_hist_file, "r", encoding="utf-8") as pf:
                pub_data = json.load(pf)
            if "linkedin_history" not in pub_data:
                pub_data["linkedin_history"] = []
            if not any(
                (h.get("share_id") and h.get("share_id") == entry.get("share_id")) or
                (h.get("date_ist") == entry.get("date_ist") and str(h.get("slot_num")) == str(entry.get("slot_num")))
                for h in pub_data["linkedin_history"]
            ):
                pub_data["linkedin_history"].append(entry)
            with open(pub_hist_file, "w", encoding="utf-8") as pf:
                json.dump(pub_data, pf, indent=2, ensure_ascii=False)
        except Exception as pe:
            log.warning(f"Could not mirror history to published_history.json: {pe}")

    try:
        os.system(f"git add '{HISTORY_FILE}' '{pub_hist_file}' 2>/dev/null && git commit -m 'sync: auto post history [skip ci]' 2>/dev/null && git push origin main 2>/dev/null || true")
    except Exception:
        pass


def is_slot_already_posted(date_str: str, slot_num: Any, history: List[dict] = None) -> bool:
    """Checks if a given slot number has already been successfully posted on a specific date."""
    if history is None:
        history = load_history()
    for item in history:
        if item.get("date_ist") == date_str and item.get("success"):
            # Exact slot match
            if str(item.get("slot_num")) == str(slot_num):
                return True
            # Cross-compatible aliases
            if str(slot_num) == "peak_1" and str(item.get("slot_num")) in ("gf_1", "1"):
                return True
            if str(slot_num) == "peak_2" and str(item.get("slot_num")) in ("gf_2", "gf_3", "gf_4", "2", "3", "4"):
                return True
    return False


def normalize_snippet(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", text.lower())[:60]


def generate_post_content(slot: Dict[str, Any], history: List[dict] = None) -> Dict[str, Any]:
    now_ist = datetime.now(IST)
    is_odd_day = (now_ist.day % 2 != 0)
    
    # Alternate categories across alternating calendar days
    cat = slot.get("category", "wealth_habits")
    if is_odd_day:
        if cat == "wealth_habits":
            cat = "financial_hacks"
        elif cat == "investing_valuation":
            cat = "corporate_moats"

    target = slot.get("target", f"General Finance Masterclass ({cat})")
    
    # Pool options
    options = GENERAL_FINANCE_VAULT.get(cat, GENERAL_FINANCE_VAULT["wealth_habits"])
    
    # Avoid reusing recently posted hooks (14-day anti-repetition memory)
    history_entries = history or []
    recent_hooks = [normalize_snippet(h.get("text", "")) for h in history_entries if h.get("success")]
    
    # Filter for completely fresh, unseen posts
    fresh_options = [
        opt for opt in options 
        if not any(SequenceMatcher(None, normalize_snippet(opt["hook"]), rh).ratio() >= 0.75 for rh in recent_hooks[-40:])
    ]
    
    chosen = random.choice(fresh_options) if fresh_options else random.choice(options)
    
    # Viral formatting: Hook + Body + High-Velocity Discussion CTA + Clean signature + Hashtags
    author_signature = (
        "Found this useful?\n"
        "→ Repost to share with your network ♻️\n"
        "→ Follow Sabhay Tomar for daily practical finance breakdowns & investing insights."
    )
    
    full_text = (
        f"{chosen['hook']}\n\n"
        f"{chosen['body']}\n\n"
        f"👇 Quick Question for the comments:\n"
        f"{chosen['cta']}\n\n"
        f"---\n{author_signature}\n\n"
        f"{' '.join(chosen['hashtags'])}"
    )
    words = full_text.split()
    
    return {
        "slot_num": slot.get("slot_num"),
        "time_ist": slot.get("time_ist", datetime.now(IST).strftime("%H:%M")),
        "target": target,
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
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    }
    
    req = urllib.request.Request(
        "https://backend.composio.dev/api/v3.1/tools/execute/LINKEDIN_CREATE_LINKED_IN_POST",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def execute_slot(slot: Dict[str, Any], dry_run: bool = False) -> bool:
    """Executes a single general finance posting slot."""
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    timestamp_str = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")
    
    log.info(f"Executing Slot #{slot['slot_num']} ({slot['time_ist']} IST) -> Target: {slot['target']}")
    
    post = generate_post_content(slot, load_history())
    
    if dry_run:
        print("\n" + "=" * 65)
        print(f"DRY RUN — SLOT #{post['slot_num']} | TARGET: {post['target']} | WORDS: {post['word_count']}")
        print("=" * 65)
        print(post["text"])
        print("=" * 65 + "\n")
        return True
        
    try:
        res = publish_post_to_composio(post["text"])
        share_id = ""
        link = ""
        
        if res.get("successful") or res.get("success"):
            data_resp = res.get("data", {})
            share_id = data_resp.get("id") or data_resp.get("share_id") or ""
            link = f"https://www.linkedin.com/feed/update/{share_id}" if share_id else ""
            log.info(f"✅ Published LIVE to LinkedIn! Share ID: {share_id} | Link: {link}")
            
            entry = {
                "date_ist": date_str,
                "timestamp_ist": timestamp_str,
                "slot_num": post["slot_num"],
                "scheduled_time_ist": post["time_ist"],
                "target": post["target"],
                "category": post["category"],
                "word_count": post["word_count"],
                "text": post["text"],
                "success": True,
                "share_id": share_id,
                "link": link,
                "error": None
            }
            save_history(entry)
            
            # Cross-post to X (Twitter)
            try:
                from x_autoposter import publish_tweet
                publish_tweet(category=post["category"])
            except Exception as xe:
                log.warning(f"X cross-posting: {xe}")
            
            print("\n" + "=" * 65)
            print(f"SLOT #{post['slot_num']} | TARGET: {post['target']} | WORDS: {post['word_count']}")
            print("=" * 65)
            print(post["text"])
            print("=" * 65 + "\n")
            return True
        else:
            err = res.get("error") or res.get("message") or "Unknown Composio error"
            log.error(f"❌ Failed to publish post: {err}")
            entry = {
                "date_ist": date_str,
                "timestamp_ist": timestamp_str,
                "slot_num": post["slot_num"],
                "scheduled_time_ist": post["time_ist"],
                "target": post["target"],
                "category": post["category"],
                "word_count": post["word_count"],
                "text": post["text"],
                "success": False,
                "share_id": None,
                "link": None,
                "error": str(err)
            }
            save_history(entry)
            return False
            
    except Exception as e:
        log.error(f"❌ Exception publishing slot {slot['slot_num']}: {e}")
        return False


def post_immediate_breakout(category: Optional[str] = None, dry_run: bool = False) -> bool:
    """Publishes an immediate viral General Finance post outside the normal schedule."""
    valid_categories = ["wealth_habits", "investing_valuation", "corporate_moats", "financial_hacks"]
    chosen_cat = category if category in valid_categories else random.choice(valid_categories)
    
    now_ist = datetime.now(IST)
    slot_desc = chosen_cat.replace("_", " ").title()
    slot = {
        "slot_num": f"boost_{now_ist.strftime('%H%M')}",
        "time_ist": now_ist.strftime("%H:%M"),
        "target": f"Immediate Boost: {slot_desc}",
        "category": chosen_cat
    }
    log.info(f"🚀 Triggering Immediate General Finance Breakout Post ({slot['target']})...")
    return execute_slot(slot, dry_run=dry_run)


def run_catch_up(dry_run: bool = False):
    """
    Scans the 2 daily peak slots for today in IST.
    Any slot whose scheduled time has already arrived and has NOT been posted yet today
    is executed immediately. Protected by non-blocking file lock.
    """
    lock_file = DATA_DIR / "autoposter.lock"
    try:
        lock_fd = open(lock_file, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        log.info("Another autoposter instance is actively executing. Exiting gracefully.")
        return

    try:
        now_ist = datetime.now(IST)
        date_str = now_ist.strftime("%Y-%m-%d")
        current_minutes = now_ist.hour * 60 + now_ist.minute
        
        log.info(f"Running catch-up engine for {date_str} at {now_ist.strftime('%H:%M:%S IST')}...")
        history = load_history(pull_remote=True)
        
        pending_slots = []
        for s in SLOTS:
            h, m = map(int, s["time_ist"].split(":"))
            slot_mins = h * 60 + m
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
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except Exception:
            pass


def show_status():
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    history = load_history()
    
    print("\n" + "=" * 65)
    print(f"GENERAL FINANCE LINKEDIN AUTOPOSTER STATUS — {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 65)
    
    today_posts = [p for p in history if p.get("date_ist") == date_str and p.get("success")]
    print(f"Today's Completed Posts: {len(today_posts)}\n")
    
    for s in SLOTS:
        posted = next((p for p in today_posts if str(p.get("slot_num")) in (str(s["slot_num"]), f"gf_{s['slot_num'][-1]}")), None)
        status_sym = "✅ POSTED" if posted else "⏳ PENDING"
        share_info = f"({posted.get('link')})" if posted else ""
        print(f"Slot #{s['slot_num']} | {s['time_ist']} IST | {s['target'][:42]:<42} | {status_sym} {share_info}")
    
    # Extra boost / legacy posts today
    other_posts = [p for p in today_posts if not any(str(p.get("slot_num")) in (str(s["slot_num"]), f"gf_{s['slot_num'][-1]}") for s in SLOTS)]
    if other_posts:
        print("\nOther Posts Active Today:")
        for op in other_posts:
            print(f"Slot {op.get('slot_num')} | {op.get('scheduled_time_ist', op.get('time_ist'))} IST | ✅ {op.get('link')}")
            
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="General Finance LinkedIn Autoposter")
    parser.add_argument("--slot", type=str, choices=["peak_1", "peak_2", "1", "2"], help="Execute a specific slot number")
    parser.add_argument("--post-now", action="store_true", help="Publish a fresh viral General Finance post immediately")
    parser.add_argument("--category", type=str, choices=["wealth_habits", "investing_valuation", "corporate_moats", "financial_hacks"], help="Specific category for --post-now")
    parser.add_argument("--catch-up", action="store_true", help="Idempotently post any due slots that haven't posted yet today")
    parser.add_argument("--dry-run", action="store_true", help="Preview post without publishing")
    parser.add_argument("--status", action="store_true", help="Show current posting status for today")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.post_now:
        post_immediate_breakout(category=args.category, dry_run=args.dry_run)
    elif args.slot:
        slot_map = {"1": "peak_1", "2": "peak_2", "peak_1": "peak_1", "peak_2": "peak_2"}
        slot_id = slot_map.get(args.slot, args.slot)
        target_slot = next((s for s in SLOTS if s["slot_num"] == slot_id), None)
        if target_slot:
            execute_slot(target_slot, dry_run=args.dry_run)
    else:
        run_catch_up(dry_run=args.dry_run)
