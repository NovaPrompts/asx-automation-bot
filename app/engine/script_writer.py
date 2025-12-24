import json
import logging
from typing import List, Literal
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.core.config import settings
from app.models.base import NewsItem, ScriptSegment, SegmentType

logger = logging.getLogger(__name__)

class ScriptOutput(BaseModel):
    segments: List[ScriptSegment]

class ScriptWriter:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_script(
        self,
        news_items: List[NewsItem],
        mode: Literal["morning", "afternoon"] = "morning"
    ) -> List[ScriptSegment]:
        """
        Generates a podcast script based on the provided news items and mode.
        """
        if not news_items:
            logger.warning("No news items provided to ScriptWriter.")
            return []

        # 1. Prepare Context
        context_str = "\n\n".join(
            [f"ID: {i+1}\nSource: {item.source_id}\nTitle: {item.title}\nSummary: {item.content_summary}" 
             for i, item in enumerate(news_items)]
        )

        # 2. Define Mode-Specific Instructions
        if mode == "morning":
            focus_instruction = (
                "Focus on Global/US market closes (S&P500, NASDAQ) from overnight "
                "and their specific implication for the ASX opening. Mention key commodities."
            )
        else:
            focus_instruction = (
                "Focus on ASX market close, top winners/losers of the day, "
                "and local earnings results."
            )

        # 3. Construct System Prompt
        system_prompt = f"""
You are a Senior Australian Financial Analyst. Your task is to write a podcast script based on the provided news context.

**Persona:**
- Tone: Professional, terse, high signal-to-noise ratio.
- Style: No fluff (e.g., avoid "Welcome back", "Let's dive in"). Get straight to the numbers.
- Language: Australian English spelling (e.g., 'labour', 'centralised', 'program').
- TTS Optimization: Write ticker symbols phonetically if ambiguous, or spaced out for clarity (e.g., "B-H-P" instead of "BHP", "C-S-L" instead of "CSL").

**Structure Instructions:**
- **{mode.upper()} EDITION**: {focus_instruction}
- segment_type "intro": Brief high-level summary of the mood.
- segment_type "market_wrap": Quantitative data, indices, currency.
- segment_type "stock_deepdive": Specific analysis of the most important stories provided.
- segment_type "outro": Very short sign-off.

**Input Context:**
{context_str}

**Output Format:**
Return a valid JSON object strictly matching this structure:
{{
  "segments": [
    {{
      "segment_type": "enum(intro, market_wrap, stock_deepdive, outro)",
      "text": "The script content for this segment..."
    }}
  ]
}}
"""

        # 4. Call LLM
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the script based on the news provided."}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            # 5. Parse and Validate
            content = response.choices[0].message.content
            parsed_json = json.loads(content)
            
            # Pydantic validation
            script_output = ScriptOutput(**parsed_json)
            return script_output.segments

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            raise e
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise e
