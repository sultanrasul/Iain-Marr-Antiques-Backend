import subprocess

class SystemService:
    @staticmethod
    def restart_system():
        try:
            # Schedule a restart after 1 second
            subprocess.Popen(["sudo", "shutdown", "-r", "now"])
            return {"success": True, "message": "Raspberry Pi is restarting..."}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
        
    @staticmethod
    def shutdown_system():
        try:
            # Schedule a shutdown after 1 second
            subprocess.Popen(["sudo", "shutdown", "now"])
            return {"success": True, "message": "Raspberry Pi is shutting down..."}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500