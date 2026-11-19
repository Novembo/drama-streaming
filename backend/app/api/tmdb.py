import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_admin
from app.models.entities import Drama, User

router = APIRouter(prefix="/admin/tmdb", tags=["admin · TMDB"])
BASE = "https://api.themoviedb.org/3"


def request_tmdb(path: str, params: dict):
    if not settings.tmdb_api_key:
        raise HTTPException(503, "TMDB_API_KEY non configurée")
    try:
        response = httpx.get(
            f"{BASE}{path}",
            params={**params, "api_key": settings.tmdb_api_key, "language": "fr-FR"},
            timeout=8.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        raise HTTPException(502, "Le service TMDB est temporairement indisponible") from None


@router.get("/search")
def search_tmdb(q: str = Query(min_length=2, max_length=80), _: User = Depends(require_admin)):
    data = request_tmdb("/search/tv", {"query": q, "include_adult": "false"})
    return [
        {
            "tmdb_id": x["id"],
            "title": x.get("name"),
            "original_title": x.get("original_name"),
            "synopsis": x.get("overview"),
            "release_year": (x.get("first_air_date") or "")[:4] or None,
            "poster_url": f"https://image.tmdb.org/t/p/w500{x['poster_path']}" if x.get("poster_path") else "",
            "banner_url": f"https://image.tmdb.org/t/p/w1280{x['backdrop_path']}" if x.get("backdrop_path") else "",
            "rating": x.get("vote_average"),
        }
        for x in data.get("results", [])[:20]
    ]


@router.post("/import/{tmdb_id}", status_code=201)
def import_tmdb(tmdb_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    existing = db.query(Drama).filter(Drama.tmdb_id == tmdb_id).first()
    if existing:
        raise HTTPException(409, "Ce drama est déjà importé")
    data = request_tmdb(f"/tv/{tmdb_id}", {})
    genres = [x["name"] for x in data.get("genres", []) if x.get("name")]
    poster = f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else ""
    banner = f"https://image.tmdb.org/t/p/w1280{data['backdrop_path']}" if data.get("backdrop_path") else ""
    item = Drama(
        tmdb_id=tmdb_id,
        title=data.get("name") or "Sans titre",
        original_title=data.get("original_name"),
        synopsis=data.get("overview") or "",
        poster_url=poster,
        banner_url=banner,
        release_year=int(data["first_air_date"][:4]) if data.get("first_air_date", "")[:4].isdigit() else None,
        country=(data.get("origin_country") or [""])[0],
        categories=genres,
        rating=data.get("vote_average"),
        is_published=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "tmdb_id": tmdb_id,
        "published": False,
        "message": "Métadonnées importées. Ajoutez les épisodes et des flux vidéo autorisés avant publication.",
    }
