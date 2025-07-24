# Databricks notebook source
import great_expectations as ge
from great_expectations.checkpoint import Checkpoint

# Simula ingestão
df = spark.read.option("header", True).csv("dbfs:/tmp/mock/iris.csv")
df.write.mode("overwrite").saveAsTable("telecom_lakehouse.ml_assets.mock_bronze")

# Validação
context = ge.get_context(context_root_dir="/Workspace/Repos/<seu-repo>/great_expectations")
results = context.run_checkpoint(checkpoint_name="iris_validation_checkpoint")

assert results["success"], "❌ Validação de schema falhou!"
