"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import check_db_connection
from app.routes import tests, plans, ai, upload, export

# Create FastAPI app
app = FastAPI(
    title="Capgemini Mi-Vie Validator API",
    description="Automotive validation plan generator for Mid-Life vehicle modifications",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
def read_root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "Capgemini Mi-Vie Validator API",
        "version": "1.0.0",
        "database": "connected" if check_db_connection() else "disconnected"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    db_status = check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "api_key_configured": bool(settings.CAPGEMINI_API_KEY),
        "debug_mode": settings.DEBUG_MODE
    }


# Include routers
app.include_router(tests.router, prefix="/api/tests", tags=["Tests"])
app.include_router(plans.router, prefix="/api/plans", tags=["Validation Plans"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Recommendations"])
app.include_router(upload.router, prefix="/api/upload", tags=["Data Upload"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("\n" + "="*60)
    print("🚀 Capgemini Mi-Vie Validator API Starting...")
    print("="*60)
    
    if check_db_connection():
        print("✅ Database connection established")
    else:
        print("❌ WARNING: Database connection failed!")
    
    print(f"📡 API running on http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"📚 Docs available at http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/docs")
    print("="*60 + "\n")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\n👋 Shutting down Capgemini Mi-Vie Validator API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG_MODE
    )
