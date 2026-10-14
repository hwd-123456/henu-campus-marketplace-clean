from pydantic import BaseModel, Field
from typing import Optional


class ErrandCreate(BaseModel):
    """Payload for POST /api/v1/errands (delivery package 03 field contract)."""

    campus: str = Field(..., min_length=1, examples=["金明校区"])
    title: str = Field(..., min_length=1, examples=["代取快递"])
    origin: str = Field(..., min_length=1, examples=["金明校区北门"])
    destination: str = Field(..., min_length=1, examples=["生活服务中心"])
    reward: float = Field(..., ge=0, examples=[3])


class ErrandAction(BaseModel):
    """Optional note for claim/complete actions."""

    note: Optional[str] = None
