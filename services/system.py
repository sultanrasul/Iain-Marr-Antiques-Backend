import os
import shutil
import subprocess
from fastapi.responses import FileResponse
import json

from services.integrations.integrations import get_sheets_service, get_database_service, get_printer_service, reset_integration

from config import settings



class SystemService:
    @staticmethod
    def restart_system():
        try:
            subprocess.Popen(["sudo", "shutdown", "-r", "now"])
            return {"success": True, "message": "Raspberry Pi is restarting..."}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

    @staticmethod
    def shutdown_system():
        try:
            subprocess.Popen(["sudo", "shutdown", "now"])
            return {"success": True, "message": "Raspberry Pi is shutting down..."}, 200
        except Exception as e:
            
            return {"success": False, "error": str(e)}, 500

    @staticmethod
    def sync_database():
        databaseService = get_database_service()
        sheetsService = get_sheets_service()
        # Import products
        products = sheetsService.get_stock()
        product_errors = databaseService.import_products_to_db(products=products)

        # Import sold items
        sold_products = sheetsService.get_sold_items()
        sold_product_errors = databaseService.import_sold_products_to_db(sold_products=sold_products)
        
        return [product_errors, sold_product_errors]

    @staticmethod
    def update_google_sheets_id(new_id: str):
        """Update Google Sheets ID and persist it."""
        settings.GOOGLE_SHEETS_ID = new_id
        settings.save_dynamic()
        reset_integration("sheets")
        return {"success": True, "GOOGLE_SHEETS_ID": new_id}, 200

    @staticmethod
    def upload_database_file(file_bytes: bytes, new_db_name: str):
        """
        Replace the current database with a new one.
        """
        try:
            # Determine folder to save the DB
            db_dir = os.path.dirname(settings.DATABASE_PATH)
            if not db_dir:
                db_dir = os.getcwd()  # default to current folder
            os.makedirs(db_dir, exist_ok=True)

            new_db_path = os.path.join(db_dir, new_db_name)

            # Write file bytes
            with open(new_db_path, "wb") as f:
                f.write(file_bytes)

            # Update settings
            settings.DATABASE_PATH = new_db_path
            settings.save_dynamic()
            reset_integration("database")

            return {"success": True, "DATABASE_PATH": new_db_path}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

    @staticmethod
    def get_current_database():
        """
        Allow frontend to download the current database file.
        Returns a FileResponse for FastAPI.
        """
        if not os.path.exists(settings.DATABASE_PATH):
            return {"success": False, "error": "Database file not found"}, 404
        return FileResponse(path=settings.DATABASE_PATH, filename=os.path.basename(settings.DATABASE_PATH))
    
    @staticmethod
    def get_settings(settings_path: str = "settings.json"):
        """
        Reads the settings.json file and returns its contents as a dictionary.
        """
        try:
            with open(settings_path, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            return {"success": False, "error": f"{settings_path} not found"}, 404
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {str(e)}"}, 400
        except Exception as e:
            return {"success": False, "error": str(e)}, 500