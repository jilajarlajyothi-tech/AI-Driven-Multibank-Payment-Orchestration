import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler


# ==========================================
# 1. LOAD DATASET
# ==========================================

DATASET_PATH = "ml/creditcard.csv"

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ==========================================
# 2. SEPARATE FEATURES AND TARGET
# ==========================================

X = df.drop("Class", axis=1)
y = df["Class"]


# ==========================================
# 3. SCALE AMOUNT
# ==========================================

scaler = StandardScaler()

X["Amount"] = scaler.fit_transform(
    X["Amount"].values.reshape(-1, 1)
)


# ==========================================
# 4. SPLIT DATA
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 5. CREATE MODEL
# ==========================================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)


# ==========================================
# 6. TRAIN MODEL
# ==========================================

print("\nTraining fraud detection model...")

model.fit(X_train, y_train)

print("Model training completed!")


# ==========================================
# 7. TEST MODEL
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 8. DISPLAY RESULTS
# ==========================================

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
# ==========================================
# 9. SAVE TRAINED MODEL
# ==========================================

joblib.dump(model, "ml/fraud_model.pkl")

# Save scaler also
joblib.dump(scaler, "ml/scaler.pkl")

print("\nModel saved successfully!")
print("Created: ml/fraud_model.pkl")
print("Created: ml/scaler.pkl")