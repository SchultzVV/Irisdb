# Databricks notebook source
# MAGIC %md
# MAGIC # 🧪 Data Quality Validation - PySpark Native
# MAGIC 
# MAGIC Este notebook implementa validações de qualidade de dados usando PySpark nativo para máxima compatibilidade.

# COMMAND ----------

from pyspark.sql.functions import col, count, when, isnan, isnull, min as spark_min, max as spark_max
import json
from datetime import datetime

print("🧪 Iniciando validação de qualidade de dados...")
print(f"⏰ Timestamp: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔵 Validação Bronze Layer

# COMMAND ----------

def validate_bronze_table():
    """Valida a tabela Bronze"""
    print("🔵 Validando tabela Bronze...")
    
    try:
        df_bronze = spark.table("default.iris_bronze")
        
        # Contagem de registros
        count_bronze = df_bronze.count()
        print(f"📊 Registros Bronze: {count_bronze}")
        
        # Validações
        validations = {
            "count_valid": 100 <= count_bronze <= 200,
            "no_nulls": df_bronze.filter(col("species").isNull()).count() == 0,
            "schema_valid": len(df_bronze.columns) == 5,
            "species_valid": df_bronze.select("species").distinct().count() == 3
        }
        
        all_passed = all(validations.values())
        print(f"✅ Bronze validação: {'PASSOU' if all_passed else 'FALHOU'}")
        
        return {"success": all_passed, "details": validations, "count": count_bronze}
        
    except Exception as e:
        print(f"❌ Erro na validação Bronze: {e}")
        return {"success": False, "details": {"error": str(e)}, "count": 0}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥈 Validação Silver Layer

# COMMAND ----------

def validate_silver_table():
    """Valida a tabela Silver"""
    print("🥈 Validando tabela Silver...")
    
    try:
        df_silver = spark.table("default.iris_silver")
        
        # Contagem de registros
        count_silver = df_silver.count()
        print(f"📊 Registros Silver: {count_silver}")
        
        # Validações
        validations = {
            "count_valid": count_silver > 0,
            "no_nulls": df_silver.filter(
                col("sepal_length").isNull() | 
                col("sepal_width").isNull() | 
                col("petal_length").isNull() | 
                col("petal_width").isNull()
            ).count() == 0,
            "positive_values": df_silver.filter(
                (col("sepal_length") <= 0) | 
                (col("sepal_width") <= 0) | 
                (col("petal_length") <= 0) | 
                (col("petal_width") <= 0)
            ).count() == 0
        }
        
        all_passed = all(validations.values())
        print(f"✅ Silver validação: {'PASSOU' if all_passed else 'FALHOU'}")
        
        return {"success": all_passed, "details": validations, "count": count_silver}
        
    except Exception as e:
        print(f"❌ Erro na validação Silver: {e}")
        return {"success": False, "details": {"error": str(e)}, "count": 0}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥇 Validação Gold Layer

# COMMAND ----------

def validate_gold_table():
    """Valida a tabela Gold"""
    print("🥇 Validando tabela Gold...")
    
    try:
        df_gold = spark.table("default.iris_gold")
        
        # Contagem de registros
        count_gold = df_gold.count()
        print(f"📊 Registros Gold: {count_gold}")
        
        # Validações
        validations = {
            "count_valid": count_gold == 3,  # 3 espécies
            "avg_columns_exist": "avg_sepal_length" in df_gold.columns,
            "count_column_exists": "count_records" in df_gold.columns,
            "reasonable_averages": True  # Verificaremos depois
        }
        
        # Verificar se as médias estão em ranges razoáveis
        if validations["avg_columns_exist"]:
            avg_stats = df_gold.select(
                spark_min("avg_sepal_length"),
                spark_max("avg_sepal_length")
            ).collect()[0]
            
            validations["reasonable_averages"] = (
                avg_stats[0] > 3.0 and avg_stats[1] < 10.0
            )
        
        all_passed = all(validations.values())
        print(f"✅ Gold validação: {'PASSOU' if all_passed else 'FALHOU'}")
        
        return {"success": all_passed, "details": validations, "count": count_gold}
        
    except Exception as e:
        print(f"❌ Erro na validação Gold: {e}")
        return {"success": False, "details": {"error": str(e)}, "count": 0}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚀 Execução das Validações

# COMMAND ----------

# Executar todas as validações
print("🚀 Executando todas as validações...")

bronze_result = validate_bronze_table()
silver_result = validate_silver_table()
gold_result = validate_gold_table()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Resultados Consolidados

# COMMAND ----------

# Consolidar resultados
pipeline_quality_passed = (
    bronze_result["success"] and 
    silver_result["success"] and 
    gold_result["success"]
)

print(f"\n🎯 RESULTADO FINAL: {'✅ PASSOU' if pipeline_quality_passed else '❌ FALHOU'}")
print(f"🔵 Bronze: {'✅' if bronze_result['success'] else '❌'}")
print(f"🥈 Silver: {'✅' if silver_result['success'] else '❌'}")
print(f"🥇 Gold: {'✅' if gold_result['success'] else '❌'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Métricas para Monitoramento

# COMMAND ----------

# Exportar métricas para monitoramento
try:
    run_timestamp = dbutils.widgets.get("run_timestamp")
except:
    run_timestamp = "manual_run"

quality_metrics = {
    "timestamp": run_timestamp,
    "bronze_validation": bronze_result["success"],
    "silver_validation": silver_result["success"], 
    "gold_validation": gold_result["success"],
    "pipeline_quality_status": pipeline_quality_passed,
    "tables_validated": ["default.iris_bronze", "default.iris_silver", "default.iris_gold"]
}

print("📊 Métricas de Qualidade:")
print(json.dumps(quality_metrics, indent=2))

# COMMAND ----------

# Se alguma validação falhar, falhar o job
if not pipeline_quality_passed:
    raise Exception("❌ Validação de qualidade falhou! Verifique os logs acima.")

print("🎉 Todas as validações de qualidade passaram!")
