import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pickle
from datetime import datetime
import os


def load_and_clean_data(file_path: str = "data/cleaned_data.csv"):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', file_path))
    if 'delay_minutes' in df.columns:
        df['delay'] = df['delay_minutes']
    elif 'arr_delay' in df.columns:
        df['delay'] = df['arr_delay']
    elif 'dep_delay' in df.columns:
        df['delay'] = df['dep_delay']
    else:
        raise ValueError("No delay column found in dataset")

    df = df.dropna(subset=['delay'])

    delay_std = df['delay'].std()
    if delay_std > 1000:
        df['delay'] = df['delay'] / 60

    delay_mean = df['delay'].mean()
    delay_std = df['delay'].std()
    df = df[abs(df['delay'] - delay_mean) <= 3 * delay_std]

    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    if 'origin_airport' in df.columns:
        df['origin'] = df['origin_airport']
    else:
        df['origin'] = 'UNK'
    if 'destination_airport' in df.columns:
        df['destination'] = df['destination_airport']
    else:
        df['destination'] = 'UNK'
    if 'airline' not in df.columns:
        df['airline'] = df.get('carrier', 'UNK')

    if 'scheduled_departure' in df.columns:
        df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'])
    elif {'year', 'month', 'day_of_month'}.issubset(df.columns):
        df['scheduled_departure'] = pd.to_datetime(
            df[['year', 'month', 'day_of_month']].assign(hour=12),
            format='%Y-%m-%d'
        )
    elif 'fl_date' in df.columns:
        df['scheduled_departure'] = pd.to_datetime(df['fl_date'])
    else:
        df['scheduled_departure'] = pd.to_datetime('2023-01-01')

    df['hour'] = df['scheduled_departure'].dt.hour
    df['weekday'] = df['scheduled_departure'].dt.weekday

    df = df.dropna(subset=['origin', 'destination', 'airline'])
    df = df[df['origin'].astype(str).str.len() == 3]
    df = df[df['destination'].astype(str).str.len() == 3]

    return df


def create_encoders(df: pd.DataFrame):
    encoders = {
        'origin': {origin: idx for idx, origin in enumerate(df['origin'].unique())},
        'destination': {dest: idx for idx, dest in enumerate(df['destination'].unique())},
        'airline': {airline: idx for idx, airline in enumerate(df['airline'].unique())},
    }
    return encoders


def encode_features(df: pd.DataFrame, encoders: dict):
    df['origin_encoded'] = df['origin'].map(encoders['origin'])
    df['destination_encoded'] = df['destination'].map(encoders['destination'])
    df['airline_encoded'] = df['airline'].map(encoders['airline'])

    features = ['origin_encoded', 'destination_encoded', 'airline_encoded', 'hour', 'weekday']
    X = df[features]
    y = df['delay']
    return X, y


def train_model(X: pd.DataFrame, y: pd.Series):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    return model, mae


def save_model(model, encoders, mae):
    model_data = {
        'model': model,
        'encoders': encoders,
        'mae': mae,
        'features': ['origin_encoded', 'destination_encoded', 'airline_encoded', 'hour', 'weekday']
    }
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
    os.makedirs(model_dir, exist_ok=True)  # create if not exists
    model_path = os.path.join(model_dir, 'model.pkl')

    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)



def main():
    try:
        df = load_and_clean_data()
        df = create_features(df)
        encoders = create_encoders(df)
        X, y = encode_features(df, encoders)
        model, mae = train_model(X, y)
        save_model(model, encoders, mae)
        print(f"Training completed. MAE: {mae:.2f} minutes ({mae/60:.2f} hours)")
    except Exception as e:
        print(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()