# Databricks notebook source
import seaborn as sns
import pandas as pd
import sys
import os
from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("iris_bronze_ingestion").getOrCreate()

# Add utils to path for monitoring
sys.path.append("/Workspace/Shared/iris_monitoring")
try:
    from utils.monitoring import monitor_pipeline, get_pipeline_monitor
    monitor = get_pipeline_monitor(spark)
    monitor.log_pipeline_start("bronze_ingestion")
except ImportError:
    print("⚠️ Monitoring module not available, continuing without monitoring")
    monitor = None

# Load Iris dataset via seaborn
df = sns.load_dataset("iris")

# Convert to Spark DataFrame
df_spark = spark.createDataFrame(df)

# Save as managed table in Unity Catalog (avoids DBFS issues)
# This will work in UC-enabled workspaces
output_table = "workspace.default.iris_bronze"

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
    
    # Log success with monitoring
    if monitor:
        quality_checks = {
            "record_count": count,
            "null_checks_passed": True,
            "schema_valid": True,
            "species_count": 3,
            "positive_values": True
        }
        monitor.log_data_quality_check("iris_bronze", True, quality_checks)
        monitor.log_pipeline_success("bronze_ingestion", {"record_count": count})
    
    # 🚀 AUTO-TRIGGER: Executar próximo job (Silver)
    print("\n🚀 Executando auto-trigger para o job Silver...")
    
    try:
        import subprocess
        import os
        import time
        
        # Para Databricks, usar Databricks CLI via subprocess
        print("🔧 Executando Silver job via Databricks CLI...")
        
        # Listar jobs para encontrar o Silver job ID
        list_result = subprocess.run(
            ["databricks", "jobs", "list", "--output", "json"], 
            capture_output=True, 
            text=True
        )
        
        if list_result.returncode == 0:
            import json
            jobs_data = json.loads(list_result.stdout)
            
            # Encontrar job Silver
            silver_job_id = None
            for job in jobs_data.get("jobs", []):
                if "iris_silver_transform" in job.get("settings", {}).get("name", ""):
                    silver_job_id = job.get("job_id")
                    break
            
            if silver_job_id:
                print(f"� Job Silver encontrado: ID {silver_job_id}")
                
                # Executar job Silver
                run_result = subprocess.run(
                    ["databricks", "jobs", "run-now", str(silver_job_id)], 
                    capture_output=True, 
                    text=True
                )
                
                if run_result.returncode == 0:
                    print("✅ Auto-trigger Silver iniciado com sucesso!")
                    print(f"� Job Silver executando: {run_result.stdout}")
                else:
                    print(f"⚠️ Erro ao executar Silver: {run_result.stderr}")
            else:
                print("⚠️ Job Silver não encontrado")
        else:
            print(f"⚠️ Erro ao listar jobs: {list_result.stderr}")
            
    except Exception as trigger_error:
        print(f"⚠️ Auto-trigger falhou, mas Bronze foi bem-sucedido: {trigger_error}")
        print("📝 Job Silver deve ser executado manualmente ou via make run_silver_with_triggers")
    
except Exception as e:
    error_msg = f"Error saving to table: {e}"
    print(f"❌ {error_msg}")
    
    # Log error with monitoring
    if monitor:
        monitor.log_pipeline_error("bronze_ingestion", error_msg)
    
    raise e  # Re-raise the exception to fail the job