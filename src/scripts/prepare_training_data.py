import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Find the root directory (two levels up from current script)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
input_csv_path = os.path.join(project_root, 'data', 'Airline_Delay_Cause.csv')


def expand_aggregated_bts_data(file_path: str, output_path: str = 'cleaned_data.csv'):
    """
    Convert aggregated BTS monthly data into synthetic flight-level data.
    This expands each row (representing a month of flights) into many individual
    flight records based on total_flights, simulating realistic variation.
    """
    df = pd.read_csv(file_path)

    synthetic_records = []
    for _, row in df.iterrows():
        total_flights = int(row['arr_flights'])
        if total_flights == 0:
            continue

        year = int(row['year'])
        month = int(row['month'])
        base_date = datetime(year, month, 1)

        avg_delay = row['arr_delay'] / total_flights if total_flights > 0 else 0
        std_delay = 15  # assume a spread in delay distribution

        for _ in range(total_flights):
            scheduled = base_date + timedelta(days=np.random.randint(0, 28),
                                              hours=np.random.randint(6, 22),
                                              minutes=np.random.randint(0, 60))

            delay_minutes = int(np.random.normal(loc=avg_delay, scale=std_delay))
            delay_minutes = max(min(delay_minutes, 360), -60)

            actual = scheduled + timedelta(minutes=delay_minutes)

            record = {
                'airline': row['carrier'],
                'flight_number': f"{row['carrier']}{np.random.randint(1000, 9999)}",
                'origin': row['airport'],
                'destination': 'SFO',
                'scheduled_departure': scheduled.isoformat(),
                'actual_departure': actual.isoformat(),
                'delay_minutes': delay_minutes
            }
            synthetic_records.append(record)

    synthetic_df = pd.DataFrame(synthetic_records)
    synthetic_df.to_csv(output_path, index=False)
    print(f"✅ Generated cleaned dataset with {len(synthetic_df)} rows and saved to {output_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv_path = os.path.join(script_dir, '..', '..', 'data', 'Airline_Delay_Cause.csv')
    input_csv_path = os.path.normpath(input_csv_path)
 
    output_csv_path = os.path.join(project_root, 'data', 'cleaned_data.csv')
    expand_aggregated_bts_data(input_csv_path, output_csv_path)
