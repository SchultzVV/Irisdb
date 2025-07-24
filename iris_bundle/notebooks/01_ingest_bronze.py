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
    
    # 🧪 VALIDAÇÕES BÁSICAS DE QUALIDADE
    print("\n🧪 Executando validações básicas de qualidade...")
    
    # Validação 1: Contagem de registros
    assert count >= 100 and count <= 200, f"❌ Contagem inesperada: {count}"
    print(f"✅ Contagem válida: {count} registros")
    
    # Validação 2: Schema correto
    df_check = spark.table(output_table)
    expected_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
    actual_columns = df_check.columns
    assert actual_columns == expected_columns, f"❌ Schema incorreto: {actual_columns}"
    print("✅ Schema válido")
    
    # Validação 3: Sem valores nulos nas colunas críticas
    from pyspark.sql.functions import col, isnan, when, count as spark_count
    
    null_check = df_check.select([
        spark_count(when(col(c).isNull(), c)).alias(c) for c in expected_columns
    ]).collect()[0]
    
    for col_name in expected_columns:
        null_count = null_check[col_name]
        if null_count > 0:
            print(f"⚠️ {null_count} valores nulos em {col_name}")
    
    # Validação 4: Espécies válidas
    species_list = [row['species'] for row in df_check.select("species").distinct().collect()]
    expected_species = ["setosa", "versicolor", "virginica"]
    assert len(species_list) == 3, f"❌ Número de espécies incorreto: {len(species_list)}"
    print(f"✅ Espécies encontradas: {species_list}")
    
    # Validação 5: Valores numéricos positivos
    numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    for col_name in numeric_cols:
        min_val = df_check.select(col(col_name)).agg({col_name: "min"}).collect()[0][0]
        assert min_val > 0, f"❌ Valores não positivos em {col_name}: {min_val}"
    print("✅ Todos os valores numéricos são positivos")
    
    print("🎉 BRONZE: Todas as validações passaram!")
    
except Exception as e:
    print(f"❌ Error saving to table: {e}")
    raise e  # Re-raise the exception to fail the job
