import os
import re
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FLIGHT_RE = re.compile(r"^[A-Z]{2,3}\d{1,4}$")  # e.g., WN1254


def prompt_nonempty(prompt):
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Please enter something.")


def prompt_yes_no(prompt, default=False):
    suffix = " [y/N]: " if not default else " [Y/n]: "
    while True:
        v = input(prompt + suffix).strip().lower()
        if v == "" and default is not None:
            return default
        if v in ("y", "yes"):
            return True
        if v in ("n", "no"):
            return False
        print("Please answer y or n.")


def main():
    # 1) User info
    print("=== FlyCast ===")
    name = prompt_nonempty("Your name: ")

    while True:
        email = prompt_nonempty("Your email (used to save your flights): ")
        if EMAIL_RE.match(email):
            break
        print("⚠️  That doesn't look like a valid email. Try again.")

    school_year = input("School year (freshman/sophomore/junior/senior/grad) [optional]: ").strip()
    consented = prompt_yes_no("Opt in to public matching with other UCSD students on the same flight?", default=False)

    # 2) Flight
    flight_number = prompt_nonempty("Enter flight number (e.g., WN1254): ").upper()
    if not FLIGHT_RE.match(flight_number):
        print("⚠️  Invalid flight number format. Please enter something like 'WN1254'.")
        return

    # Optional rideshare inputs
    wants_ride = prompt_yes_no("Do you want a rideshare estimate to/from the airport?", default=True)
    rider_address = ""
    rider_miles = None
    ride_time = ""
    if wants_ride:
        print("\nRideshare options:")
        rider_address = input("Pickup/dropoff address (optional; works best with Google key): ").strip()
        miles_str = input("If no address or no key: approx miles to airport (optional number): ").strip()
        try:
            rider_miles = float(miles_str) if miles_str else None
        except Exception:
            rider_miles = None
        ride_time = input("Pickup time (HH:MM 24h, local) [Enter for now]: ").strip()

    # Internal config (no user prompts)
    use_mock = (os.getenv("FLYCAST_USE_MOCK", "1") == "1")
    model_path = os.getenv("FLYCAST_MODEL_PATH", "model/model.pkl")

    # 3) Predict
    from src.db import get_db_connection
    from src.scraper import FlightDataFetcher
    from src.predict import load_model, predict_delay

    model, encoders = load_model(model_path)
    if not model:
        print("❌ Could not load model.")
        return

    mock_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_flights"))
    fetcher = FlightDataFetcher(mock_mode=use_mock, mock_dir=mock_dir)
    flight_data = fetcher.get_flight_info(flight_number)
    if not flight_data:
        print("❌ Could not fetch flight data.")
        return

    delay_prediction = predict_delay(model, flight_data, encoders)
    if delay_prediction is None:
        print("❌ Prediction failed.")
        return

    print(f"\nPredicted delay for {flight_number}: {round(float(delay_prediction), 2)} minutes")

    # 4) Save (quiet)
    if not prompt_yes_no("Save this to your FlyCast history?", default=True):
        print("Done.")
        return

    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to the database.")
        return

    try:
        with conn:
            with conn.cursor() as cur:
                # Upsert or fetch user
                cur.execute(
                    """
                    INSERT INTO users (name, email, school_year, consented)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE
                      SET name = EXCLUDED.name,
                          school_year = EXCLUDED.school_year,
                          consented = EXCLUDED.consented
                    RETURNING id;
                    """,
                    (name, email, school_year or None, consented),
                )
                user_id = cur.fetchone()[0]

                # Map flight fields
                airline = flight_data.get("airline", "Unknown")
                dep_ts = flight_data.get("departure_time")
                arr_ts = flight_data.get("arrival_time")
                origin = flight_data.get("origin") or flight_data.get("origin_airport")
                dest = flight_data.get("destination") or flight_data.get("destination_airport")
                gate = flight_data.get("gate")
                terminal = flight_data.get("terminal")

                # Insert flight and get id
                cur.execute(
                    """
                    INSERT INTO user_flights (
                        user_id, flight_number, airline, departure_time, arrival_time,
                        origin_airport, destination_airport, gate, terminal, predicted_delay_minutes
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id;
                    """,
                    (
                        user_id,
                        flight_number,
                        airline,
                        dep_ts,
                        arr_ts,
                        origin,
                        dest,
                        gate,
                        terminal,
                        round(float(delay_prediction), 2),
                    ),
                )
                uf_id = cur.fetchone()[0]

                # 5) Rideshare estimate (print + save)
                if wants_ride:
                    airport_code = None
                    direction = None
                    origin_up = (origin or "").upper()
                    dest_up   = (dest or "").upper()
                    if origin_up in ("SAN", "KSAN"):
                        airport_code = "SAN"
                        direction = "from_airport"
                    elif dest_up in ("SAN", "KSAN"):
                        airport_code = "SAN"
                        direction = "to_airport"

                    est_tuple = None
                    if airport_code:
                        from src.rideshare import estimate_to_from_airport
                        est_tuple = estimate_to_from_airport(
                            airport_code,
                            address=rider_address or None,
                            miles_override=rider_miles,
                            when_hhmm=ride_time or None,
                            direction=direction,
                        )
                    elif rider_miles is not None:
                        # Generic miles-based estimate when airport unsupported
                        from src.rideshare import estimate_to_from_airport
                        est_tuple = estimate_to_from_airport(
                            "SAN",  # coords not used in miles-only path
                            address=None,
                            miles_override=rider_miles,
                            when_hhmm=ride_time or None,
                            direction="to_airport",
                        )

                    if est_tuple:
                        est_cost, est_mins = est_tuple
                        print(f"Rideshare estimate: ${est_cost} ~ {est_mins} min")
                        cur.execute(
                            """
                            INSERT INTO rideshare_estimates (
                                user_flight_id, estimated_cost_usd, estimated_duration_minutes
                            ) VALUES (%s, %s, %s)
                            """,
                            (uf_id, est_cost, est_mins),
                        )
                    else:
                        print("Rideshare estimate: (skipped — need an address+key or miles)")

        print("Saved to database.")
    except Exception as e:
        print(f"❌ DB error while saving: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()