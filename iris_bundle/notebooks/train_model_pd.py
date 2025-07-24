# notebooks/04_train_model.py
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Leitura do dado Silver
silver_table = dbutils.widgets.get("input_gold_table")
model_name = dbutils.widgets.get("output_model")

df_spark = spark.table(silver_table)
df = df_spark.toPandas()

# Preparação
X = df.drop(columns=["species"])
y = df["species"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Treina novo modelo
model = RandomForestClassifier()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
new_acc = accuracy_score(y_test, y_pred)

# Busca última métrica registrada
client = mlflow.tracking.MlflowClient()
try:
    latest_versions = client.get_latest_versions(model_name)
    last_run_id = latest_versions[0].run_id
    last_acc = float(client.get_metric_history(last_run_id, "accuracy")[-1].value)
except Exception:
    last_acc = 0.0  # Nenhum modelo registrado ainda

# Compara e registra se melhorar
if new_acc > last_acc:
    with mlflow.start_run():
        mlflow.log_metric("accuracy", new_acc)
        mlflow.sklearn.log_model(model, "iris_rf_model")
        mlflow.register_model("runs:/" + mlflow.active_run().info.run_id + "/iris_rf_model", model_name)
        print(f"✅ Novo modelo registrado! Accuracy: {new_acc:.4f} (anterior: {last_acc:.4f})")
else:
    print(f"⚠️ Novo modelo descartado. Accuracy {new_acc:.4f} ≤ {last_acc:.4f}")
