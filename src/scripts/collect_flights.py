import requests
import pandas as pd
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

class FlightDataCollector:
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.api_key = os.getenv('AVIATIONSTACK_API_KEY')
        self.mock_dir = 'mock_responses'
        
        if not mock_mode and not self.api_key:
            raise ValueError("AVIATIONSTACK_API_KEY not found in environment variables")
        
        # Create mock directory if it doesn't exist
        if mock_mode and not os.path.exists(self.mock_dir):
            os.makedirs(self.mock_dir)
    
    def get_flights_for_date(self, date: str, airline: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get flights for a specific date from AviationStack API."""
        if self.mock_mode:
            return self._load_mock_flights(date, airline)
        else:
            return self._fetch_live_flights(date, airline)
    
    def _fetch_live_flights(self, date: str, airline: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch live flight data from AviationStack API."""
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': self.api_key,
            'date': date
        }
        
        if airline:
            params['airline_iata'] = airline
        
        try:
            print(f"Fetching flights for {date} (airline: {airline or 'all'})...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Save response for mock mode
            self._save_mock_response(date, airline, data)
            
            return self._extract_flight_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {date}: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse API response for {date}: {e}")
            return []
    
    def _load_mock_flights(self, date: str, airline: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load mock flight data from saved JSON file."""
        filename = self._get_mock_filename(date, airline)
        
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                return self._extract_flight_data(data)
            else:
                print(f"Mock file {filename} not found. Run in live mode first to generate mock data.")
                return []
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Failed to load mock data for {date}: {e}")
            return []
    
    def _save_mock_response(self, date: str, airline: Optional[str], data: Dict[str, Any]) -> None:
        """Save API response to mock file."""
        filename = self._get_mock_filename(date, airline)
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Mock data saved to {filename}")
        except Exception as e:
            print(f"Failed to save mock data: {e}")
    
    def _get_mock_filename(self, date: str, airline: Optional[str]) -> str:
        """Generate mock filename based on date and airline."""
        airline_suffix = f"_{airline}" if airline else "_all"
        return os.path.join(self.mock_dir, f"flights_{date}{airline_suffix}.json")
    
    def _extract_flight_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relevant flight information from API response."""
        flights = []
        
        try:
            if not data.get('data') or len(data['data']) == 0:
                print("No flight data found in API response")
                return flights
            
            for flight in data['data']:
                # Extract basic flight info
                airline = flight.get('airline', {}).get('iata', 'Unknown')
                origin = flight.get('departure', {}).get('iata', 'Unknown')
                destination = flight.get('arrival', {}).get('iata', 'Unknown')
                
                # Extract departure times
                scheduled_departure = flight.get('departure', {}).get('scheduled', None)
                actual_departure = flight.get('departure', {}).get('actual', None)
                
                # Skip flights without both scheduled and actual departure times
                if not scheduled_departure or not actual_departure:
                    continue
                
                # Calculate delay in minutes
                try:
                    scheduled_dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                    actual_dt = datetime.fromisoformat(actual_departure.replace('Z', '+00:00'))
                    delay_minutes = int((actual_dt - scheduled_dt).total_seconds() / 60)
                except:
                    continue
                
                # Skip invalid airport codes
                if len(origin) != 3 or len(destination) != 3:
                    continue
                
                flight_data = {
                    'airline': airline,
                    'origin': origin,
                    'destination': destination,
                    'scheduled_departure': scheduled_departure,
                    'actual_departure': actual_departure,
                    'delay_minutes': delay_minutes,
                    'flight_number': flight.get('flight', {}).get('iata', 'Unknown')
                }
                
                flights.append(flight_data)
            
            print(f"Extracted {len(flights)} valid flights")
            
        except Exception as e:
            print(f"Error extracting flight data: {e}")
        
        return flights
    
    def collect_flights(self, airline: Optional[str], days_back: int, limit: int) -> pd.DataFrame:
        """Collect flights for the specified parameters."""
        all_flights = []
        dates_processed = 0
        
        # Generate dates going back from today
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        current_date = start_date
        while current_date <= end_date and len(all_flights) < limit:
            date_str = current_date.strftime('%Y-%m-%d')
            
            flights = self.get_flights_for_date(date_str, airline)
            all_flights.extend(flights)
            
            dates_processed += 1
            current_date += timedelta(days=1)
            
            # Add delay to avoid rate limiting
            if not self.mock_mode:
                time.sleep(1)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_flights)
        
        if len(df) == 0:
            print("No flights collected")
            return df
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['airline', 'origin', 'destination', 'scheduled_departure'])
        
        # Limit to requested number
        if len(df) > limit:
            df = df.head(limit)
        
        print(f"\nCollection Summary:")
        print(f"Dates processed: {dates_processed}")
        print(f"Total flights collected: {len(df)}")
        print(f"Unique airlines: {df['airline'].nunique()}")
        print(f"Unique origins: {df['origin'].nunique()}")
        print(f"Unique destinations: {df['destination'].nunique()}")
        print(f"Delay statistics: mean={df['delay_minutes'].mean():.2f}, std={df['delay_minutes'].std():.2f}")
        
        return df

def main():
    parser = argparse.ArgumentParser(description='Collect flight data from AviationStack')
    parser.add_argument('--airline', help='Airline IATA code (e.g., WN for Southwest)')
    parser.add_argument('--days-back', type=int, default=5, help='Number of days to go back (default: 5)')
    parser.add_argument('--limit', type=int, default=200, help='Maximum number of flights to collect (default: 200)')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API')
    parser.add_argument('--output', default='flights_dataset.csv', help='Output CSV file (default: flights_dataset.csv)')
    
    args = parser.parse_args()
    
    try:
        # Initialize collector
        collector = FlightDataCollector(mock_mode=args.mock)
        
        # Collect flights
        df = collector.collect_flights(args.airline, args.days_back, args.limit)
        
        if len(df) > 0:
            # Save to CSV
            df.to_csv(args.output, index=False)
            print(f"\nFlight data saved to {args.output}")
            print(f"Dataset shape: {df.shape}")
        else:
            print("No flight data collected")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 