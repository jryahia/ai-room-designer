import json
import logging
from datetime import datetime

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

from config import settings

REPORT_SYSTEM_PROMPT = """You are a market research analyst specializing in interior design trends.
Analyze user design selection data and produce a comprehensive, sellable trend report.
Respond in valid JSON only."""

REPORT_PROMPT_TEMPLATE = """Analyze the following interior design user selections for {room_type_label} rooms
and generate a comprehensive trend report.

SELECTION DATA:
- Total selections analyzed: {total_picks}
- Top chosen themes: {top_themes}
- Average room dimensions: {avg_dimensions}
- Most popular colors chosen: {popular_colors}
- Date range of data: {date_range}

Individual design summaries (sample of {sample_size}):
{design_samples}

Generate a professional trend report as JSON:
{{
  "report_title_it": "Titolo del Report",
  "report_title_en": "Report Title",
  "executive_summary_it": "Sommario esecutivo...",
  "executive_summary_en": "Executive summary...",
  "top_themes": [
    {{"theme": "theme_name", "percentage": 45, "growth_trend": "rising/stable/declining", "notes_it": "...", "notes_en": "..."}}
  ],
  "color_analysis": {{
    "dominant_colors": [{{"hex": "#XXXXXX", "label": "Color Name", "frequency": "high/medium/low"}}],
    "emerging_colors": [{{"hex": "#XXXXXX", "label": "Color Name"}}],
    "declining_colors": [{{"hex": "#XXXXXX", "label": "Color Name"}}],
    "commentary_it": "...",
    "commentary_en": "..."
  }},
  "dimension_insights": {{
    "most_common_size": "description",
    "avg_area_sqm": 0.0,
    "notes_it": "...",
    "notes_en": "..."
  }},
  "avg_budget": {{
    "by_tier": {{"budget": 0, "mid_range": 0, "premium": 0, "luxury": 0}},
    "overall_avg_eur": 0
  }},
  "consumer_insights_it": ["insight 1", "insight 2", "insight 3"],
  "consumer_insights_en": ["insight 1", "insight 2", "insight 3"],
  "recommendations_for_retailers_it": ["raccomandazione 1", "raccomandazione 2"],
  "recommendations_for_retailers_en": ["recommendation 1", "recommendation 2"],
  "forecast_next_6_months_it": "...",
  "forecast_next_6_months_en": "...",
  "methodology_note_it": "...",
  "methodology_note_en": "..."
}}"""


class TrendReportGenerator:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = settings.openai_model

    def should_generate_report(self, total_picks: int) -> bool:
        return total_picks > 0 and total_picks % settings.trend_report_interval == 0

    async def generate_report(self, room_type: str, picks: list[dict]) -> dict:
        if not picks:
            return {}

        from collections import Counter
        themes = Counter(p.get("theme", "unknown") for p in picks)
        top_themes = [t for t, _ in themes.most_common(5)]

        widths = [p.get("width_m", 0) for p in picks if p.get("width_m")]
        lengths = [p.get("length_m", 0) for p in picks if p.get("length_m")]
        avg_w = round(sum(widths) / len(widths), 1) if widths else 0
        avg_l = round(sum(lengths) / len(lengths), 1) if lengths else 0

        colors = []
        for p in picks:
            ds = p.get("design_summary", {})
            for c in ds.get("color_palette", []):
                if isinstance(c, dict) and "hex" in c:
                    colors.append(c["hex"])
        popular_colors = [c for c, _ in Counter(colors).most_common(5)]

        sample = picks[:20]
        design_samples = json.dumps(
            [{"theme": p.get("theme"), "design": p.get("design_summary", {}).get("name_en", "")} for p in sample],
            ensure_ascii=False,
        )

        prompt = REPORT_PROMPT_TEMPLATE.format(
            room_type_label=room_type.replace("_", " ").title(),
            total_picks=len(picks),
            top_themes=", ".join(top_themes),
            avg_dimensions=f"{avg_w}m × {avg_l}m",
            popular_colors=", ".join(popular_colors) if popular_colors else "varied",
            date_range=f"Up to {datetime.now().strftime('%B %Y')}",
            sample_size=len(sample),
            design_samples=design_samples,
        )

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = resp.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as e:
            logger.exception("Report generation error")
            return {}

    def format_for_business(self, report: dict) -> str:
        if not report:
            return "<p>No report data available.</p>"

        sections = []
        sections.append(f"<h1>{report.get('report_title_en', 'Design Trend Report')}</h1>")
        sections.append(f"<p><em>{report.get('report_title_it', '')}</em></p>")

        if es := report.get("executive_summary_en"):
            sections.append(f"<h2>Executive Summary</h2><p>{es}</p>")

        if themes := report.get("top_themes"):
            sections.append("<h2>Top Design Themes</h2><ul>")
            for t in themes:
                sections.append(
                    f"<li><strong>{t['theme'].title()}</strong> — {t['percentage']}% ({t['growth_trend']}): {t.get('notes_en', '')}</li>"
                )
            sections.append("</ul>")

        if ca := report.get("color_analysis"):
            sections.append("<h2>Color Analysis</h2>")
            if dominant := ca.get("dominant_colors"):
                sections.append("<p><strong>Dominant colors:</strong> " + ", ".join(
                    f'<span style="background:{c["hex"]};padding:2px 8px;border-radius:3px;">{c["label"]}</span>'
                    for c in dominant
                ) + "</p>")
            sections.append(f"<p>{ca.get('commentary_en', '')}</p>")

        if insights := report.get("consumer_insights_en"):
            sections.append("<h2>Consumer Insights</h2><ul>")
            for i in insights:
                sections.append(f"<li>{i}</li>")
            sections.append("</ul>")

        if recs := report.get("recommendations_for_retailers_en"):
            sections.append("<h2>Recommendations for Retailers</h2><ul>")
            for r in recs:
                sections.append(f"<li>{r}</li>")
            sections.append("</ul>")

        if forecast := report.get("forecast_next_6_months_en"):
            sections.append(f"<h2>6-Month Forecast</h2><p>{forecast}</p>")

        return "\n".join(sections)
