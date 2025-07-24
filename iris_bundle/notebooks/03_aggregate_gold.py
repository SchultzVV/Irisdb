# Databricks notebook source
from pyspark.sql.functions import avg, count

# Get parameters from job (with fallback)
try:
    input_silver_table = dbutils.widgets.get("input_silver_table")
    output_gold_table = dbutils.widgets.get("output_gold_table")
except:
    input_silver_table = "default.iris_silver"
    output_gold_table = "default.iris_gold"

# Load data from Silver table (Unity Catalog)
df = spark.table(input_silver_table)

# Aggregation by species
df_gold = (
    df.groupBy("species")
      .agg(
          avg("sepal_length").alias("avg_sepal_length"),
          avg("sepal_width").alias("avg_sepal_width"),
          avg("petal_length").alias("avg_petal_length"),
          avg("petal_width").alias("avg_petal_width"),
          count("*").alias("count")
      )
)

# Save to Gold layer (Unity Catalog table)
df_gold.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_gold_table)

print("✅ Gold aggregation complete")
print(f"✅ Data saved to table: {output_gold_table}")
print(f"✅ Aggregated {df_gold.count()} species")
