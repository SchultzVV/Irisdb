import os

# Define a estrutura do projeto com os arquivos e seus conteúdos
project_structure = {
    "notebooks": {},
    "tests": {
        "test_data_quality.py": '''
import pyspark.sql.functions as F

def test_no_nulls_in_silver(spark):
    df = spark.read.format("delta").load("/mnt/datalake/iris/silver")
    null_count = df.select([F.count(F.when(F.col(c).isNull(), c)) for c in df.columns])
    assert all([row == 0 for row in null_count.collect()[0]])
'''
    },
    "resources/jobs": {},
    "resources/pipelines": {
        "lakehouse_pipeline.yml": '''
resources:
  pipelines:
    iris_pipeline:
      name: iris-lakehouse-pipeline
      target: iris_pipeline_db
      libraries:
        - notebook: notebooks/01_ingest_bronze.py
        - notebook: notebooks/02_transform_silver.py
        - notebook: notebooks/03_aggregate_gold.py
        - notebook: notebooks/04_train_model.py
      configuration:
        source: s3://your-bucket/datalake/iris/
        output_gold_table: iris.gold
        output_model: iris_model
'''
    },
    ".github/workflows": {
        "ci.yml": '''
name: CI Bundle Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Databricks CLI
        run: |
          pip install databricks-cli

      - name: Configure Databricks CLI
        run: databricks auth login --host ${{ secrets.DATABRICKS_HOST }} --token ${{ secrets.DATABRICKS_TOKEN }}

      - name: Validate Bundle
        run: databricks bundle validate

      - name: Deploy Bundle
        run: databricks bundle deploy --target dev

      - name: Run Lakehouse Pipeline
        run: databricks bundle run iris_pipeline --target dev
'''
    },
    "": {
        "databricks.yml": '''
bundle:
  name: iris_bundle
  run_as:
    user_name: "{{env.DATABRICKS_USER}}"

include:
  - notebooks/*
  - resources/jobs/*
  - resources/pipelines/*
  - tests/*

targets:
  dev:
    workspace:
      host: https://your-workspace-url
    mode: development
'''
    }
}

# Função para criar estrutura de pastas e arquivos
def create_structure(base_path="/dbfs/tmp/iris_bundle"):
    for folder, files in project_structure.items():
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file_name, content in files.items():
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as f:
                f.write(content.strip())

# Executa a criação do projeto
if __name__ == "__main__":
    create_structure()
    print("Projeto Databricks Asset Bundle criado com sucesso em ./iris_bundle")
