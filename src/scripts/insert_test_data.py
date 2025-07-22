import psycopg2
from datetime import datetime, timedelta

import sys 
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from db_config import DB_CONFIG

try:
    # Connect to your PostgreSQL database using credentials from db_config
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Insert a test user
    cursor.execute("""
        INSERT INTO users (name, email, school_year, consented)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, ("Ishaan Garg", "ishaan@ucsd.edu", "Sophomore", True))
    user_id = cursor.fetchone()[0]

    # Insert a test flight tied to that user
    cursor.execute("""
        INSERT INTO user_flights (
            user_id, flight_number, airline, departure_time,
            arrival_time, origin_airport, destination_airport, gate, terminal,
            predicted_delay_minutes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        user_id,
        "UA123",
        "United Airlines",
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=1, hours=2, minutes=45),
        "SAN",
        "SFO",
        "A4",
        "T2",
        18
    ))

    # Commit changes and close connection
    conn.commit()
    print("✅ Inserted test user and flight successfully.")

except Exception as e:
    print("❌ Error inserting test data:", e)

finally:
    cursor.close()
    conn.close()