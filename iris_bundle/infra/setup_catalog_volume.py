# Databricks notebook source
# MAGIC %md
# MAGIC ## 📦 Criação de Catálogo, Schema e Volume no Unity Catalog
# MAGIC Este notebook garante que todos os recursos de armazenamento estejam prontos para uso pelo pipeline.

# MAGIC %sql
CREATE CATALOG IF NOT EXISTS telecom_lakehouse;

-- Alternativamente, você pode verificar se o catálogo está ativo:
-- SHOW CATALOGS;

# COMMAND ----------

# MAGIC %sql
USE CATALOG telecom_lakehouse;

# COMMAND ----------

# MAGIC %sql
CREATE SCHEMA IF NOT EXISTS ml_assets;

# COMMAND ----------

# MAGIC %sql
CREATE VOLUME IF NOT EXISTS telecom_lakehouse.ml_assets.iris_volume;
