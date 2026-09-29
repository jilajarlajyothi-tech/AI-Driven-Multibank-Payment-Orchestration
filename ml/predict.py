import pandas as pd
import joblib

# Load trained model
model = joblib.load("ml/fraud_model.pkl")

# Load scaler
scaler = joblib.load("ml/scaler.pkl")

print("Fraud detection model loaded successfully!")

# Load dataset
df = pd.read_csv("ml/creditcard.csv")

# Select one transaction
transaction = df.drop("Class", axis=1).iloc[[0]]

# Scale Amount
transaction["Amount"] = scaler.transform(
    transaction["Amount"].values.reshape(-1, 1)
).flatten()

# Make prediction
prediction = model.predict(transaction)[0]

# Get fraud probability
probability = model.predict_proba(transaction)[0][1]

print()
print("Transaction Analysis")
print("--------------------")

if prediction == 1:
    print("Result: FRAUDULENT TRANSACTION")
else:
    print("Result: NORMAL TRANSACTION")

print("Fraud Probability:", round(probability * 100, 2), "%")