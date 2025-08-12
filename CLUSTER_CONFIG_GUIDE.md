# 🖥️ Guia de Configuração de Clusters

## 📋 Situação Atual
- **Status**: Usando **Serverless Computing** (padrão Databricks)
- **Vantagens**: Sem gerenciamento de cluster, start rápido, escalabilidade automática
- **Custos**: Pay-per-use, ideal para workloads esporádicos

## 🔧 Como Configurar Clusters Específicos

### 1️⃣ **No arquivo `databricks.yml`** (Configuração Global)

```yaml
variables:
  cluster_id:
    description: "ID do cluster específico"
    default: "0123-456789-abcdef"

resources:
  clusters:
    iris_cluster:
      cluster_name: "iris-processing-cluster"
      spark_version: "13.3.x-scala2.12"
      node_type_id: "i3.xlarge"
      num_workers: 2
```

### 2️⃣ **Nos arquivos de Job** (resources/jobs/*.yml)

#### Opção A: Cluster Existente
```yaml
jobs:
  my_job:
    existing_cluster_id: ${var.cluster_id}
```

#### Opção B: Novo Cluster por Job
```yaml
jobs:
  my_job:
    new_cluster:
      cluster_name: "job-specific-cluster"
      spark_version: "13.3.x-scala2.12"
      node_type_id: "i3.xlarge"
      num_workers: 2
```

#### Opção C: Instance Pool (Recomendado para Produção)
```yaml
jobs:
  my_job:
    new_cluster:
      instance_pool_id: "pool-id-here"
      num_workers: 2
```

### 3️⃣ **Level de Task** (Override específico)
```yaml
tasks:
  - task_key: my_task
    existing_cluster_id: "task-specific-cluster"
```

## 🎯 Quando Usar Cada Opção

| Cenário | Recomendação | Motivo |
|---------|-------------|---------|
| **Desenvolvimento** | Serverless | Flexibilidade, sem overhead |
| **Produção Regular** | Cluster Pool | Eficiência de custos |
| **Jobs Críticos** | Cluster Dedicado | Performance garantida |
| **Workloads Grandes** | Auto Scaling Cluster | Escalabilidade |

## 💰 Comparação de Custos

- **Serverless**: $0.20/DBU + compute
- **Job Cluster**: $0.15/DBU + compute  
- **All-Purpose Cluster**: $0.40/DBU + compute
- **Instance Pool**: $0.15/DBU + compute (+ economia de start time)

## 🚀 Para Ativar Clusters no Futuro

1. **Descomente** as seções no `databricks.yml`
2. **Substitua** os IDs de cluster pelos valores reais
3. **Deploy** novamente: `make deploy`
4. **Teste** com um job: `make run_bronze`

## 📊 Monitoramento de Clusters

- **UI Databricks**: `/compute/clusters`
- **Métricas**: CPU, Memory, Network I/O
- **Logs**: Driver logs, Executor logs
- **Spark UI**: Jobs, Stages, Tasks

## ⚡ Dicas de Performance

```yaml
spark_conf:
  "spark.databricks.adaptive.enabled": "true"
  "spark.databricks.adaptive.coalescePartitions.enabled": "true"
  "spark.databricks.adaptive.localShuffleReader.enabled": "true"
  "spark.sql.adaptive.skewJoin.enabled": "true"
```

## 🔐 Tags Recomendadas

```yaml
custom_tags:
  Environment: "dev|prod"
  Project: "iris_pipeline"
  Team: "data_engineering"
  CostCenter: "analytics"
  Owner: "vitor@company.com"
```
