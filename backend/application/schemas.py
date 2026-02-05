from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Message(BaseModel):
    type: str
    user_id: str | None = None
    username: str | None = None
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))