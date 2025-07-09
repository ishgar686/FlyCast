from fastapi import FastAPI, Query
from pydantic import BaseModel
import random

app = FastAPI()

# Input model for flight prediction
class FlightRequest(BaseModel):
    airline: str
    flight_number: str
    date: str  # format: YYYY-MM-DD

# Dummy user data (can later be connected to a real DB)
UCSD_USERS = {
    "UA123": ["alice@ucsd.edu", "bob@ucsd.edu"],
    "DL456": ["carol@ucsd.edu"]
}

@app.get("/")
def index():
    return {"message": "Welcome to FlyCast!"}

@app.post("/predict")
def predict_delay(req: FlightRequest):
    delay_minutes = random.choice([0, 5, 15, 30, 60])
    return {
        "airline": req.airline,
        "flight_number": req.flight_number,
        "date": req.date,
        "predicted_delay_minutes": delay_minutes
    }

@app.get("/shared-travelers/")
def get_shared_travelers(flight_number: str = Query(...)):
    return {
        "flight_number": flight_number,
        "ucsd_users": UCSD_USERS.get(flight_number.upper(), [])
    }
