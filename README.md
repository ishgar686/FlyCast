✈️ FlyCast — Flight Delay & Travel Helper (CLI)
FlyCast is a CLI tool that predicts flight delay duration (minutes) and gives a quick rideshare cost + ETA to/from the airport. It saves your results to PostgreSQL and includes an optional, consent-based “public match” for UCSD travelers on the same flight.

Features
Delay prediction using a trained scikit-learn model (model.pkl)

Rideshare estimate (price + minutes) to/from the airport

History & analytics stored in PostgreSQL

Consent-first public matching (opt-in) for UCSD students on the same flight

Dockerized so anyone can run it from the terminal

Tech stack
Python, scikit-learn, PostgreSQL, Docker, and optional external APIs (Uber / Maps). Works with local Postgres or a managed instance (e.g., Cloud SQL on GCP).

Quickstart
1) Clone & env
bash
Copy
Edit
git clone <your-repo-url>
cd FlyCast
cp .env.example .env   # fill in values as needed
Minimal env you’ll want to set:

makefile
Copy
Edit
PGHOST=host.docker.internal
PGPORT=5432
PGDATABASE=flycast_db
PGUSER=ishaangarg
PGPASSWORD=
# Optional providers:
GOOGLE_MAPS_API_KEY=   # for address-based time/cost
UBER_BEARER_TOKEN=     # if you have Guest Rides access
2) Create the DB schema (once)
bash
Copy
Edit
psql -h localhost -p 5432 -U your_user -d flycast_db -f schema.sql
3) Run (Docker)
bash
Copy
Edit
docker build -t flycast .
docker run -it --rm --env-file .env \
  -e PGHOST=host.docker.internal -e PGPORT=5432 \
  -e PGDATABASE=flycast_db -e PGUSER=ishaangarg -e PGPASSWORD="" \
  -e FLYCAST_USE_MOCK=1 -e FLYCAST_MODEL_PATH=/app/model/model.pkl \
  flycast
(or) Run locally
bash
Copy
Edit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python cli.py
How it works (user flow)
The CLI asks for name / email / school year and consent (for UCSD matching).

Enter a flight number (e.g., WN1254).

Optionally provide a pickup/dropoff address (or miles) and a time for rideshare.

FlyCast prints:

Predicted delay in minutes

Estimated rideshare price + minutes

Choose to save results to your history.

Providers: if present, FlyCast uses configured providers for estimates and falls back gracefully when needed. No provider details are shown to the end user.

Database
Tables:

users — profile & consent

user_flights — saved flight queries + predictions

rideshare_estimates — cost + duration for a user/flight

flight_matches — experimental public match data

Peek inside with psql:

sql
Copy
Edit
\dt
SELECT * FROM users ORDER BY id DESC LIMIT 5;
SELECT * FROM user_flights ORDER BY id DESC LIMIT 5;
SELECT * FROM rideshare_estimates ORDER BY id DESC LIMIT 5;

-- who saved what (recent)
SELECT u.name, u.email, uf.flight_number, uf.airline,
       uf.predicted_delay_minutes, uf.created_at
FROM user_flights uf
JOIN users u ON u.id = uf.user_id
ORDER BY uf.created_at DESC
LIMIT 20;
Environment variables (common)
Name	Purpose
PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD	Postgres connection
FLYCAST_USE_MOCK	Use mock flight data during dev (1/0)
FLYCAST_MODEL_PATH	Path to model.pkl inside the container
GOOGLE_MAPS_API_KEY	(Optional) Enables address-based ride time/cost
UBER_BEARER_TOKEN	(Optional) Enables Uber estimates when available
UBER_ENV	sandbox or production (default: production)
FLYCAST_DEBUG	1 to print which estimate provider was used

Keep real secrets in .env only. Don’t commit them.

Training (optional)
If you want to (re)train:

bash
Copy
Edit
python src/scripts/prepare_training_data.py
python src/train_model.py
A new model/model.pkl will be produced.

Privacy & consent
Public matching is opt-in. If you decline, your flights aren’t included in any public match views.

Stored data is limited to what the CLI collects and the minimal fields needed for estimates and analytics.

Project structure (high level)
graphql
Copy
Edit
cli.py                    # interactive terminal app
schema.sql                # database schema
src/
  predict.py              # load model + predict delay
  scraper.py              # flight info fetching (dev-friendly)
  rideshare.py            # ride estimates (provider-aware, with fallback)
  db.py                   # Postgres connection helper
model/                    # trained model (model.pkl)
FAQ
Do I need API keys to get an estimate?
No—FlyCast still returns a basic estimate without keys. Keys enable richer, address-based results.

Can I use a cloud Postgres?
Yes. Set the PG env vars to your managed database (e.g., Cloud SQL).

Why no provider names in the CLI?
We keep the UX simple. The app quietly selects the best available provider and stores the result.