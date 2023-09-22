from pydantic import BaseModel
from typing import List

class Settings(BaseModel):
    NightVisionEnabled: bool = False
    FacialRecognitionEnabled: bool = False
    NotificationCooldown: int = 300

class CameraPreview(BaseModel):
    cameraId: int
    frame: str  # I assume this is a typo and should be 'frame' instead of 'fames'
    isMonitoring: bool

class Previews(BaseModel):
    cameraPreviews: List[CameraPreview]
    
class Recording(BaseModel):
    datetime: str
    filename: str