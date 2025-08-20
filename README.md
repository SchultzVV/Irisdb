# 🌸 Iris MLOps Pipeline - Unity Catalog

## 📋 Visão Geral

Pipeline de Machine Learning para classificação do dataset Iris usando **Unity Catalog** como camada de governança de dados e **MLflow** para gerenciamento de modelos. Sistema simplificado e pronto para produção com **Serverless Computing** e **monitoramento ElasticSearch integrado**.

## ⭐ **IMPORTANTE: Configuração de Clusters**

📖 **Consulte o arquivo [`CLUSTER_CONFIG_GUIDE.md`](CLUSTER_CONFIG_GUIDE.md)** para informações detalhadas sobre:
- Como configurar clusters específicos vs Serverless
- Otimizações de performance e custos  
- Configurações para desenvolvimento vs produção
- **Este é o ponto mais importante para customização do projeto!**

## 🏗️ Arquitetura Unity Catalog

```
📊 Dataset Iris (UCI/sklearn)
       ↓
🥉 workspace.default.iris_bronze (Raw data)
       ↓
🥈 workspace.default.iris_silver (Cleaned data)
       ↓     ↓
🥇 iris_gold ← 🤖 MLflow Model Registry
       ↓           ↓
📋 Analytics ← 📊 Model Inference → 🔔 Alerts
```

## 🔄 Pipeline Simplificado

### Jobs Essenciais (5 notebooks)

| Ordem | Job | Descrição | Unity Catalog Table | Compute |
|-------|-----|-----------|-------------------|---------|
| 1️⃣ | **Bronze** | Ingestão dataset Iris | `workspace.default.iris_bronze` | Serverless |
| 2️⃣ | **Silver** | Limpeza e transformação | `workspace.default.iris_silver` | Serverless |
| 3️⃣ | **Gold** | Agregações para analytics | `workspace.default.iris_gold` | Serverless |
| 4️⃣ | **Training** | ML model + MLflow registry | MLflow Model | Serverless |
| 5️⃣ | **Inference** | Model predictions + visualizations | `workspace.default.iris_inference_*` | Serverless |

### Fluxo Sequencial
```
🥉 Bronze → 🥈 Silver → 🥇 Gold → 🤖 Training → � Inference
```

## 🚀 Comandos Principais

### Pipeline Completa
```bash
# Executa toda a pipeline sequencialmente
make run_pipeline
```

### Jobs Individuais
```bash
make run_bronze     # Ingestão
make run_silver     # Transformação
make run_gold       # Agregação  
make run_training   # ML Training
make run_inference  # Model Inference + Visualizations
```

### Deploy e Validação
```bash
make validate       # Validar configuração
make deploy         # Deploy para Databricks
make status         # Status do projeto
make help           # Ver todos os comandos
```

## 📊 Monitoramento e Observabilidade

### ElasticSearch + Kibana Dashboard
- **Logs centralizados**: Todos os pipelines enviam logs para ElasticSearch
- **Dashboard Kibana**: Visualizações em tempo real de execuções, erros e métricas
- **Alertas Teams**: Notificações automáticas para falhas e sucessos
- **Métricas ML**: Tracking de performance dos modelos

### Configuração do Monitoramento
```bash
# 1. Configure as variáveis de ambiente
export ELASTICSEARCH_HOST="your-elasticsearch-host"
export ELASTICSEARCH_PORT="9200"
export TEAMS_WEBHOOK_URL="your-teams-webhook-url"

# 2. Deploy da infraestrutura de monitoramento
./scripts/deploy_monitoring.sh

# 3. Atualize o bundle com configurações de monitoramento
databricks bundle deploy --target dev
```

### Dashboard Kibana
- **URL**: `http://your-kibana-host:5601/app/dashboards#/view/iris-pipeline-overview`
- **Índice**: `iris-pipeline-logs`
- **Visualizações**:
  - Status dos pipelines em tempo real
  - Timeline de execuções
  - Checks de qualidade de dados
  - Métricas de performance dos modelos
  - Logs de erro e alertas

### Teams Notifications
- **Início de pipeline**: Notificação azul com parâmetros
- **Sucesso**: Notificação verde com métricas
- **Falha**: Notificação vermelha com detalhes do erro
- **Data Quality**: Alertas quando validações falham

## 📊 Unity Catalog - Governança de Dados

### Catálogo e Schema
- **Catalog**: `workspace`
- **Schema**: `default`
- **Managed Tables**: Todas as tabelas são gerenciadas pelo Unity Catalog
- **Compute**: Serverless (configuração de cluster disponível no [`CLUSTER_CONFIG_GUIDE.md`](CLUSTER_CONFIG_GUIDE.md))

### Tabelas Criadas
```sql
-- Bronze Layer (Raw data)
workspace.default.iris_bronze
  ├── sepal_length: double
  ├── sepal_width: double  
  ├── petal_length: double
  ├── petal_width: double
  ├── species: string
  ├── ingestion_timestamp: timestamp
  ├── source: string
  └── batch_id: string

-- Silver Layer (Cleaned data)  
workspace.default.iris_silver
  ├── sepal_length: double
  ├── sepal_width: double
  ├── petal_length: double  
  ├── petal_width: double
  ├── species: string
  ├── processed_timestamp: timestamp
  └── quality_score: double

-- Gold Layer (Aggregated data)
workspace.default.iris_gold
  ├── species: string
  ├── avg_sepal_length: double
  ├── avg_sepal_width: double
  ├── avg_petal_length: double
  ├── avg_petal_width: double
  ├── sample_count: long
  └── aggregation_timestamp: timestamp

-- Inference Results (Multiple tables with timestamps)
workspace.default.iris_inference_results_*
  ├── sepal_length_cm: double
  ├── sepal_width_cm: double
  ├── petal_length_cm: double  
  ├── petal_width_cm: double
  ├── predicted_class: string
  ├── confidence: double
  ├── inference_timestamp: timestamp
  ├── model_name: string
  └── model_version: string
```

## 🤖 MLflow Integration

### Model Registry
- **Model Name**: `iris_classifier`
- **Stage**: `Production` (ou fallback para modelo de referência)
- **Algorithm**: RandomForestClassifier
- **Features**: Simplified approach com fallback para quando MLflow não está configurado
- **Metrics**: Accuracy, Classification Report, Feature Importance

### Features Implementadas
- ✅ Model training com RandomForestClassifier
- ✅ Fallback quando MLflow registry não disponível
- ✅ Feature importance tracking
- ✅ Performance monitoring
- ✅ Inference com visualizações completas

## 📁 Estrutura do Projeto

```
├── 📖 CLUSTER_CONFIG_GUIDE.md   # ⭐ CONFIGURAÇÃO DE CLUSTERS (IMPORTANTE!)
├── resources/jobs/              # Job definitions (5 jobs essenciais)
│   ├── bronze_job.yml          # 🥉 Ingestão Unity Catalog
│   ├── silver_job.yml          # 🥈 Transformação  
│   ├── gold_job.yml            # 🥇 Agregação
│   ├── training_job.yml        # 🤖 ML Training + MLflow
│   └── inference_job.yml       # 🔮 Model Inference + Visualizations
├── notebooks/                   # Implementation notebooks (5 essenciais)
│   ├── 01_ingest_bronze.py     # Download Iris + Unity Catalog
│   ├── 02_transform_silver.py  # Data cleaning
│   ├── 03_aggregate_gold.py    # Analytics aggregations
│   ├── 04_train_model.py       # ML training + MLflow
│   └── 05_model_inference.py   # Model inference + comprehensive visualizations
├── databricks.yml              # Bundle configuration + cluster settings
├── Makefile                    # Automation commands
└── .github/workflows/          # CI/CD pipeline
    └── ci-cd-pipeline.yml      # GitHub Actions automation
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```bash
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-token

# Unity Catalog settings (atuais)
catalog_name=workspace
schema_name=default

# Notifications (opcional)
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
make run_pipeline
```

### ⚡ Configuração Avançada de Clusters
Para configurar clusters específicos ao invés de Serverless, consulte:
👉 **[`CLUSTER_CONFIG_GUIDE.md`](CLUSTER_CONFIG_GUIDE.md)** - Guia completo com exemplos

## 🔍 Monitoramento

### Verificar Status
```bash
make status         # Status geral do projeto
make list-jobs      # Lista todos os jobs disponíveis  
make help          # Ver todos os comandos
```

### Recursos Implementados
- ✅ **Inference Job** com visualizações completas
- ✅ **Model fallback** quando MLflow não disponível
- ✅ **Unity Catalog** para todas as tabelas
- ✅ **Serverless Computing** (configurável para clusters específicos)
- ✅ **CI/CD Pipeline** com GitHub Actions

## 🎯 Benefícios

### ✅ Unity Catalog
- **Governança centralizada** de todos os dados
- **Tabelas gerenciadas** com versionamento automático
- **Catalog `workspace`** com schema `default`
- **Lineage tracking** completo

### ✅ Serverless Computing
- **Sem gerenciamento** de clusters
- **Start rápido** dos jobs
- **Escalabilidade automática**
- **Pay-per-use** eficiente

### ✅ MLflow Integration
- **Model registry** com fallback robusto
- **Inference completa** com visualizações
- **Performance tracking** detalhado
- **Feature importance** analysis

### ✅ Configuração Flexível
- **Serverless por padrão** (sem overhead)
- **Clusters específicos** configuráveis via [`CLUSTER_CONFIG_GUIDE.md`](CLUSTER_CONFIG_GUIDE.md)
- **CI/CD automatizado** com GitHub Actions
- **5 jobs essenciais** bem estruturados

### ✅ Produção Ready
- **Databricks Asset Bundles** para deploy
- **Unity Catalog** para governança
- **Comprehensive logging** e monitoramento
- **Pipeline limpo** e documentado

---

## 🚀 Quick Start

```bash
# 1. Deploy
make deploy

# 2. Execute pipeline completa
make run_pipeline

# 3. Monitorar
make status
```

## 📖 Documentação Importante

- 🔧 **[`CLUSTER_CONFIG_GUIDE.md`](CLUSTER_CONFIG_GUIDE.md)** - Configuração de clusters (essencial!)
- 📋 **[`databricks.yml`](databricks.yml)** - Configuração do bundle
- ⚙️ **[`Makefile`](Makefile)** - Comandos de automação

**Pipeline MLOps simplificada e pronta para produção!** 🌟
