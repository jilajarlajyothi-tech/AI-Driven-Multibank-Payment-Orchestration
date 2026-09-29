import os
import joblib
import pandas as pd


# Get the project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Model paths
MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "fraud_model.pkl"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "scaler.pkl"
)


# Load model and scaler
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def detect_fraud(transaction_data):
    """
    Analyze a transaction and return fraud probability.
    """

    # Convert transaction data into DataFrame
    transaction = pd.DataFrame([transaction_data])

    # Scale Amount
    transaction["Amount"] = scaler.transform(
        transaction["Amount"].values.reshape(-1, 1)
    ).flatten()

    # Prediction
    prediction = model.predict(transaction)[0]

    # Fraud probability
    fraud_probability = model.predict_proba(
        transaction
    )[0][1]

    # Convert probability to percentage
    fraud_percentage = fraud_probability * 100


    # Determine risk
    if fraud_percentage < 20:
        risk_level = "LOW"

    elif fraud_percentage < 60:
        risk_level = "MEDIUM"

    else:
        risk_level = "HIGH"


    return {
        "prediction": int(prediction),
        "fraud_probability": round(fraud_percentage, 2),
        "risk_level": risk_level
    }