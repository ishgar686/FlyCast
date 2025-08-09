# ✈️ FlyCast: Flight Delay Duration Predictor

FlyCast is a machine learning pipeline that predicts **flight delay duration in minutes** using data from the U.S. Bureau of Transportation Statistics (BTS).

## 🔧 Features
- Generates synthetic flight-level data from monthly BTS reports
- Trains a Random Forest regression model
- Achieves ~12 minute MAE using real-world airline performance data
- Outputs a `model.pkl` for future inference

## 🗂️ Project Structure
- `src/train_model.py`: Full training pipeline
- `src/scripts/prepare_training_data.py`: Converts BTS CSV into flight-level data
- `data/`: Raw and processed data
- `model/`: Trained model output

## 🏃‍♂️ How to Run
```bash
# Generate synthetic data
python src/scripts/prepare_training_data.py

# Train the model
python src/train_model.py


# How Users Can Interact
Example:
```bash
python src/cli.py WN1254
Replace WN1254 with your flight number to receive a delay estimate and status update.

