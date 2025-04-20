import sys
import os
from pathlib import Path

# Get the directory where this main.py file resides
# In Vercel, this will be something like /var/task/backend
script_dir = Path(__file__).resolve().parent

# Add this directory to the *start* of the Python search path
# This ensures Python looks here first for the 'app' directory
sys.path.insert(0, str(script_dir))

# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api import auth, game, users, dashboard, profile
# from app.core.config import settings
# from app.db.connection import init_connection_pool, close_all_connections



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     init_connection_pool()
#     yield
#     # Shutdown
#     close_all_connections()

# app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# # CORS Configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(game.router, prefix="/api/game", tags=["Game"])
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
# app.include_router(profile.router, prefix="/api/profile", tags=["profile"])

if __name__ == "__main__":
		print("Starting JEMS api-server")
		enqueue_task()
    # import uvicorn
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
