# Databricks notebook source

# Load data from Bronze 1
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
input_bronze_table = dbutils.widgets.get("input_bronze_table")
output_silver_table = dbutils.widgets.get("output_silver_table")

# Load data from Bronze 2
bronze_path = "/mnt/datalake/iris/bronze"
df = spark.read.format("delta").load(bronze_path)

# Validação de schema esperada
expected_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
assert df.columns == expected_columns, "❌ Schema inesperado na Bronze table"

# Exemplo de transformação
df_clean = df.dropna()

# Data cleaning and validation
from pyspark.sql.functions import col
df_clean = (
    df.dropna()
      .filter(col("sepal_length") > 0)
)

# Save to Silver layer 1
silver_path = "/mnt/datalake/iris/silver"
df_clean.write.mode("overwrite").format("delta").save(silver_path)

# Save to Silver layer 2
df_clean.write.mode("overwrite").saveAsTable(output_silver_table)

print("✅ Silver transformation complete")
