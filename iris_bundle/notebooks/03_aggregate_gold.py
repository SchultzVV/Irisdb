# Databricks notebook source
from pyspark.sql.functions import avg

# Load data from Silver
silver_path = "/mnt/datalake/iris/silver"
df = spark.read.format("delta").load(silver_path)

# Aggregation by species
df_gold = (
    df.groupBy("species")
      .agg(
          avg("sepal_length").alias("avg_sepal_length"),
          avg("sepal_width").alias("avg_sepal_width"),
          avg("petal_length").alias("avg_petal_length"),
          avg("petal_width").alias("avg_petal_width")
      )
)

# Save to Gold layer
gold_path = "/mnt/datalake/iris/gold"
df_gold.write.mode("overwrite").format("delta").save(gold_path)

print("✅ Gold aggregation complete")
