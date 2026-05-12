import httpx
from datetime import datetime

from config import settings

CURRENT_YEAR = datetime.now().year

FALLBACK_TRENDS: dict[str, list[str]] = {
    "kitchen": [
        f"Open shelving with integrated LED lighting — top kitchen trend {CURRENT_YEAR}",
        "Two-tone cabinet colors: navy lower cabinets + natural wood upper",
        "Waterfall quartz countertops replacing granite in modern kitchens",
        "Integrated smart appliances with hidden handles (handleless design)",
        "Large-format porcelain slabs as backsplash tiles",
        "Warm terracotta and earthy tones replacing cold grays",
        "Butler's pantry and scullery making a comeback in larger kitchens",
    ],
    "bedroom": [
        f"Boucle fabric headboards and upholstered bed frames trending {CURRENT_YEAR}",
        "Earthy neutrals: warm beige, terracotta, and soft sage dominate palettes",
        "Integrated bedside niches replacing traditional nightstands",
        "Curved furniture — round mirrors, arched headboards, organic shapes",
        "Japandi style (Japanese + Scandinavian hybrid) continues to grow",
        "Smart lighting with circadian rhythm automation",
        "Platform beds with hidden storage gaining popularity on Pinterest",
    ],
    "living_room": [
        f"Curved sofas and rounded corners are the biggest living room trend {CURRENT_YEAR}",
        "Biophilic design: indoor plants as structural elements, not accessories",
        "Layered rugs over hardwood floors for texture and warmth",
        "Fluted wood panels as accent walls replacing plain wallpaper",
        "Warm ambient lighting with floor lamps replacing overhead fixtures",
        "Modular sectional sofas for flexible layouts",
        "Vintage and antique pieces mixed with contemporary furniture",
    ],
    "bathroom": [
        f"Wet room bathrooms (no shower enclosure) trending {CURRENT_YEAR}",
        "Terrazzo tiles making strong comeback in bath floors and walls",
        "Freestanding bathtubs as sculptural centerpieces",
        "Matte black fixtures replacing chrome in modern bathrooms",
        "Spa-inspired steam showers with LED chromotherapy",
        "Floating vanities with indirect LED underlighting",
        "Natural stone: travertine and limestone replacing ceramic tiles",
    ],
    "office": [
        f"Biophilic home office design with living plant walls {CURRENT_YEAR}",
        "Acoustic panels doubling as decorative wall art",
        "Sit-stand desks becoming standard in home office setups",
        "Japandi and minimalist aesthetics dominate productive spaces",
        "Warm wood tones replacing cold white desks",
        "Integrated cable management systems for clean aesthetics",
        "Dual-monitor setups with monitor arms for flexible ergonomics",
    ],
}

THEME_TRENDS: dict[str, list[str]] = {
    "modern": [
        "Clean lines, neutral palettes with warm accents",
        "Integrated smart home technology seamlessly hidden",
        "Open plan spaces with zoning through lighting and rugs",
    ],
    "rustic": [
        "Reclaimed wood beams and distressed finishes",
        "Stone accent walls and fireplace surrounds",
        "Wrought iron fixtures and hardware",
    ],
    "industrial": [
        "Exposed brick, concrete, and structural steel",
        "Edison bulb pendant lighting in black metal frames",
        "Polished concrete floors with area rugs",
    ],
    "japanese": [
        "Wabi-sabi imperfection philosophy in materials choice",
        "Shoji screens as room dividers",
        "Low furniture, floor cushions, and tatami-inspired areas",
    ],
    "scandinavian": [
        "Hygge concept: cozy textiles, candles, warm neutrals",
        "Functional minimalism with hidden storage",
        "Natural materials: oak, wool, linen, and ceramic",
    ],
    "mediterranean": [
        "Terracotta tiles, arched doorways, whitewashed walls",
        "Blue and white color combinations with pops of yellow",
        "Handmade ceramic accessories and decorative tiles",
    ],
    "boho": [
        "Macrame wall hangings and rattan furniture",
        "Rich jewel tones: terracotta, mustard, deep teal",
        "Layered textiles and global-inspired patterns",
    ],
    "minimalist": [
        "Hidden storage to eliminate visual clutter",
        "Monochromatic palettes with texture as interest",
        "Quality over quantity — fewer but better pieces",
    ],
    "classic": [
        "Crown molding, wainscoting, and architectural details",
        "Rich fabrics: velvet, silk, and damask patterns",
        "Symmetrical arrangements and formal layouts",
    ],
    "vintage": [
        "Mid-century modern revival with teak and walnut",
        "Retro color palettes: avocado, mustard, burnt orange",
        "Statement vintage furniture paired with modern basics",
    ],
    "eclectic": [
        "Curated mix of periods, styles, and cultures",
        "Gallery walls with diverse art collections",
        "Bold pattern mixing with cohesive color thread",
    ],
}


class TrendSearcher:
    def __init__(self):
        self.api_key = settings.search_api_key
        self.engine_id = settings.search_engine_id

    async def search_trends(self, room_type: str, theme: str | None = None) -> list[str]:
        if self.api_key and self.engine_id:
            try:
                return await self._google_search(room_type, theme)
            except Exception:
                pass
        return self.get_fallback_trends(room_type, theme)

    async def _google_search(self, room_type: str, theme: str | None) -> list[str]:
        queries = [
            f"top {room_type.replace('_', ' ')} interior design styles {CURRENT_YEAR}",
            f"trending {room_type.replace('_', ' ')} colors Italy {CURRENT_YEAR}",
            f"IKEA {CURRENT_YEAR} new products {room_type.replace('_', ' ')}",
            f"Pinterest most saved {room_type.replace('_', ' ')} layouts {CURRENT_YEAR}",
        ]
        if theme:
            queries.append(f"{theme} {room_type.replace('_', ' ')} design trends {CURRENT_YEAR}")

        snippets: list[str] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for query in queries[:3]:
                try:
                    resp = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params={
                            "key": self.api_key,
                            "cx": self.engine_id,
                            "q": query,
                            "num": 3,
                        },
                    )
                    data = resp.json()
                    for item in data.get("items", []):
                        snippet = item.get("snippet", "").strip()
                        if snippet:
                            snippets.append(snippet)
                except Exception:
                    continue

        return snippets[:10] if snippets else self.get_fallback_trends(room_type, theme)

    def get_fallback_trends(self, room_type: str, theme: str | None = None) -> list[str]:
        trends = list(FALLBACK_TRENDS.get(room_type, []))
        if theme and theme in THEME_TRENDS:
            trends.extend(THEME_TRENDS[theme])
        return trends[:10]
