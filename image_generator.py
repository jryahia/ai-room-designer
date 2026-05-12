import asyncio
import base64
import httpx
from openai import AsyncOpenAI

from config import settings

DALLE_SYSTEM_PREFIX = (
    "Photorealistic interior design render, professional architectural photography, "
    "high-end magazine quality, beautiful natural and artificial lighting, "
    "sharp details, 8K resolution, no people, no text, no watermarks. "
)


class ImageGenerator:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.enabled = bool(api_key or settings.openai_api_key)

    async def generate_render(self, design_prompt: str, design_name: str = "") -> str | None:
        if not self.enabled or not design_prompt:
            return None

        full_prompt = DALLE_SYSTEM_PREFIX + design_prompt

        try:
            resp = await self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt[:4000],
                n=1,
                size="1792x1024",
                quality="hd",
                style="vivid",
            )
            return resp.data[0].url
        except Exception as e:
            print(f"DALL-E error for '{design_name}': {e}")
            return None

    async def generate_all_renders(self, designs: list[dict]) -> list[dict]:
        tasks = [
            self.generate_render(d.get("dalle_prompt", ""), d.get("name_en", ""))
            for d in designs
        ]
        # Run all 5 in parallel (DALL-E rate limit: 5 img/min on tier 1)
        urls = await asyncio.gather(*tasks, return_exceptions=True)

        for design, url in zip(designs, urls):
            if isinstance(url, str):
                design["render_url"] = url
            else:
                design["render_url"] = None

        return designs

    async def fetch_image_as_b64(self, url: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return base64.b64encode(resp.content).decode("utf-8")
        except Exception:
            pass
        return None
