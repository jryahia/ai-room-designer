import json
from pathlib import Path
from datetime import datetime
from collections import Counter

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from config import settings
from models import Base, UserDesignPick, TrendReport

Path("data").mkdir(exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_pick(
    db: Session,
    room_type: str,
    theme: str,
    width_m: float,
    length_m: float,
    height_m: float,
    selected_design_index: int,
    design_summary: dict,
) -> UserDesignPick:
    pick = UserDesignPick(
        room_type=room_type,
        theme=theme,
        width_m=width_m,
        length_m=length_m,
        height_m=height_m,
        selected_design_index=selected_design_index,
        design_summary=json.dumps(design_summary),
    )
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick


def get_picks_by_room_type(db: Session, room_type: str) -> list[dict]:
    picks = db.query(UserDesignPick).filter(UserDesignPick.room_type == room_type).all()
    result = []
    for p in picks:
        result.append({
            "id": p.id,
            "theme": p.theme,
            "width_m": p.width_m,
            "length_m": p.length_m,
            "height_m": p.height_m,
            "selected_design_index": p.selected_design_index,
            "design_summary": json.loads(p.design_summary) if p.design_summary else {},
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


def get_all_picks(db: Session) -> list[dict]:
    picks = db.query(UserDesignPick).order_by(UserDesignPick.created_at.desc()).all()
    result = []
    for p in picks:
        result.append({
            "id": p.id,
            "room_type": p.room_type,
            "theme": p.theme,
            "width_m": p.width_m,
            "length_m": p.length_m,
            "height_m": p.height_m,
            "selected_design_index": p.selected_design_index,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


def get_pick_count(db: Session) -> int:
    return db.query(func.count(UserDesignPick.id)).scalar() or 0


def get_pick_count_by_room(db: Session, room_type: str) -> int:
    return (
        db.query(func.count(UserDesignPick.id))
        .filter(UserDesignPick.room_type == room_type)
        .scalar()
        or 0
    )


def get_winning_patterns(db: Session, room_type: str) -> dict:
    picks = get_picks_by_room_type(db, room_type)
    if not picks:
        return {}

    themes = Counter(p["theme"] for p in picks)
    avg_width = sum(p["width_m"] for p in picks) / len(picks)
    avg_length = sum(p["length_m"] for p in picks) / len(picks)

    colors = []
    for p in picks:
        summary = p.get("design_summary", {})
        palette = summary.get("color_palette", [])
        for c in palette:
            if isinstance(c, dict) and "hex" in c:
                colors.append(c["hex"])

    top_colors = [c for c, _ in Counter(colors).most_common(5)]

    return {
        "top_themes": [t for t, _ in themes.most_common(3)],
        "avg_dimensions": {"width": round(avg_width, 1), "length": round(avg_length, 1)},
        "popular_colors": top_colors,
        "total_picks": len(picks),
    }


def save_report(db: Session, room_type: str, report_data: dict, pick_count: int) -> TrendReport:
    report = TrendReport(
        room_type=room_type,
        report_data=json.dumps(report_data),
        pick_count=pick_count,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_latest_report(db: Session, room_type: str) -> dict | None:
    report = (
        db.query(TrendReport)
        .filter(TrendReport.room_type == room_type)
        .order_by(TrendReport.generated_at.desc())
        .first()
    )
    if report:
        return {
            "room_type": report.room_type,
            "report_data": json.loads(report.report_data) if report.report_data else {},
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "pick_count": report.pick_count,
        }
    return None


def get_aggregate_stats(db: Session) -> dict:
    total = get_pick_count(db)
    by_room = {}
    by_theme = {}

    picks = db.query(UserDesignPick).all()
    for p in picks:
        by_room[p.room_type] = by_room.get(p.room_type, 0) + 1
        by_theme[p.theme] = by_theme.get(p.theme, 0) + 1

    return {
        "total_picks": total,
        "by_room_type": by_room,
        "by_theme": by_theme,
        "top_room": max(by_room, key=by_room.get) if by_room else None,
        "top_theme": max(by_theme, key=by_theme.get) if by_theme else None,
    }
