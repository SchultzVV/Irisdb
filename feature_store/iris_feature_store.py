# Databricks notebook source
# MAGIC %md
# MAGIC # 🏪 Iris Feature Store
# MAGIC 
# MAGIC Este notebook implementa um Feature Store centralizado para o dataset Iris,
# MAGIC criando features engineered que podem ser reutilizadas em múltiplos modelos.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Instalação de Dependências

# COMMAND ----------

# MAGIC %pip install databricks-feature-store
# MAGIC dbutils.library.restartPython()

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
# MAGIC ## 📊 Carregamento de Dados Base

# COMMAND ----------

# Carregar dataset Iris
df_iris = sns.load_dataset("iris")
df_spark = spark.createDataFrame(df_iris)

# Adicionar ID único para cada registro
df_with_id = df_spark.withColumn("iris_id", F.monotonically_increasing_id())

# Mostrar dados base
print("📊 Primeiros 10 registros do dataset:")
df_with_id.limit(10).show()
print(f"Total de registros: {df_with_id.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Feature Engineering

# COMMAND ----------

def create_iris_features(df):
    """
    Cria features engineered para o dataset Iris
    """
    
    # Features básicas de relação
    df_features = df.withColumn(
        "sepal_ratio", F.col("sepal_length") / F.col("sepal_width")
    ).withColumn(
        "petal_ratio", F.col("petal_length") / F.col("petal_width")
    ).withColumn(
        "sepal_area", F.col("sepal_length") * F.col("sepal_width")
    ).withColumn(
        "petal_area", F.col("petal_length") * F.col("petal_width")
    )
    
    # Features de tamanho total
    df_features = df_features.withColumn(
        "total_length", F.col("sepal_length") + F.col("petal_length")
    ).withColumn(
        "total_width", F.col("sepal_width") + F.col("petal_width")
    ).withColumn(
        "total_area", F.col("sepal_area") + F.col("petal_area")
    )
    
    # Features de diferença
    df_features = df_features.withColumn(
        "length_diff", F.col("sepal_length") - F.col("petal_length")
    ).withColumn(
        "width_diff", F.col("sepal_width") - F.col("petal_width")
    )
    
    # Features categóricas baseadas em percentis
    df_features = df_features.withColumn(
        "size_category",
        F.when(F.col("total_area") > 15, "large")
         .when(F.col("total_area") > 8, "medium")
         .otherwise("small")
    )
    
    # Features de distância euclidiana do centro
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
df_features = create_iris_features(df_with_id)

# Mostrar features criadas
print("📊 Features criadas - primeiros 10 registros:")
df_features.limit(10).show()
print(f"Número de features: {len(df_features.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## �️ Criação do Feature Store

# COMMAND ----------

# Configuração da Feature Table
feature_table_name = "hive_metastore.default.iris_features"
print(f"🏪 Criando Feature Store: {feature_table_name}")

try:
    # Salvar como tabela gerenciada no Unity Catalog
    df_feature_table.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(feature_table_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Validação da Feature Table

# COMMAND ----------

# Ler features da tabela usando SQL
print(f"📊 Feature Table Statistics:")

# Contar registros
count_query = f"SELECT COUNT(*) as total_records FROM {feature_table_name}"
total_records = spark.sql(count_query).collect()[0]['total_records']
print(f"  - Total records: {total_records}")

# Contar colunas 
columns_query = f"DESCRIBE {feature_table_name}"
columns_info = spark.sql(columns_query).collect()
print(f"  - Total features: {len(columns_info)}")

# Distribuição por espécie
print(f"  - Species distribution:")
species_query = f"SELECT species, COUNT(*) as count FROM {feature_table_name} GROUP BY species ORDER BY count DESC"
species_dist = spark.sql(species_query).collect()
for row in species_dist:
    print(f"    {row['species']}: {row['count']} registros")

# Estatísticas básicas das features numéricas
print(f"\n📈 Feature Statistics (primeiras features):")
sample_query = f"SELECT sepal_ratio, petal_ratio, total_area FROM {feature_table_name} LIMIT 5"
sample_data = spark.sql(sample_query).collect()
for i, row in enumerate(sample_data, 1):
    print(f"  Sample {i}: sepal_ratio={row['sepal_ratio']:.3f}, petal_ratio={row['petal_ratio']:.3f}, total_area={row['total_area']:.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Feature Importance Analysis

# COMMAND ----------

# Converter para Pandas para análise de correlação
pandas_df = features_df.select(*numeric_features + ["species"]).toPandas()

# Calcular correlações
correlations = pandas_df.corr()
print("🔗 Feature Correlations with Target (Species):")

# Criar mapeamento numérico para espécies
species_mapping = {"setosa": 0, "versicolor": 1, "virginica": 2}
pandas_df["species_numeric"] = pandas_df["species"].map(species_mapping)

# Correlações com target
target_correlations = pandas_df.corr()["species_numeric"].sort_values(ascending=False)
print(target_correlations[:-1])  # Excluir auto-correlação

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 Feature Selection

# COMMAND ----------

# Selecionar top features baseado em correlação
top_features = target_correlations.abs().sort_values(ascending=False).head(8).index.tolist()
top_features.remove("species_numeric")  # Remover target

print(f"🎯 Top Features selecionadas:")
for i, feature in enumerate(top_features, 1):
    corr_value = target_correlations[feature]
    print(f"  {i}. {feature}: {corr_value:.3f}")

# Criar tabela de features selecionadas
selected_features_df = features_df.select(["iris_id", "species"] + top_features + ["feature_timestamp"])

# Salvar features selecionadas
# Tabela para features selecionadas
selected_table_name = "hive_metastore.default.iris_features_selected"
selected_features_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(selected_table_name)

print(f"\n✅ Selected features saved to: {selected_table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📝 Feature Store Metadata

# COMMAND ----------

# Criar metadata da feature store
feature_metadata = {
    "feature_table_name": feature_table_name,
    "selected_features_table": selected_table_name,
    "total_features": len(features_df.columns),
    "selected_features_count": len(top_features),
    "top_features": top_features,
    "creation_timestamp": df_features.select("feature_timestamp").first()["feature_timestamp"],
    "feature_engineering_version": "v1.0",
    "description": "Iris feature store with engineered features for species classification"
}

# Registrar metadata no MLflow
with mlflow.start_run(run_name="iris_feature_store_creation") as run:
    mlflow.log_params(feature_metadata)
    mlflow.log_metric("total_records", features_df.count())
    mlflow.log_metric("feature_count", len(features_df.columns))
    mlflow.log_metric("selected_features_count", len(top_features))
    
    # Log correlations como artifact
    correlation_df = pd.DataFrame(target_correlations).reset_index()
    correlation_df.columns = ["feature", "correlation"]
    correlation_df.to_csv("/tmp/feature_correlations.csv", index=False)
    mlflow.log_artifact("/tmp/feature_correlations.csv")

print("✅ Feature Store metadata registrada no MLflow")
print(f"📊 Run ID: {run.info.run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Validações de Qualidade

# COMMAND ----------

# Validações de qualidade das features
print("🧪 Executando validações de qualidade da Feature Store...")

# 1. Verificar valores nulos
null_counts = features_df.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in numeric_features]).collect()[0]
print(f"\n1️⃣ Valores nulos por feature:")
for feature, null_count in zip(numeric_features, null_counts):
    print(f"  {feature}: {null_count}")
    assert null_count == 0, f"Feature {feature} tem valores nulos!"

# 2. Verificar ranges válidos
print(f"\n2️⃣ Validação de ranges:")
for feature in numeric_features:
    min_val = features_df.select(F.min(feature)).collect()[0][0]
    max_val = features_df.select(F.max(feature)).collect()[0][0]
    print(f"  {feature}: [{min_val:.3f}, {max_val:.3f}]")
    
    # Validações específicas
    if "ratio" in feature:
        assert min_val > 0, f"Ratio {feature} deve ser positivo!"
    if "area" in feature:
        assert min_val >= 0, f"Área {feature} deve ser não-negativa!"

# 3. Verificar distribuição por espécie
species_counts = features_df.groupBy("species").count().collect()
print(f"\n3️⃣ Distribuição por espécie:")
for row in species_counts:
    print(f"  {row['species']}: {row['count']} registros")
    assert row['count'] == 50, f"Espécie {row['species']} deveria ter 50 registros!"

print("\n✅ Todas as validações de qualidade passaram!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Feature Store Summary

# COMMAND ----------

print("🏪 IRIS FEATURE STORE - SUMMARY")
print("=" * 50)
print(f"📊 Total Features Created: {len(features_df.columns)}")
print(f"🎯 Selected Features: {len(top_features)}")
print(f"📦 Total Records: {features_df.count()}")
print(f"🏷️ Classes: {features_df.select('species').distinct().count()}")
print(f"📅 Created: {feature_metadata['creation_timestamp']}")
print(f"🔗 Feature Table: {feature_table_name}")
print(f"⭐ Selected Table: {selected_table_name}")
print("\n🎯 Top Features by Correlation:")
for i, feature in enumerate(top_features[:5], 1):
    corr_value = target_correlations[feature]
    print(f"  {i}. {feature}: {corr_value:.3f}")

print("\n✅ Feature Store criado com sucesso!")
print("📝 Próximos passos:")
print("  1. Use as features no modelo AutoML")
print("  2. Configure monitoring de drift")
print("  3. Atualize features conforme necessário")
