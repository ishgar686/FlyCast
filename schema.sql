-- Table to store user info and consent
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    school_year VARCHAR(20),
    consented BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store flight info tied to a user
CREATE TABLE user_flights (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    flight_number VARCHAR(10) NOT NULL,
    airline VARCHAR(100),
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    origin_airport VARCHAR(10),
    destination_airport VARCHAR(10),
    gate VARCHAR(10),
    terminal VARCHAR(10),
    predicted_delay_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store Uber estimates for a user-flight pair
CREATE TABLE rideshare_estimates (
    id SERIAL PRIMARY KEY,
    user_flight_id INTEGER REFERENCES user_flights(id) ON DELETE CASCADE,
    estimated_cost_usd NUMERIC(6, 2),
    estimated_duration_minutes INTEGER,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to track public matches (UCSD students on same flight)
CREATE TABLE flight_matches (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    matched_user_ids INTEGER[], -- Postgres array of user IDs
    match_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);