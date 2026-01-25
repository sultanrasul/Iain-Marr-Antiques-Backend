from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import system, stock, sales
from config import settings
from utils.exceptions import http_exception_handler
import uvicorn

app = FastAPI(title="Iain Marr Antiques - Point of Sale Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system.router, prefix="/api/v1")
app.include_router(stock.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "healthy"}