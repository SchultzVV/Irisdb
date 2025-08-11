# Databricks notebook source
# MAGIC %md
# MAGIC # 🚨 Setup Completo para Monitoramento Avançado
# MAGIC 
# MAGIC Este notebook executa toda a cadeia necessária para monitoramento:
# MAGIC 1. Ingestão Bronze
# MAGIC 2. Transformação Silver  
# MAGIC 3. Monitoramento Avançado com Teams

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import *
import seaborn as sns
from datetime import datetime
import requests
import json

print("✅ Bibliotecas importadas com sucesso!")
print(f"🕒 Timestamp: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔵 Etapa 1: Ingestão Bronze

# COMMAND ----------

print("🔵 ETAPA 1: INGESTÃO BRONZE")
print("=" * 50)

# Carregar dataset Iris
df_iris = sns.load_dataset("iris")
df_spark = spark.createDataFrame(df_iris)

# Adicionar metadados
df_bronze = df_spark \
    .withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_source", F.lit("seaborn")) \
    .withColumn("_batch_id", F.lit(datetime.now().strftime("%Y%m%d_%H%M%S")))

# Salvar na camada Bronze
bronze_table = "hive_metastore.default.iris_bronze"
df_bronze.write.mode("overwrite").saveAsTable(bronze_table)

print(f"✅ Dados Bronze salvos: {bronze_table}")
print(f"📊 Registros: {df_bronze.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥈 Etapa 2: Transformação Silver

# COMMAND ----------

print("🥈 ETAPA 2: TRANSFORMAÇÃO SILVER")
print("=" * 50)

# Carregar dados Bronze
df_bronze_read = spark.table(bronze_table)

# Transformações de limpeza
df_silver = df_bronze_read \
    .filter(F.col("sepal_length").isNotNull()) \
    .filter(F.col("sepal_width").isNotNull()) \
    .filter(F.col("petal_length").isNotNull()) \
    .filter(F.col("petal_width").isNotNull()) \
    .filter(F.col("species").isNotNull()) \
    .withColumn("species_clean", F.trim(F.col("species"))) \
    .withColumn("_silver_timestamp", F.current_timestamp()) \
    .drop("species") \
    .withColumnRenamed("species_clean", "species")

# Salvar na camada Silver
silver_table = "hive_metastore.default.iris_silver"
df_silver.write.mode("overwrite").saveAsTable(silver_table)

print(f"✅ Dados Silver salvos: {silver_table}")
print(f"📊 Registros: {df_silver.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚨 Etapa 3: Monitoramento Avançado

# COMMAND ----------

print("🚨 ETAPA 3: MONITORAMENTO AVANÇADO")
print("=" * 50)

# Configurações
WEBHOOK_SCOPE = "teams"
WEBHOOK_KEY = "webhook_url"

# COMMAND ----------

def get_teams_webhook():
    """
    Obtém webhook do Teams dos secrets
    """
    try:
        webhook_url = dbutils.secrets.get(scope=WEBHOOK_SCOPE, key=WEBHOOK_KEY)
        return webhook_url
    except Exception as e:
        print(f"⚠️ Webhook não configurado: {str(e)}")
        print("💡 Configure com: make setup-teams")
        return None

def send_teams_notification(webhook_url, title, message, color="warning"):
    """
    Envia notificação para Microsoft Teams
    """
    if not webhook_url:
        print("❌ Webhook não disponível")
        return False
        
    try:
        # Cores para diferentes tipos de alerta
        colors = {
            "success": "good",
            "warning": "warning", 
            "error": "attention"
        }
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": colors.get(color, "warning"),
            "title": f"🚨 {title}",
            "text": message,
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Ver Detalhes no Databricks",
                    "targets": [
                        {
                            "os": "default",
                            "uri": "https://dbc-aecddb3a-6d52.cloud.databricks.com"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Notificação enviada com sucesso!")
            return True
        else:
            print(f"❌ Erro ao enviar notificação: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar notificação: {str(e)}")
        return False

# COMMAND ----------

# Obter webhook
webhook_url = get_teams_webhook()

# Carregar dados para monitoramento
current_data = spark.table(silver_table)
record_count = current_data.count()

print(f"📊 Dados atuais: {record_count} registros")

# COMMAND ----------

# Análise básica de qualidade
quality_metrics = {}

# Verificar valores nulos
null_counts = current_data.select([
    F.sum(F.col(c).isNull().cast("int")).alias(f"null_{c}") 
    for c in current_data.columns if c not in ["_ingestion_timestamp", "_source", "_batch_id", "_silver_timestamp"]
]).collect()[0].asDict()

total_nulls = sum(null_counts.values())
quality_metrics["total_null_values"] = total_nulls

# Estatísticas das features numéricas
numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
for col in numeric_cols:
    stats = current_data.select(
        F.mean(col).alias("mean"),
        F.stddev(col).alias("std"),
        F.min(col).alias("min"),
        F.max(col).alias("max")
    ).collect()[0]
    
    quality_metrics[f"{col}_mean"] = float(stats["mean"] or 0)
    quality_metrics[f"{col}_std"] = float(stats["std"] or 0)

# Distribuição de classes
species_dist = current_data.groupBy("species").count().collect()
class_counts = {row["species"]: row["count"] for row in species_dist}
quality_metrics["class_distribution"] = class_counts

print("📈 Métricas de qualidade calculadas:")
for key, value in quality_metrics.items():
    if key != "class_distribution":
        print(f"   {key}: {value}")

print(f"📊 Distribuição de classes: {quality_metrics['class_distribution']}")

# COMMAND ----------

# Verificar se há problemas para alertar
alerts = []

# Alerta por valores nulos
if total_nulls > 0:
    alerts.append(f"⚠️ Encontrados {total_nulls} valores nulos nos dados")

# Alerta por contagem baixa
if record_count < 100:
    alerts.append(f"⚠️ Contagem baixa de registros: {record_count}")

# Alerta por desequilíbrio de classes
class_counts_values = list(class_counts.values())
if max(class_counts_values) / min(class_counts_values) > 2:
    alerts.append(f"⚠️ Desequilíbrio nas classes detectado")

# Verificar outliers
for col in numeric_cols:
    mean_val = quality_metrics[f"{col}_mean"]
    std_val = quality_metrics[f"{col}_std"]
    
    if std_val > mean_val * 0.5:  # Desvio padrão muito alto
        alerts.append(f"⚠️ Alta variabilidade em {col} (std: {std_val:.2f})")

# COMMAND ----------

# Enviar notificação se houver alertas ou status normal
if alerts:
    alert_message = f"""
**🚨 Alertas Detectados no Pipeline Iris**

**📊 Resumo dos Dados:**
- Total de registros: {record_count}
- Valores nulos: {total_nulls}
- Classes: {len(class_counts)} tipos

**⚠️ Alertas:**
{chr(10).join([f"• {alert}" for alert in alerts])}

**📈 Métricas Principais:**
- Sepal Length: {quality_metrics['sepal_length_mean']:.2f} ± {quality_metrics['sepal_length_std']:.2f}
- Sepal Width: {quality_metrics['sepal_width_mean']:.2f} ± {quality_metrics['sepal_width_std']:.2f}
- Petal Length: {quality_metrics['petal_length_mean']:.2f} ± {quality_metrics['petal_length_std']:.2f}
- Petal Width: {quality_metrics['petal_width_mean']:.2f} ± {quality_metrics['petal_width_std']:.2f}

**🕒 Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if webhook_url:
        send_teams_notification(
            webhook_url,
            "Alertas no Pipeline Iris",
            alert_message,
            "warning"
        )
    
    print("🚨 ALERTAS DETECTADOS:")
    for alert in alerts:
        print(f"   {alert}")
        
else:
    success_message = f"""
**✅ Pipeline Iris - Status Normal**

**📊 Resumo dos Dados:**
- Total de registros: {record_count}
- Valores nulos: {total_nulls}
- Classes balanceadas: {len(class_counts)} tipos

**📈 Métricas Principais:**
- Sepal Length: {quality_metrics['sepal_length_mean']:.2f} ± {quality_metrics['sepal_length_std']:.2f}
- Sepal Width: {quality_metrics['sepal_width_mean']:.2f} ± {quality_metrics['sepal_width_std']:.2f}
- Petal Length: {quality_metrics['petal_length_mean']:.2f} ± {quality_metrics['petal_length_std']:.2f}
- Petal Width: {quality_metrics['petal_width_mean']:.2f} ± {quality_metrics['petal_width_std']:.2f}

**🕒 Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if webhook_url:
        send_teams_notification(
            webhook_url,
            "Pipeline Iris - Status OK",
            success_message,
            "success"
        )
    
    print("✅ Nenhum alerta detectado - Pipeline funcionando normalmente")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Resumo Final

# COMMAND ----------

print("🎯 RESUMO DA EXECUÇÃO")
print("=" * 50)
print(f"✅ Bronze: {bronze_table} - {df_bronze.count()} registros")
print(f"✅ Silver: {silver_table} - {record_count} registros")
print(f"📊 Alertas detectados: {len(alerts)}")
print(f"🔗 Teams webhook: {'Configurado' if webhook_url else 'Não configurado'}")
print(f"🕒 Finalizado em: {datetime.now()}")

if webhook_url:
    print("📱 Notificação enviada para Microsoft Teams")
else:
    print("💡 Para configurar Teams: make setup-teams")

print("\n🚀 Monitoramento avançado concluído com sucesso!")
