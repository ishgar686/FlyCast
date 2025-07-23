import requests
import json
import os
import random
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class FlightDataFetcher:
    def __init__(self, mock_mode=False, mock_dir=None):
        self.mock_mode = mock_mode
        self.mock_dir = mock_dir or os.path.join(os.path.dirname(__file__), "..", "mock_flights")
        self.mock_dir = os.path.abspath(self.mock_dir)
        self.api_key = os.getenv("AVIATIONSTACK_API_KEY")

    def get_flight_info(self, flight_number: str) -> Optional[Dict[str, Any]]:
        if self.mock_mode:
            target_file = os.path.join(self.mock_dir, f"{flight_number}.json")
            if os.path.exists(target_file):
                with open(target_file) as f:
                    return json.load(f)

            airline_prefix = ''.join(filter(str.isalpha, flight_number)).upper()
            all_files = [f for f in os.listdir(self.mock_dir) if f.endswith(".json")]
            matching_files = [f for f in all_files if f.startswith(airline_prefix)]

            if matching_files:
                chosen_file = random.choice(matching_files)
            elif all_files:
                chosen_file = random.choice(all_files)
            else:
                return None

            with open(os.path.join(self.mock_dir, chosen_file)) as f:
                return json.load(f)
        else:
            return self._fetch_live_data(flight_number)

    def _fetch_live_data(self, flight_number: str) -> Optional[Dict[str, Any]]:
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': self.api_key,
            'flight_iata': flight_number
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._extract_flight_data(data)
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def _extract_flight_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not data.get('data') or len(data['data']) == 0:
                return None

            flight = data['data'][0]
            return {
                'flight_number': flight.get('flight', {}).get('iata', 'Unknown'),
                'origin': flight.get('departure', {}).get('iata', 'Unknown'),
                'destination': flight.get('arrival', {}).get('iata', 'Unknown'),
                'scheduled_departure': flight.get('departure', {}).get('scheduled', 'Unknown'),
                'actual_departure': flight.get('departure', {}).get('actual', 'Unknown'),
                'status': flight.get('flight_status', 'Unknown')
            }

        except (KeyError, IndexError):
            return None