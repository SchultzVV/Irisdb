# Databricks notebook source
# MAGIC %md
# MAGIC # 🧪 Data Quality Validation with Great Expectations
# MAGIC 
# MAGIC Este notebook implementa validações de qualidade de dados usando Great Expectations em cada camada do pipeline.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Setup e Importações

# COMMAND ----------

import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.core.yaml_handler import YAMLHandler
import json
import os

# spark e dbutils são disponíveis implicitamente no Databricks
# from pyspark.sql import SparkSession - não necessário no Databricks

# Configuração do contexto Great Expectations
context_root_dir = "/Workspace/Users/xultezz@gmail.com/.bundle/iris_bundle/dev/files/great_expectations"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Utility Functions

# COMMAND ----------

def get_ge_context():
    """Obtém o contexto do Great Expectations"""
    try:
        context = gx.get_context(context_root_dir=context_root_dir)
        return context
    except Exception as e:
        print(f"❌ Erro ao obter contexto GE: {e}")
        return None

def validate_table(table_name, checkpoint_name):
    """
    Valida uma tabela usando um checkpoint específico
    
    Args:
        table_name (str): Nome da tabela no Unity Catalog
        checkpoint_name (str): Nome do checkpoint a executar
    
    Returns:
        dict: Resultado da validação
    """
    try:
        context = get_ge_context()
        if not context:
            return {"success": False, "error": "Contexto GE não disponível"}
        
        # Criar batch request
        batch_request = RuntimeBatchRequest(
            datasource_name="iris_data",
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name=table_name,
            runtime_parameters={"query": f"SELECT * FROM {table_name}"},
            batch_identifiers={"default_identifier_name": f"{table_name}_batch"}
        )
        
        # Executar checkpoint
        results = context.run_checkpoint(
            checkpoint_name=checkpoint_name,
            validations=[
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": checkpoint_name.replace("_checkpoint", "_suite")
                }
            ]
        )
        
        return {
            "success": results["success"],
            "statistics": results.get("statistics", {}),
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": table_name,
            "checkpoint": checkpoint_name
        }

def print_validation_summary(validation_result, layer_name):
    """Imprime um resumo da validação de forma user-friendly"""
    print(f"\n{'='*60}")
    print(f"🧪 VALIDAÇÃO {layer_name.upper()} LAYER")
    print(f"{'='*60}")
    
    if validation_result["success"]:
        print("✅ STATUS: PASSOU EM TODAS AS VALIDAÇÕES")
        stats = validation_result.get("statistics", {})
        if stats:
            print(f"📊 Expectativas avaliadas: {stats.get('evaluated_expectations', 'N/A')}")
            print(f"✅ Expectativas bem-sucedidas: {stats.get('successful_expectations', 'N/A')}")
            print(f"❌ Expectativas falharam: {stats.get('unsuccessful_expectations', 0)}")
            print(f"📈 Taxa de sucesso: {stats.get('success_percent', 'N/A')}%")
    else:
        print("❌ STATUS: FALHOU EM ALGUMAS VALIDAÇÕES")
        print(f"🔍 Erro: {validation_result.get('error', 'Erro desconhecido')}")
    
    print(f"{'='*60}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔵 Bronze Layer Validation

# COMMAND ----------

def validate_bronze_layer():
    """Valida a camada Bronze"""
    print("🔵 Iniciando validação da camada Bronze...")
    
    table_name = "default.iris_bronze"
    checkpoint_name = "iris_bronze_checkpoint"
    
    # Verificar se a tabela existe
    try:
        count = spark.table(table_name).count()
        print(f"📊 Tabela {table_name} encontrada com {count} registros")
    except Exception as e:
        print(f"❌ Tabela {table_name} não encontrada: {e}")
        return {"success": False, "error": f"Tabela não existe: {e}"}
    
    # Executar validação
    result = validate_table(table_name, checkpoint_name)
    print_validation_summary(result, "Bronze")
    
    return result

# Executar validação Bronze
bronze_result = validate_bronze_layer()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥈 Silver Layer Validation

# COMMAND ----------

def validate_silver_layer():
    """Valida a camada Silver"""
    print("🥈 Iniciando validação da camada Silver...")
    
    table_name = "default.iris_silver"
    checkpoint_name = "iris_silver_checkpoint"
    
    # Verificar se a tabela existe
    try:
        count = spark.table(table_name).count()
        print(f"📊 Tabela {table_name} encontrada com {count} registros")
    except Exception as e:
        print(f"❌ Tabela {table_name} não encontrada: {e}")
        return {"success": False, "error": f"Tabela não existe: {e}"}
    
    # Executar validação
    result = validate_table(table_name, checkpoint_name)
    print_validation_summary(result, "Silver")
    
    return result

# Executar validação Silver (apenas se Bronze passou)
if bronze_result["success"]:
    silver_result = validate_silver_layer()
else:
    print("⏭️ Pulando validação Silver - Bronze falhou")
    silver_result = {"success": False, "error": "Bronze validation failed"}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥇 Gold Layer Validation

# COMMAND ----------

def validate_gold_layer():
    """Valida a camada Gold"""
    print("🥇 Iniciando validação da camada Gold...")
    
    table_name = "default.iris_gold"
    checkpoint_name = "iris_gold_checkpoint"
    
    # Verificar se a tabela existe
    try:
        count = spark.table(table_name).count()
        print(f"📊 Tabela {table_name} encontrada com {count} registros")
        
        # Mostrar preview dos dados Gold
        print("👀 Preview dos dados Gold:")
        spark.table(table_name).show(5, truncate=False)
        
    except Exception as e:
        print(f"❌ Tabela {table_name} não encontrada: {e}")
        return {"success": False, "error": f"Tabela não existe: {e}"}
    
    # Executar validação
    result = validate_table(table_name, checkpoint_name)
    print_validation_summary(result, "Gold")
    
    return result

# Executar validação Gold (apenas se Silver passou)
if silver_result["success"]:
    gold_result = validate_gold_layer()
else:
    print("⏭️ Pulando validação Gold - Silver falhou")
    gold_result = {"success": False, "error": "Silver validation failed"}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Relatório Final de Qualidade

# COMMAND ----------

def generate_quality_report():
    """Gera relatório final de qualidade de dados"""
    print("🎯 RELATÓRIO FINAL DE QUALIDADE DE DADOS")
    print("="*70)
    
    layers = [
        ("Bronze", bronze_result),
        ("Silver", silver_result), 
        ("Gold", gold_result)
    ]
    
    all_passed = True
    
    for layer_name, result in layers:
        status = "✅ PASSOU" if result["success"] else "❌ FALHOU"
        print(f"{layer_name:<10} | {status}")
        
        if not result["success"]:
            all_passed = False
            error = result.get("error", "Erro desconhecido")
            print(f"           | 🔍 {error}")
    
    print("="*70)
    
    if all_passed:
        print("🎉 PIPELINE DE QUALIDADE: TODOS OS LAYERS PASSARAM!")
        print("✅ Os dados estão prontos para uso em produção")
    else:
        print("⚠️  PIPELINE DE QUALIDADE: ALGUMAS VALIDAÇÕES FALHARAM")
        print("🔧 Revise os dados antes de prosseguir para produção")
    
    print("="*70)
    
    return all_passed

# Gerar relatório final
pipeline_quality_passed = generate_quality_report()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚨 Alertas e Notificações

# COMMAND ----------

def send_quality_alerts():
    """Envia alertas baseados nos resultados de qualidade"""
    
    if not pipeline_quality_passed:
        print("🚨 ALERTA DE QUALIDADE DE DADOS!")
        print("📧 Em produção, isso enviaria:")
        print("   - Email para equipe de dados")
        print("   - Slack notification")
        print("   - Dashboard alert")
        print("   - Log para sistema de monitoramento")
    else:
        print("🔔 Notificação: Pipeline de qualidade executado com sucesso")
        print("📊 Dados validados e aprovados para uso")

# Executar alertas
send_quality_alerts()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Métricas para Monitoramento

# COMMAND ----------

# Exportar métricas para monitoramento
quality_metrics = {
    "timestamp": dbutils.widgets.get("run_timestamp") if "run_timestamp" in [w.name for w in dbutils.widgets.getAll()] else "manual_run",
    "bronze_validation": bronze_result["success"],
    "silver_validation": silver_result["success"], 
    "gold_validation": gold_result["success"],
    "pipeline_quality_status": pipeline_quality_passed,
    "tables_validated": ["default.iris_bronze", "default.iris_silver", "default.iris_gold"]
}

print("📊 Métricas de Qualidade:")
print(json.dumps(quality_metrics, indent=2))

# Em produção, essas métricas seriam enviadas para:
# - CloudWatch/Azure Monitor
# - Datadog
# - Prometheus
# - Sistema interno de métricas
