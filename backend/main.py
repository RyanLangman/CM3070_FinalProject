from fastapi import FastAPI
from fastapi.routing import APIRouter
from routes.routes import routes as api_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the API routes
app.include_router(
    APIRouter(prefix="/api"),
    prefix="/api/v1",  # Versioning
    tags=["API"],
)

# Test endpoint
@app.get("/")
def read_root():
    return {"message": "Home Surveillance API is up and running!"}

# Include the routes from routes.py
app.include_router(api_routes, prefix="/api/v1", tags=["API Endpoints"])