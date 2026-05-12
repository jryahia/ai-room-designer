import json
import re
from openai import AsyncOpenAI
from config import settings, THEMES, ROOM_TYPES

SYSTEM_PROMPT = """You are an expert interior designer with 20 years of experience in Italian and European design.
You generate photorealistic, detailed, and commercially viable interior design proposals.
Always respond in valid JSON only — no markdown, no extra text.
All design names, rationale, furniture lists, and labels must be provided in BOTH Italian and English."""

DESIGN_PROMPT_TEMPLATE = """Design 5 distinct interior design proposals for this room.

ROOM DETAILS:
- Type: {room_type_en} ({room_type_it})
- Dimensions: {width}m wide × {length}m long × {height}m high ({area:.1f} m²)
- Requested theme: {theme_en} ({theme_it})
- Room photo analysis: {photo_description}

CURRENT DESIGN TRENDS (use these to inform proposals):
{trends}

USER HISTORY INSIGHTS (what worked well for similar rooms):
{history}

Generate exactly 5 DIFFERENT design proposals. Each must be unique in color palette, furniture style, and mood.
Proposals should range from: faithful to theme, creative interpretation, budget-friendly, luxury, and mixed/eclectic.

Return a JSON object with this exact structure:
{{
  "designs": [
    {{
      "index": 0,
      "name_it": "Nome del Design",
      "name_en": "Design Name",
      "tagline_it": "Frase breve evocativa",
      "tagline_en": "Short evocative phrase",
      "dalle_prompt": "Photorealistic interior render of [detailed description for DALL-E 3: specific furniture, exact colors, lighting, materials, style, room angle — 150-200 words], professional architectural photography, 8K, beautiful natural lighting",
      "style_tags": ["tag1", "tag2", "tag3", "tag4"],
      "color_palette": [
        {{"hex": "#XXXXXX", "label_it": "Nome Colore", "label_en": "Color Name", "role": "primary/secondary/accent/neutral/surface"}},
        {{"hex": "#XXXXXX", "label_it": "Nome Colore", "label_en": "Color Name", "role": "primary/secondary/accent/neutral/surface"}},
        {{"hex": "#XXXXXX", "label_it": "Nome Colore", "label_en": "Color Name", "role": "primary/secondary/accent/neutral/surface"}},
        {{"hex": "#XXXXXX", "label_it": "Nome Colore", "label_en": "Color Name", "role": "primary/secondary/accent/neutral/surface"}},
        {{"hex": "#XXXXXX", "label_it": "Nome Colore", "label_en": "Color Name", "role": "primary/secondary/accent/neutral/surface"}}
      ],
      "furniture": [
        {{
          "name_it": "Nome Mobile",
          "name_en": "Furniture Name",
          "category": "sofa/bed/table/chair/storage/lighting/rug/decor",
          "estimated_cost_eur": 450,
          "brand_suggestion": "IKEA / H&M Home / Zara Home / Maisons du Monde / etc",
          "ikea_link_hint": "IKEA product line name if applicable"
        }}
      ],
      "decor": [
        {{
          "name_it": "Nome Decor",
          "name_en": "Decor Name",
          "estimated_cost_eur": 45
        }}
      ],
      "total_cost": {{
        "min_eur": 1200,
        "max_eur": 2800,
        "budget_tier": "budget/mid-range/premium/luxury"
      }},
      "rationale_it": "Paragrafo 1 che spiega la visione del design...\\n\\nParagrafo 2 che descrive i materiali e colori scelti...\\n\\nParagrafo 3 con consigli pratici di implementazione...",
      "rationale_en": "Paragraph 1 explaining the design vision...\\n\\nParagraph 2 describing chosen materials and colors...\\n\\nParagraph 3 with practical implementation tips..."
    }}
  ]
}}

IMPORTANT:
- Include 6-10 furniture items and 3-5 decor items per design
- Total costs should be realistic for Italian market
- DALL-E prompts must be extremely detailed and photorealistic
- Make each of the 5 designs visually and stylistically distinct
- All 5 designs should suit the exact room dimensions"""


class DesignGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.openai_model

    async def _analyze_photo(self, room_photo_b64: str) -> str:
        if not room_photo_b64:
            return "Empty room with standard walls, floor, and ceiling. Natural light from windows."

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe this room briefly for an interior designer: "
                                    "floor type, wall color, windows, existing features, light conditions. "
                                    "Max 100 words, focus on structural elements."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{room_photo_b64}"},
                            },
                        ],
                    }
                ],
            )
            return resp.choices[0].message.content or "Standard empty room."
        except Exception:
            return "Empty room with standard walls, floor, and ceiling."

    async def generate_designs(
        self,
        room_photo_b64: str,
        room_type: str,
        dimensions: dict,
        theme: str,
        trends: list[str],
        user_history: list[dict],
    ) -> list[dict]:
        photo_desc = await self._analyze_photo(room_photo_b64)

        room_info = ROOM_TYPES.get(room_type, {"label": room_type, "it": room_type})
        theme_info = THEMES.get(theme, {"en": theme, "it": theme})

        trend_text = "\n".join(f"• {t}" for t in trends) if trends else "No specific trends data available."

        history_text = "No previous design history for this room type."
        if user_history:
            history_text = f"Top themes chosen: {', '.join(user_history.get('top_themes', []))}\n"
            if user_history.get("popular_colors"):
                history_text += f"Popular colors: {', '.join(user_history['popular_colors'])}"

        area = dimensions["width"] * dimensions["length"]

        prompt = DESIGN_PROMPT_TEMPLATE.format(
            room_type_en=room_info["label"],
            room_type_it=room_info["it"],
            width=dimensions["width"],
            length=dimensions["length"],
            height=dimensions["height"],
            area=area,
            theme_en=theme_info["en"],
            theme_it=theme_info["it"],
            photo_description=photo_desc,
            trends=trend_text,
            history=history_text,
        )

        resp = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=6000,
            temperature=0.85,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw = resp.choices[0].message.content or "{}"
        return self.parse_designs(raw)

    def parse_designs(self, llm_response: str) -> list[dict]:
        try:
            data = json.loads(llm_response)
            designs = data.get("designs", [])
            validated = []
            for i, d in enumerate(designs[:5]):
                validated.append({
                    "index": d.get("index", i),
                    "name_it": d.get("name_it", f"Design {i+1}"),
                    "name_en": d.get("name_en", f"Design {i+1}"),
                    "tagline_it": d.get("tagline_it", ""),
                    "tagline_en": d.get("tagline_en", ""),
                    "dalle_prompt": d.get("dalle_prompt", ""),
                    "style_tags": d.get("style_tags", []),
                    "color_palette": d.get("color_palette", []),
                    "furniture": d.get("furniture", []),
                    "decor": d.get("decor", []),
                    "total_cost": d.get("total_cost", {"min_eur": 0, "max_eur": 0, "budget_tier": "mid-range"}),
                    "rationale_it": d.get("rationale_it", ""),
                    "rationale_en": d.get("rationale_en", ""),
                    "render_url": None,
                })
            return validated
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
