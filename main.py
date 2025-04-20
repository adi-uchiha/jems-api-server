import sys
import os
from pathlib import Path

# Get the directory where this main.py file resides
# In Vercel, this will be something like /var/task/backend
script_dir = Path(__file__).resolve().parent

# Add this directory to the *start* of the Python search path
# This ensures Python looks here first for the 'app' directory
sys.path.insert(0, str(script_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import encode
from app.core.config import settings
from app.db.connection import init_connection_pool, close_all_db_connections



@asynccontextmanager
async def lifespan(app: FastAPI):
		# Startup
		init_connection_pool()
		yield
		# Shutdown
		close_all_db_connections()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS Configuration
app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
)

# # Include routers
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(encode.router, prefix="/api", tags=["Encoding"])

if __name__ == "__main__":
		print("🟢️ 🟢️ 🟢️ --- Starting JEMS api-server --- 🟢️ 🟢️ 🟢️")
		import uvicorn
		uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
