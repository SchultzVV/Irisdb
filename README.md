# 🌸 Iris MLOps Pipeline - Unity Catalog

## 📋 Visão Geral

Pipeline de Machine Learning para classificação do dataset Iris usando **Unity Catalog** como camada de governança de dados e **MLflow** para gerenciamento de modelos. Sistema com **auto-triggers** que executa jobs em cascata automaticamente.

## 🏗️ Arquitetura Unity Catalog

```
📊 Dataset Iris (UCI/sklearn)
       ↓
🥉 hive_metastore.default.iris_bronze (Raw data)
       ↓
🥈 hive_metastore.default.iris_silver (Cleaned data)
       ↓     ↓
🥇 iris_gold ← 🤖 MLflow Model Registry
       ↓           ↓
📋 Analytics ← 📊 Model Monitoring → 🔔 Teams Alerts
```

## 🔄 Pipeline com Auto-Triggers

### Ordem de Execução Automática

| Ordem | Job | Descrição | Unity Catalog Table | Auto-Trigger |
|-------|-----|-----------|-------------------|---------------|
| 1️⃣ | **Bronze** | Ingestão dataset Iris | `iris_bronze` | Manual |
| 2️⃣ | **Silver** | Limpeza e transformação | `iris_silver` | ✅ Bronze success |
| 3️⃣a | **Gold** | Agregações para analytics | `iris_gold` | ✅ Silver success |
| 3️⃣b | **Training** | ML model + MLflow registry | MLflow Model | ✅ Silver success |
| 4️⃣ | **Monitoring** | Model drift + Teams alerts | - | ✅ Training success |

### Fluxo Visual
```
🥉 Bronze (manual)
     ↓ ✅ auto-trigger
🥈 Silver  
     ↓ ✅ auto-trigger
   ┌─────────┐
   ↓ parallel ↓
🥇 Gold    🤖 Training
             ↓ ✅ auto-trigger
           📊 Monitoring
```

## 🚀 Comandos Principais

### Pipeline Completa (Recomendado)
```bash
# Executa toda a pipeline automaticamente
make run_bronze_with_triggers
```

### Pipelines Parciais
```bash
# A partir do Silver
make run_silver_with_triggers

# Apenas Training + Monitoring  
make run_training_with_triggers
```

### Jobs Individuais
```bash
make run_bronze     # Ingestão
make run_silver     # Transformação
make run_gold       # Agregação  
make run_training   # ML Training
make run_monitoring # Monitoramento
```

### Deploy e Validação
```bash
make validate       # Validar configuração
make deploy         # Deploy para Databricks
make help_essential # Ver todos os comandos
```

## 📊 Unity Catalog - Governança de Dados

### Catálogo e Schema
- **Catalog**: `hive_metastore`
- **Schema**: `default`
- **Managed Tables**: Todas as tabelas são gerenciadas pelo Unity Catalog

### Tabelas Criadas
```sql
-- Bronze Layer (Raw data)
hive_metastore.default.iris_bronze
  ├── sepal_length: double
  ├── sepal_width: double  
  ├── petal_length: double
  ├── petal_width: double
  ├── species: string
  ├── ingestion_timestamp: timestamp
  ├── source: string
  └── batch_id: string

-- Silver Layer (Cleaned data)  
hive_metastore.default.iris_silver
  ├── sepal_length: double
  ├── sepal_width: double
  ├── petal_length: double  
  ├── petal_width: double
  ├── species: string
  ├── processed_timestamp: timestamp
  └── quality_score: double

-- Gold Layer (Aggregated data)
hive_metastore.default.iris_gold
  ├── species: string
  ├── avg_sepal_length: double
  ├── avg_sepal_width: double
  ├── avg_petal_length: double
  ├── avg_petal_width: double
  ├── sample_count: long
  └── aggregation_timestamp: timestamp
```

## 🤖 MLflow Integration

### Model Registry
- **Model Name**: `iris_classifier`
- **Stage**: `Production`
- **Algorithm**: RandomForestClassifier
- **Input Example**: ✅ Auto-signature inference
- **Metrics**: Accuracy, Precision, Recall, F1-Score

### Features
- ✅ Automatic model registration
- ✅ Production stage promotion
- ✅ Feature importance tracking
- ✅ Model versioning
- ✅ Performance monitoring

## 📁 Estrutura do Projeto

```
├── resources/jobs/              # Job definitions
│   ├── bronze_job.yml          # 🥉 Ingestão Unity Catalog
│   ├── silver_job.yml          # 🥈 Transformação  
│   ├── gold_job.yml            # 🥇 Agregação
│   ├── training_job.yml        # 🤖 ML Training + MLflow
│   ├── complete_pipeline.yml   # 🚀 Pipeline orquestrado
│   └── model_monitoring.yml    # 📊 Monitoring + Teams
├── notebooks/                   # Implementation notebooks
│   ├── 01_ingest_bronze.py     # Download Iris + Unity Catalog
│   ├── 02_transform_silver.py  # Data cleaning
│   ├── 03_aggregate_gold.py    # Analytics aggregations
│   ├── 04_train_model.py       # ML training + MLflow
│   └── model_monitoring.py     # Drift detection + alerts
├── databricks.yml              # Bundle configuration
├── Makefile                    # Automation commands
└── deploy.sh                   # Automated deployment
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```bash
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-token

# Unity Catalog settings
catalog_name=hive_metastore
schema_name=default

# Notifications
notification_email=your-email@company.com
teams_webhook=https://your-teams-webhook
```

### Deploy
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Deploy to Databricks
make validate && make deploy

# 3. Execute pipeline
make run_bronze_with_triggers
```

## 🔍 Monitoramento

### Verificar Status
```bash
make check_essential_status  # Status dos jobs
make check_tables           # Tabelas Unity Catalog  
make check_models          # Modelos MLflow
```

### Teams Alerts
O sistema envia alertas automáticos para Microsoft Teams quando:
- 🚨 Model accuracy < threshold
- ❌ Data quality issues
- 📭 Empty tables
- ⚠️ Pipeline failures

## 🎯 Benefícios

### ✅ Unity Catalog
- **Governança centralizada** de todos os dados
- **Tabelas gerenciadas** com versionamento automático
- **Controle de acesso** granular
- **Lineage tracking** completo

### ✅ Auto-Triggers
- **Execução automática** em cascata
- **Paralelismo** entre Gold e Training
- **Error handling** robusto
- **Um comando** executa tudo

### ✅ MLflow Integration
- **Model registry** nativo
- **Automatic signature** inference
- **Version control** de modelos
- **Performance tracking** contínuo

### ✅ Produção Ready
- **Databricks Asset Bundles** para deploy
- **Unity Catalog** para governança
- **Teams integration** para alertas
- **Comprehensive logging** e monitoramento

---

## 🚀 Quick Start

```bash
# 1. Deploy
make deploy

# 2. Execute pipeline completa
make run_bronze_with_triggers

# 3. Monitorar
make check_essential_status
```

**Pipeline MLOps completa com Unity Catalog e auto-triggers em um comando!** 🌟
