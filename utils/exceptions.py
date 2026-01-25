from fastapi import HTTPException

class NotFoundError(Exception): pass
class PrinterNotConnected(Exception): pass

def http_exception_handler(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail="No Stock data found")
    if isinstance(exc, PrinterNotConnected):
        return HTTPException(status_code=400, detail="Printer not connected")

    return HTTPException(status_code=500, detail="Internal server error")
