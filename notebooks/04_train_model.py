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

print(f"🔍 Loading data from: {input_gold_table}")

# Load Silver data (better for ML training than aggregated Gold)
df_spark = spark.table(input_gold_table)
df = df_spark.toPandas()

print(f"📊 Dataset shape: {df.shape}")

# 🧪 VALIDAÇÕES DE QUALIDADE PARA ML
print("\n🧪 Executando validações para ML...")

# Validação 1: Dataset não vazio
assert len(df) > 0, "❌ Dataset vazio!"
print(f"✅ Dataset com {len(df)} registros")

# Validação 2: Colunas necessárias existem
expected_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
missing_cols = [col for col in expected_columns if col not in df.columns]
assert len(missing_cols) == 0, f"❌ Colunas faltando: {missing_cols}"
print("✅ Todas as colunas necessárias presentes")

# Validação 3: Sem valores nulos
assert df.isnull().sum().sum() == 0, "❌ Dataset contém valores nulos!"
print("✅ Nenhum valor nulo encontrado")

# Prepare data
X = df.drop(columns=["species"])
y = df["species"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"🔍 Training set: {len(X_train)} samples")
print(f"🔍 Test set: {len(X_test)} samples")

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
    mlflow.log_param("random_state", 42)
    mlflow.log_metric("accuracy", accuracy)
    
    # Log model
    mlflow.sklearn.log_model(model, output_model)
    
    print("✅ Model training complete")
    print(f"✅ Model accuracy: {accuracy:.4f}")
    print(f"✅ Model logged as: {output_model}")
    
    # Validação 4: Accuracy mínima
    assert accuracy > 0.8, f"❌ Accuracy muito baixa: {accuracy:.4f}"
    print(f"✅ Accuracy aceitável: {accuracy:.4f}")

print("\n🎯 ML pipeline completed successfully!")
