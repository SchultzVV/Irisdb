# Databricks notebook source
# MAGIC %md
# MAGIC # 🏪 Iris Feature Store Simples
# MAGIC 
# MAGIC Este notebook implementa um Feature Store simplificado para o dataset Iris.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import *
import mlflow
import seaborn as sns
from datetime import datetime

print("✅ Bibliotecas importadas com sucesso!")
print(f"🕒 Timestamp: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Carregamento de Dados da Camada Silver

# COMMAND ----------

# Carregar dados da tabela Silver do Unity Catalog
silver_table = "hive_metastore.default.iris_silver"
print(f"📊 Carregando dados da tabela Silver: {silver_table}")

try:
    df_silver = spark.table(silver_table)
    print("✅ Tabela Silver carregada com sucesso!")
    
    # Verificar esquema e dados
    print("📋 Schema da tabela Silver:")
    df_silver.printSchema()
    
    # Adicionar ID único para cada registro (para feature store)
    df_with_id = df_silver.withColumn("iris_id", F.monotonically_increasing_id())
    
    # Mostrar dados base
    print("📊 Dados Silver carregados:")
    df_with_id.show(5)
    print(f"📦 Total de registros: {df_with_id.count()}")
    
except Exception as e:
    print(f"❌ Erro ao carregar tabela Silver: {str(e)}")
    print("🔄 Usando dados do seaborn como fallback...")
    
    # Fallback para dados do seaborn
    df_iris = sns.load_dataset("iris")
    df_spark = spark.createDataFrame(df_iris)
    df_with_id = df_spark.withColumn("iris_id", F.monotonically_increasing_id())
    
    print("📊 Dataset Iris (fallback) carregado:")
    df_with_id.show(5)
    print(f"📦 Total de registros: {df_with_id.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🛠️ Feature Engineering

# COMMAND ----------

def create_features(df):
    """
    Cria features engineered para o dataset Iris
    """
    print("🛠️ Criando features engineered...")
    
    # Features básicas
    df_features = df.withColumn(
        "sepal_area", F.col("sepal_length") * F.col("sepal_width")
    ).withColumn(
        "petal_area", F.col("petal_length") * F.col("petal_width")
    ).withColumn(
        "total_area", F.col("sepal_area") + F.col("petal_area")
    )
    
    # Features de proporção
    df_features = df_features.withColumn(
        "sepal_ratio", F.col("sepal_length") / F.col("sepal_width")
    ).withColumn(
        "petal_ratio", F.col("petal_length") / F.col("petal_width")
    ).withColumn(
        "area_ratio", F.col("sepal_area") / F.col("petal_area")
    )
    
    # Features de distância euclidiana
    df_features = df_features.withColumn(
        "distance_from_origin",
        F.sqrt(
            F.pow(F.col("sepal_length"), 2) + 
            F.pow(F.col("sepal_width"), 2) + 
            F.pow(F.col("petal_length"), 2) + 
            F.pow(F.col("petal_width"), 2)
        )
    )
    
    # Timestamp para versionamento
    df_features = df_features.withColumn(
        "feature_timestamp", F.current_timestamp()
    )
    
    return df_features

# Aplicar feature engineering
df_feature_table = create_features(df_with_id)

print("🎯 Features criadas:")
df_feature_table.printSchema()
print(f"📊 Total de colunas: {len(df_feature_table.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Salvar Feature Store

# COMMAND ----------

# Criar tabela temporária primeiro para testar
temp_table_name = "iris_features_temp"
df_feature_table.createOrReplaceTempView(temp_table_name)

print(f"✅ Tabela temporária criada: {temp_table_name}")

# Testar consulta
result = spark.sql(f"SELECT COUNT(*) as count FROM {temp_table_name}")
record_count = result.collect()[0]['count']
print(f"📊 Registros na tabela temporária: {record_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🗃️ Salvar como Tabela Delta

# COMMAND ----------

# Tentar salvar usando formato Delta simples
try:
    # Usar apenas o schema default sem especificar catálogo
    simple_table_name = "iris_features"
    
    print(f"💾 Salvando como tabela Delta: {simple_table_name}")
    
    df_feature_table.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(simple_table_name)
    
    print(f"✅ Tabela Delta criada: {simple_table_name}")
    
    # Validar criação
    validation_df = spark.table(simple_table_name)
    print(f"🔍 Validação - Registros: {validation_df.count()}")
    
except Exception as e:
    print(f"❌ Erro ao criar tabela Delta: {str(e)}")
    
    # Fallback para tabela temporária
    print("🔄 Usando tabela temporária como fallback")
    temp_table_name = "iris_features_temp"
    df_feature_table.createOrReplaceTempView(temp_table_name)
    print(f"✅ Tabela temporária criada: {temp_table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Análise das Features

# COMMAND ----------

# Análise estatística das features numéricas
print("📊 Análise Estatística das Features:")

numeric_features = [
    "sepal_length", "sepal_width", "petal_length", "petal_width",
    "sepal_area", "petal_area", "total_area", 
    "sepal_ratio", "petal_ratio", "area_ratio", "distance_from_origin"
]

for feature in numeric_features:
    stats = df_feature_table.select(
        F.mean(feature).alias("mean"),
        F.stddev(feature).alias("std"),
        F.min(feature).alias("min"),
        F.max(feature).alias("max")
    ).collect()[0]
    
    print(f"📊 {feature}:")
    print(f"   Mean: {stats['mean']:.3f}, Std: {stats['std']:.3f}")
    print(f"   Min: {stats['min']:.3f}, Max: {stats['max']:.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏷️ Análise por Espécie

# COMMAND ----------

# Estatísticas por espécie
print("🏷️ Análise por Espécie:")

species_stats = df_feature_table.groupBy("species").agg(
    F.count("*").alias("count"),
    F.mean("total_area").alias("avg_total_area"),
    F.mean("distance_from_origin").alias("avg_distance"),
    F.mean("sepal_ratio").alias("avg_sepal_ratio"),
    F.mean("petal_ratio").alias("avg_petal_ratio")
).collect()

for row in species_stats:
    print(f"🌸 {row['species']}:")
    print(f"   Count: {row['count']}")
    print(f"   Avg Total Area: {row['avg_total_area']:.3f}")
    print(f"   Avg Distance: {row['avg_distance']:.3f}")
    print(f"   Avg Sepal Ratio: {row['avg_sepal_ratio']:.3f}")
    print(f"   Avg Petal Ratio: {row['avg_petal_ratio']:.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Resumo do Feature Store

# COMMAND ----------

print("🎯 RESUMO DO FEATURE STORE")
print("=" * 50)
print(f"📊 Total Features Created: {len(df_feature_table.columns)}")
print(f"📦 Total Records: {df_feature_table.count()}")
print(f"🏷️ Classes: {df_feature_table.select('species').distinct().count()}")

# Listar todas as features
feature_list = df_feature_table.columns
print(f"\n📝 Features Disponíveis ({len(feature_list)}):")
for i, feature in enumerate(feature_list, 1):
    print(f"   {i:2d}. {feature}")

print("\n✅ Feature Store criado com sucesso!")
print("🚀 Pronto para uso em modelos de ML!")
