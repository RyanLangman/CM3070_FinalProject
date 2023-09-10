import json
import os
from models.models import Settings

def load_settings_from_file(file_path='settings.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return Settings(**data)
    else:
        default_settings = Settings(NightVisionEnabled=True, FacialRecognitionEnabled=True, NotificationCooldown=10, TelegramAPI="api_key_here")
        save_settings_to_file(default_settings, file_path)
        return default_settings

def save_settings_to_file(settings, file_path='settings.json'):
    with open(file_path, 'w') as f:
        json.dump(settings.dict(), f)  # Assuming Settings is a Pydantic model