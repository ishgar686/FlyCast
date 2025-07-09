import requests
import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FlightDataFetcher:
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.api_key = os.getenv('AVIATIONSTACK_API_KEY')
        self.mock_file = 'mock_response.json'
        
        if not mock_mode and not self.api_key:
            raise ValueError("AVIATIONSTACK_API_KEY not found in environment variables")
    
    def get_flight_info(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """Get flight information from AviationStack API or mock data."""
        if self.mock_mode:
            return self._load_mock_data(flight_number)
        else:
            return self._fetch_live_data(flight_number)
    
    def _fetch_live_data(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """Fetch live data from AviationStack API."""
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': self.api_key,
            'flight_iata': flight_number
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Save response for mock mode
            self._save_mock_data(flight_number, data)
            
            return self._extract_flight_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse API response: {e}")
            return None
    
    def _load_mock_data(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """Load mock data from saved JSON file."""
        try:
            if os.path.exists(self.mock_file):
                with open(self.mock_file, 'r') as f:
                    data = json.load(f)
                return self._extract_flight_data(data)
            else:
                print(f"Mock file {self.mock_file} not found. Run in live mode first to generate mock data.")
                return None
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Failed to load mock data: {e}")
            return None
    
    def _save_mock_data(self, flight_number: str, data: Dict[str, Any]) -> None:
        """Save API response to mock file."""
        try:
            with open(self.mock_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Mock data saved to {self.mock_file}")
        except Exception as e:
            print(f"Failed to save mock data: {e}")
    
    def _extract_flight_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract relevant flight information from API response."""
        try:
            if not data.get('data') or len(data['data']) == 0:
                print("No flight data found in API response")
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
            
        except (KeyError, IndexError) as e:
            print(f"Failed to extract flight data: {e}")
            return None

def scrape_flight_info(flight_number: str, mock_mode: bool = False) -> Optional[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    fetcher = FlightDataFetcher(mock_mode=mock_mode)
    return fetcher.get_flight_info(flight_number)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch flight information from AviationStack')
    parser.add_argument('flight_number', help='Flight number (e.g., WN673)')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API')
    
    args = parser.parse_args()
    
    try:
        fetcher = FlightDataFetcher(mock_mode=args.mock)
        result = fetcher.get_flight_info(args.flight_number)
        
        if result:
            print("Flight Information:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("Failed to fetch flight information")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
