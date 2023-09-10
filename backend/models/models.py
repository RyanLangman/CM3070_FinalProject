from pydantic import BaseModel
from typing import Dict, List

class Settings(BaseModel):
    NightVisionEnabled: bool = False
    FacialRecognitionEnabled: bool = False
    NotificationCooldown: int = 300
    TelegramAPI: str = ""
    RecordingInSeconds: int = 5

class VideoPreviews(BaseModel):
    frames: Dict[int, str]  # Dictionary of webcam IDs to base64 encoded frame strings

class Recordings(BaseModel):
    files: List[str]  # List of file paths or names