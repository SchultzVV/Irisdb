# Databricks notebook source
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load Silver data
silver_path = "/mnt/datalake/iris/silver"
df_spark = spark.read.format("delta").load(silver_path)
df = df_spark.toPandas()

# Prepare data
X = df.drop(columns=["species"])
y = df["species"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

# Log with MLflow
with mlflow.start_run():
    mlflow.log_metric("accuracy", acc)
    mlflow.sklearn.log_model(model, "iris_rf_model")
    print(f"✅ Model trained and logged with accuracy: {acc}")
