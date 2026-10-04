import base64
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import ROOM_TYPES, THEMES, settings
from database import (
    get_db,
    get_aggregate_stats,
    get_latest_report,
    get_pick_count,
    get_pick_count_by_room,
    get_picks_by_room_type,
    get_winning_patterns,
    save_pick,
    save_report,
)
from design_generator import DesignGenerator
from image_generator import ImageGenerator
from trend_report import TrendReportGenerator
from trend_searcher import TrendSearcher

router = APIRouter()
templates = Jinja2Templates(directory="templates")

trend_searcher = TrendSearcher()
design_gen = DesignGenerator()
image_gen = ImageGenerator()
report_gen = TrendReportGenerator()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "themes": THEMES,
            "room_types": ROOM_TYPES,
            "current_year": datetime.now().year,
        },
    )


@router.post("/design", response_class=HTMLResponse)
async def create_design(
    request: Request,
    room_type: str = Form(...),
    theme: str = Form(...),
    custom_theme: str = Form(""),
    width_m: float = Form(...),
    length_m: float = Form(...),
    height_m: float = Form(...),
    room_photo: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Read and encode photo
    photo_b64 = ""
    if room_photo and room_photo.filename:
        content = await room_photo.read()
        photo_b64 = base64.b64encode(content).decode("utf-8")

    effective_theme = custom_theme.strip() if theme == "custom" and custom_theme.strip() else theme

    dimensions = {"width": width_m, "length": length_m, "height": height_m}

    # Fetch trends and user history
    trends = await trend_searcher.search_trends(room_type, effective_theme)
    history = get_winning_patterns(db, room_type)

    # Generate designs
    designs = await design_gen.generate_designs(
        room_photo_b64=photo_b64,
        room_type=room_type,
        dimensions=dimensions,
        theme=effective_theme,
        trends=trends,
        user_history=history,
    )

    # Generate renders in parallel
    if designs:
        designs = await image_gen.generate_all_renders(designs)

    room_info = ROOM_TYPES.get(room_type, {"label": room_type, "it": room_type, "emoji": "🏠"})
    theme_info = THEMES.get(effective_theme, {"en": effective_theme, "it": effective_theme, "emoji": "✨"})

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "request": request,
            "designs": designs,
            "room_type": room_type,
            "room_info": room_info,
            "theme": effective_theme,
            "theme_info": theme_info,
            "dimensions": dimensions,
            "area": round(width_m * length_m, 1),
            "themes": THEMES,
            "room_types": ROOM_TYPES,
            "current_year": datetime.now().year,
        },
    )


@router.post("/api/pick")
async def record_pick(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await request.json()
    room_type = body.get("room_type", "")
    theme = body.get("theme", "")
    width_m = float(body.get("width_m", 0))
    length_m = float(body.get("length_m", 0))
    height_m = float(body.get("height_m", 0))
    selected_index = int(body.get("selected_design_index", 0))
    design_summary = body.get("design_summary", {})

    pick = save_pick(db, room_type, theme, width_m, length_m, height_m, selected_index, design_summary)

    total_picks = get_pick_count(db)
    if report_gen.should_generate_report(total_picks):
        picks = get_picks_by_room_type(db, room_type)
        report_data = await report_gen.generate_report(room_type, picks)
        if report_data:
            save_report(db, room_type, report_data, total_picks)

    return JSONResponse({"success": True, "pick_id": pick.id, "total_picks": total_picks})


@router.get("/api/history")
async def get_history(db: Session = Depends(get_db)):
    picks = db.execute(
        __import__("sqlalchemy").text(
            "SELECT room_type, theme, COUNT(*) as cnt FROM user_design_picks GROUP BY room_type, theme ORDER BY cnt DESC LIMIT 50"
        )
    ).fetchall()
    return JSONResponse([{"room_type": r[0], "theme": r[1], "count": r[2]} for r in picks])


@router.get("/api/trends/{room_type}")
async def get_trends(room_type: str, db: Session = Depends(get_db)):
    report = get_latest_report(db, room_type)
    if not report:
        return JSONResponse({"message": "No trend report available yet", "room_type": room_type})
    return JSONResponse(report)


@router.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    stats = get_aggregate_stats(db)
    return JSONResponse(stats)


@router.get("/api/report/{room_type}/html")
async def get_report_html(room_type: str, db: Session = Depends(get_db)):
    report = get_latest_report(db, room_type)
    if not report:
        return HTMLResponse("<p>No report available yet. Data is collected as users make design selections.</p>")
    html = report_gen.format_for_business(report.get("report_data", {}))
    return HTMLResponse(f"""
    <!DOCTYPE html><html><head>
    <meta charset="utf-8">
    <title>Trend Report — {room_type.replace('_', ' ').title()}</title>
    <style>
      body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto; padding: 20px; color: #333; }}
      h1 {{ color: #1a1a2e; }} h2 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 8px; }}
      li {{ margin: 6px 0; }} p {{ line-height: 1.7; }}
    </style>
    </head><body>{html}</body></html>
    """)
