# Databricks notebook source
import seaborn as sns
import pandas as pd

# Load Iris dataset via seaborn
df = sns.load_dataset("iris")

# Convert to Spark DataFrame
df_spark = spark.createDataFrame(df)

# Save as managed table in Unity Catalog (avoids DBFS issues)
# This will work in UC-enabled workspaces
output_table = "default.iris_bronze"

try:
    # Try to save as managed table
    df_spark.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_table)
    print(f"✅ Bronze ingestion complete - saved to table: {output_table}")
    
    # Show count to verify
    count = spark.table(output_table).count()
    print(f"✅ Table contains {count} rows")
    
except Exception as e:
    print(f"❌ Error saving to table: {e}")
    # Fallback: try to save to workspace tmp location
    fallback_path = "/tmp/iris_bronze_data"
    df_spark.write.mode("overwrite").format("parquet").save(fallback_path)
    print(f"✅ Saved to fallback location: {fallback_path}")
