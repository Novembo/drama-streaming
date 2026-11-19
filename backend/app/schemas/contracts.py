from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=128)


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=20, max_length=4096)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class DramaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    synopsis: str
    poster_url: str
    banner_url: str
    release_year: int | None
    country: str
    categories: list[str]
    rating: float | None


class EpisodeOut(BaseModel):
    id: int
    episode_number: int
    title: str
    duration_seconds: int
    thumbnail_url: str
    qualities: list[str]
    subtitles: list[str]
    audio_tracks: list[str]


class ProgressInput(BaseModel):
    episode_id: int
    progress_seconds: int = Field(ge=0)
    completed: bool = False


class PlanOut(BaseModel):
    id: str
    name: str
    duration_days: int
    price_xof: int
    currency: str = "XOF"
    features: list[str]


class CheckoutInput(BaseModel):
    plan_id: str
    provider: str = Field(pattern="^(fedapay|cinetpay)$")
    phone_number: str | None = Field(default=None, max_length=24)


class CheckoutOut(BaseModel):
    payment_id: int
    reference: str
    status: str
    amount_xof: int
    checkout_url: str
    message: str


class DramaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=255)
    synopsis: str = Field(default="", max_length=12000)
    poster_url: str = Field(default="", max_length=512)
    banner_url: str = Field(default="", max_length=512)
    release_year: int | None = Field(default=None, ge=1900, le=2100)
    country: str = Field(default="Corée du Sud", max_length=80)
    categories: list[str] = Field(default_factory=list, max_length=12)
    tmdb_id: int | None = None
    original_title: str | None = Field(default=None, max_length=255)
    rating: float | None = Field(default=None, ge=0, le=10)


class EpisodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    episode_number: int = Field(ge=1)
    title: str = Field(default="", max_length=255)
    duration_seconds: int = Field(default=0, ge=0)
    video_360p: str = Field(min_length=8)
    video_480p: str | None = None
    video_720p: str | None = None
    video_1080p: str | None = None
    thumbnail_url: str = Field(default="", max_length=512)
    subtitles: list[str] = Field(default_factory=lambda: ["FR"], max_length=2)
    audio_tracks: list[str] = Field(default_factory=lambda: ["FR"], max_length=2)
    is_published: bool = False
