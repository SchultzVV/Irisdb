# Databricks notebook source
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Get parameters from job (with fallback)
try:
    input_gold_table = dbutils.widgets.get("input_gold_table")
    output_model = dbutils.widgets.get("output_model")
except:
    input_gold_table = "default.iris_silver"  # Use silver data for training
    output_model = "iris_model"

# Load Silver data (better for ML training than aggregated Gold)
df_spark = spark.table(input_gold_table)
df = df_spark.toPandas()

# Prepare data
X = df.drop(columns=["species"])
y = df["species"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model with MLflow tracking
with mlflow.start_run():
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Log metrics and model
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("test_size", 0.2)
    mlflow.log_metric("accuracy", accuracy)
    
    # Log model
    mlflow.sklearn.log_model(model, output_model)
    
    print("✅ Model training complete")
    print(f"✅ Model accuracy: {accuracy:.4f}")
    print(f"✅ Model logged as: {output_model}")
acc = accuracy_score(y_test, y_pred)

# Log with MLflow
with mlflow.start_run():
    mlflow.log_metric("accuracy", acc)
    mlflow.sklearn.log_model(model, "iris_rf_model")
    print(f"✅ Model trained and logged with accuracy: {acc}")
