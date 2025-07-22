```r
iris_bundle/
├── notebooks/
│   ├── 01_ingest_bronze.py       <- Salva dados crus no Delta Lake
│   ├── 02_transform_silver.py    <- Limpa e padroniza os dados
│   ├── 03_aggregate_gold.py      <- Agrega por espécie (gold)
│   ├── 04_train_model.py         <- Treina modelo com MLflow
│   ├── 05_batch_inference.py     <- Roda batch inference
├── tests/
│   ├── test_data_quality.py      <- Validações nos dados (pytest)
│   └── test_model_accuracy.py    <- Teste de regressão para modelo
├── databricks.yml                <- Definição principal do bundle
├── resources/
│   ├── jobs/
│   │   ├── bronze_job.yml
│   │   ├── silver_job.yml
│   │   ├── gold_job.yml
│   │   └── training_job.yml
│   ├── pipelines/
│   │   └── lakehouse_pipeline.yml
└── .github/workflows/
    └── ci.yml                    <- Workflow GitHub Actions para deploy + validação
```
