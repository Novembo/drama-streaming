from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, or_, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, selectinload

from app.core.cache import get_json, invalidate, set_json
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.entities import (
    Drama,
    Episode,
    Favorite,
    Subscription,
    User,
    UserHistory,
)
from app.schemas.contracts import (
    DramaCreate,
    DramaOut,
    EpisodeCreate,
    EpisodeOut,
    ProgressInput,
)

router = APIRouter(tags=["catalog"])


def episode_out(ep: Episode):
    qualities = [
        q
        for q, v in [
            ("360p", ep.video_360p),
            ("480p", ep.video_480p),
            ("720p", ep.video_720p),
            ("1080p", ep.video_1080p),
        ]
        if v
    ]
    return EpisodeOut(
        id=ep.id,
        episode_number=ep.episode_number,
        title=ep.title,
        duration_seconds=ep.duration_seconds,
        thumbnail_url=ep.thumbnail_url,
        qualities=qualities[:4],
        subtitles=ep.subtitles,
        audio_tracks=ep.audio_tracks,
    )


def _has_category(db: Session, category: str):
    """Category membership. JSON has no containment operator on PostgreSQL (this filter used to return
    HTTP 500 there) and the generic `.contains()` degrades to LIKE, so pick the right operator per dialect."""
    if db.get_bind().dialect.name == "postgresql":
        return cast(Drama.categories, JSONB).contains([category])  # `@>`, served by the GIN index
    return text("EXISTS (SELECT 1 FROM json_each(dramas.categories) WHERE json_each.value = :cat)").bindparams(
        cat=category
    )


@router.get("/dramas", response_model=list[DramaOut])
def list_dramas(
    category: str | None = None,
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    cache_key = f"dramas:v1:{category or ''}:{q or ''}:{limit}:{offset}"
    cached = get_json(cache_key)
    if cached is not None:
        return cached
    stmt = (
        select(Drama).where(Drama.is_published.is_(True)).order_by(Drama.created_at.desc()).limit(limit).offset(offset)
    )
    if category:
        stmt = stmt.where(_has_category(db, category))
    if q:
        pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"  # escape LIKE wildcards
        stmt = stmt.where(
            or_(
                Drama.title.ilike(pattern, escape="\\"),
                Drama.synopsis.ilike(pattern, escape="\\"),
            )
        )
    result = [DramaOut.model_validate(x).model_dump(mode="json") for x in db.scalars(stmt).all()]
    set_json(cache_key, result, ttl=60)
    return result


@router.get("/dramas/{drama_id}")
def drama_detail(drama_id: int, db: Session = Depends(get_db)):
    drama = db.scalar(
        select(Drama).options(selectinload(Drama.episodes)).where(Drama.id == drama_id, Drama.is_published.is_(True))
    )
    if not drama:
        raise HTTPException(404, "Drama introuvable")
    return {
        "id": drama.id,
        "title": drama.title,
        "original_title": drama.original_title,
        "synopsis": drama.synopsis,
        "poster_url": drama.poster_url,
        "banner_url": drama.banner_url,
        "release_year": drama.release_year,
        "country": drama.country,
        "categories": drama.categories,
        "rating": float(drama.rating) if drama.rating else None,
        "episodes": [episode_out(e).model_dump() for e in drama.episodes if e.is_published],
    }


@router.get("/episodes/{episode_id}")
def episode_stream(
    episode_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ep = db.scalar(
        select(Episode)
        .join(Drama)
        .where(
            Episode.id == episode_id,
            Episode.is_published.is_(True),
            Drama.is_published.is_(True),
        )
    )
    if not ep:
        raise HTTPException(404, "Épisode introuvable")
    # Only playback URLs are returned to authenticated users. Signed CDN URLs should be generated here in production.
    now = datetime.now(UTC)
    vip = (
        db.scalar(
            select(Subscription.id)
            .where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                Subscription.ends_at > now,
            )
            .limit(1)
        )
        is not None
    )
    available = (
        [("360p", ep.video_360p)]
        if not vip
        else [
            ("360p", ep.video_360p),
            ("480p", ep.video_480p),
            ("720p", ep.video_720p),
            ("1080p", ep.video_1080p),
        ]
    )
    qualities = [{"resolution": r, "url": u} for r, u in available if u]
    return {
        "id": ep.id,
        "episode_number": ep.episode_number,
        "title": ep.title,
        "duration_seconds": ep.duration_seconds,
        "qualities": qualities[:4],
        "subtitles": ep.subtitles,
        "audio_tracks": ep.audio_tracks,
        "vip_required_for_hd": not vip,
    }


@router.get("/me/favorites")
def favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Favorite)
        .options(selectinload(Favorite.drama))
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return [DramaOut.model_validate(x.drama) for x in rows]


@router.post("/me/favorites/{drama_id}", status_code=204)
def add_favorite(drama_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.scalar(select(Drama.id).where(Drama.id == drama_id, Drama.is_published.is_(True))):
        raise HTTPException(404, "Drama introuvable")
    if not db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.drama_id == drama_id)):
        db.add(Favorite(user_id=user.id, drama_id=drama_id))
        db.commit()


@router.delete("/me/favorites/{drama_id}", status_code=204)
def remove_favorite(drama_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.drama_id == drama_id).delete()
    db.commit()


@router.put("/me/progress")
def save_progress(
    payload: ProgressInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ep = db.get(Episode, payload.episode_id)
    if not ep or not ep.is_published:
        raise HTTPException(404, "Épisode introuvable")
    progress = min(payload.progress_seconds, ep.duration_seconds or payload.progress_seconds)
    row = db.scalar(select(UserHistory).where(UserHistory.user_id == user.id, UserHistory.episode_id == ep.id))
    if row is None:
        row = UserHistory(user_id=user.id, episode_id=ep.id)
        db.add(row)
    row.progress_seconds = progress
    row.completed = payload.completed or (ep.duration_seconds > 0 and progress >= ep.duration_seconds * 0.95)
    db.commit()
    return {"saved": True, "progress_seconds": progress, "completed": row.completed}


@router.get("/me/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(UserHistory)
        .options(selectinload(UserHistory.episode).selectinload(Episode.drama))
        .where(UserHistory.user_id == user.id)
        .order_by(UserHistory.updated_at.desc())
        .limit(50)
    ).all()
    return [
        {
            "episode_id": r.episode_id,
            "episode_number": r.episode.episode_number,
            "drama_id": r.episode.drama_id,
            "drama_title": r.episode.drama.title,
            "poster_url": r.episode.drama.poster_url,
            "progress_seconds": r.progress_seconds,
            "completed": r.completed,
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/admin/dramas", status_code=201)
def create_drama(
    payload: DramaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    drama = Drama(**payload.model_dump())
    db.add(drama)
    db.commit()
    db.refresh(drama)
    invalidate("dramas:v1:")
    return {"id": drama.id}


@router.post("/admin/dramas/{drama_id}/episodes", status_code=201)
def create_episode(
    drama_id: int,
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not db.get(Drama, drama_id):
        raise HTTPException(404, "Drama introuvable")
    ep = Episode(drama_id=drama_id, **payload.model_dump())
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return {"id": ep.id}


@router.post("/admin/dramas/{drama_id}/publish")
def publish_drama(drama_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    drama = db.get(Drama, drama_id)
    if not drama:
        raise HTTPException(404, "Drama introuvable")
    count = db.scalar(select(Episode.id).where(Episode.drama_id == drama_id, Episode.is_published.is_(True)).limit(1))
    if not count:
        raise HTTPException(
            409,
            "Publiez au moins un épisode avec un flux 360p avant de publier le drama",
        )
    drama.is_published = True
    db.commit()
    invalidate("dramas:v1:")
    return {"id": drama.id, "is_published": True}
