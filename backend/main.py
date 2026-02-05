from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "AI Travel Planner API Running"}

@app.get("/plan")
def create_plan(place: str, days: int, interest: str):

    # -------------------------------
    # Get coordinates from OSM
    # -------------------------------
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "ai-travel-planner"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if not data:
        return {"error": "Place not found"}

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    # -------------------------------
    # Simple AI Itinerary Generator
    # -------------------------------
    itinerary = []

    for i in range(1, days + 1):

        itinerary.append({
            "day": i,
            "activity": f"Explore {interest} places in {place}"
        })

    # -------------------------------
    # Return Response
    # -------------------------------
    return {
        "place": place,
        "lat": lat,
        "lon": lon,
        "itinerary": itinerary
    }
