# Databricks notebook source

# Load data from Bronze layer (Unity Catalog)
from pyspark.sql import SparkSession

# Get parameters from job (with fallback)
try:
    input_bronze_table = dbutils.widgets.get("input_bronze_table")
    output_silver_table = dbutils.widgets.get("output_silver_table")
except:
    input_bronze_table = "workspace.default.iris_bronze"
    output_silver_table = "workspace.default.iris_silver"

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

# 🧪 VALIDAÇÕES SILVER
print("\n🧪 Executando validações Silver...")

# Validação 1: Sem valores nulos (após limpeza)
from pyspark.sql.functions import col, count as spark_count, when

null_counts = df_clean.select([
    spark_count(when(col(c).isNull(), c)).alias(c) for c in df_clean.columns
]).collect()[0]

for col_name in df_clean.columns:
    null_count = null_counts[col_name]
    assert null_count == 0, f"❌ Silver ainda tem nulos em {col_name}: {null_count}"

print("✅ Silver: Sem valores nulos")

# Validação 2: Todos os valores são positivos
numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
for col_name in numeric_cols:
    min_val = df_clean.select(col(col_name)).agg({col_name: "min"}).collect()[0][0]
    assert min_val > 0, f"❌ Valores não positivos em {col_name}: {min_val}"

print("✅ Silver: Todos os valores numéricos positivos")

# Validação 3: Contagem razoável após limpeza
final_count = df_clean.count()
assert final_count >= 100, f"❌ Muitos dados perdidos na limpeza: {final_count}"
print(f"✅ Silver: {final_count} registros limpos mantidos")

print("🎉 SILVER: Todas as validações passaram!")
