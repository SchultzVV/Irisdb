# Databricks notebook source
import seaborn as sns
import pandas as pd

# Load Iris dataset via seaborn
df = sns.load_dataset("iris")

# Convert to Spark DataFrame
df_spark = spark.createDataFrame(df)

# Save as Delta table in the Bronze layer
bronze_path = "/mnt/datalake/iris/bronze"
df_spark.write.mode("overwrite").format("delta").save(bronze_path)

print("✅ Bronze ingestion complete")
