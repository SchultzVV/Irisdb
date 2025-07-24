# Databricks notebook source

# Load data from Bronze layer (Unity Catalog)
from pyspark.sql import SparkSession

# Get parameters from job (with fallback)
try:
    input_bronze_table = dbutils.widgets.get("input_bronze_table")
    output_silver_table = dbutils.widgets.get("output_silver_table")
except:
    input_bronze_table = "default.iris_bronze"
    output_silver_table = "default.iris_silver"

# Load data from Bronze table (not DBFS path)
df = spark.table(input_bronze_table)

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
      .filter(col("sepal_width") > 0)
      .filter(col("petal_length") > 0)
      .filter(col("petal_width") > 0)
)

# Save to Silver layer (Unity Catalog table)
df_clean.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_silver_table)

print("✅ Silver transformation complete")
print(f"✅ Data saved to table: {output_silver_table}")
print(f"✅ Cleaned {df_clean.count()} rows")
df_clean.write.mode("overwrite").saveAsTable(output_silver_table)

print("✅ Silver transformation complete")
