import logging
from datetime import datetime, timezone
from typing import Optional
import google.generativeai as genai
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini once at module load
genai.configure(api_key=settings.GEMINI_API_KEY)

# checking which are models available to use in v1beta
# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)
model = genai.GenerativeModel(model_name="gemini-2.5-flash",)


# ---------- Prompt builder ----------

def build_prompt(sector: str, market_data: Optional[str]) -> str:
    """
    Build the full prompt we send to Gemini.
    If market_data is available, it's injected as context.
    If not, Gemini falls back to its own training knowledge.
    """
    today = datetime.now(timezone.utc).strftime("%d %B %Y")

    context_block = ""
    if market_data:
        context_block = f"""
## LIVE MARKET RESEARCH DATA (use this as primary source)

{market_data}

---
"""

    prompt = f"""You are a senior financial analyst specializing in Indian equity markets.
Today's date is {today}.

{context_block}

## YOUR TASK

Analyze the **{sector.upper()} sector in India** and generate a comprehensive trade opportunities report.

Use the market research data above as your primary source. Supplement with your own knowledge where needed.

## REPORT FORMAT

Return the report strictly in the following markdown format:

---

# {sector.title()} Sector — Trade Opportunities Report
**Date:** {today}
**Market:** India (BSE/NSE)

## 1. Sector Overview
Brief description of the sector, its size, and role in the Indian economy.

## 2. Current Market Sentiment
- Overall sentiment: Bullish / Bearish / Neutral
- Key drivers of current sentiment
- Recent developments impacting the sector

## 3. Top Trade Opportunities
List 3-5 specific opportunities with reasoning:
- Opportunity name
- Why it's an opportunity right now
- Risk level: Low / Medium / High

## 4. Key Stocks to Watch
List 4-6 stocks (BSE/NSE listed) with:
- Stock name & ticker
- Why it's worth watching
- Short-term outlook

## 5. Risk Factors
List major risks that could impact this sector negatively.

## 6. Analyst Recommendation
A short paragraph with an overall recommendation for traders/investors looking at this sector right now.

---

Be specific, data-driven, and concise. Avoid generic filler content.
"""
    return prompt


# ---------- Core analysis function ----------

def analyze_sector(sector: str, market_data: Optional[str]) -> str:
    """
    Sends sector + collected market data to Gemini.
    Returns the markdown report as a string.
    Raises exception on API failure.
    """
    prompt = build_prompt(sector, market_data)

    logger.info(f"Sending prompt to Gemini for sector: {sector}")

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.4,       # lower = more factual, less creative
                max_output_tokens=2048,
            ),
        )

        report = response.text
        logger.info(f"Gemini response received for sector: {sector} ({len(report)} chars)")
        return report

    except Exception as e:
        logger.error(f"Gemini API error for sector '{sector}': {str(e)}")
        raise RuntimeError(f"AI analysis failed: {str(e)}")