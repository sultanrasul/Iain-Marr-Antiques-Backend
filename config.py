import json
import os
from pydantic_settings import BaseSettings

CONFIG_FILE = "settings.json"

class Settings(BaseSettings):
    # --- Static / secret settings from env ---
    GOOGLE_SERVICE_ACCOUNT_JSON: dict
    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    TURSO_DATABASE_URL: str
    TURSO_AUTH_TOKEN: str

    # --- Editable settings persisted to JSON ---
    api_v1_prefix: str = "/api/v1"
    GOOGLE_SHEETS_ID: str
    DATABASE_PATH: str
    ENV: str = "testing"
    

    class Config:
        env_file = ".env"

    # --- Minimal JSON logic ---
    def load_dynamic(self):
        default_dynamic = {
            "api_v1_prefix": self.api_v1_prefix,
            "GOOGLE_SHEETS_ID": self.GOOGLE_SHEETS_ID,
            "DATABASE_PATH": self.DATABASE_PATH
        }

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                for key in default_dynamic:
                    setattr(self, key, data.get(key, default_dynamic[key]))
        else:
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_dynamic, f, indent=4)

    def save_dynamic(self):
        dynamic_keys = ["api_v1_prefix", "GOOGLE_SHEETS_ID", "DATABASE_PATH",]
        data = {key: getattr(self, key) for key in dynamic_keys}
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

# --- Load settings ---
settings = Settings()
settings.load_dynamic()

# --- Example runtime update ---
def update_sheets_id(new_id: str):
    settings.GOOGLE_SHEETS_ID = new_id
    settings.save_dynamic()