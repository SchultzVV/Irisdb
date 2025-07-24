# notebooks/05_batch_inference.py
from datetime import datetime
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

if datetime.now().hour in range(9, 18):
    print("Executando inferência em horário comercial...")
    model_name = dbutils.widgets.get("model_name")
    input_data_table = dbutils.widgets.get("input_data_table")

    df = spark.table(input_data_table)
    print(f"🔍 Rodaria inferência com modelo: {model_name}")
    # Aqui você poderia carregar o modelo via MLflow e prever
else:
    print("⏰ Fora do horário comercial. Inferência não executada.")
