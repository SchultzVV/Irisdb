# Databricks notebook source
from pyspark.sql.functions import col

# Load data from Bronze
bronze_path = "/mnt/datalake/iris/bronze"
df = spark.read.format("delta").load(bronze_path)

# Data cleaning and validation
df_clean = (
    df.dropna()
      .filter(col("sepal_length") > 0)
)

# Save to Silver layer
silver_path = "/mnt/datalake/iris/silver"
df_clean.write.mode("overwrite").format("delta").save(silver_path)

print("✅ Silver transformation complete")
