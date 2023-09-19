from helpers.cameras import get_available_cameras

class Config:
    available_cameras = None

    @classmethod
    def initialize(cls):
        cls.available_cameras = get_available_cameras(1)