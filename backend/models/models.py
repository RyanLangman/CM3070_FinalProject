from pydantic import BaseModel
from typing import Dict, List

class Settings(BaseModel):
    NightVisionEnabled: bool
    FacialRecognitionEnabled: bool
    NotificationCooldown: int
    TelegramAPI: str
    RecordingInMinutes: int

class VideoPreviews(BaseModel):
    frames: Dict[int, str]  # Dictionary of webcam IDs to base64 encoded frame strings

class Recordings(BaseModel):
    files: List[str]  # List of file paths or names