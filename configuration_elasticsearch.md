# 📊 Configuração ElasticSearch e Kibana para Iris Pipeline

## 🎯 Visão Geral

Este documento detalha como configurar o sistema de monitoramento completo usando **ElasticSearch**, **Kibana** e **Microsoft Teams** para o pipeline Iris MLOps. O sistema captura logs em tempo real, cria dashboards visuais e envia alertas automáticos.

## 🏗️ Arquitetura de Monitoramento

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Databricks    │───▶│   ElasticSearch  │───▶│     Kibana      │
│   Spark Jobs    │    │   (Port 9200)    │    │   (Port 5601)   │
│                 │    │                  │    │                 │
│ • log4j.props   │    │ • Index Template │    │ • Dashboard     │
│ • monitoring.py │    │ • ILM Policy     │    │ • Visualizations│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Microsoft Teams │    │   Log Aggregator │    │   Real-time     │
│   Notifications │    │   & Search       │    │   Monitoring    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Pré-requisitos

### 1. **ElasticSearch e Kibana**

#### Instalação via Docker (Recomendado)
```bash
# 1. Criar network para ElasticSearch e Kibana
docker network create elastic

# 2. Executar ElasticSearch
docker run -d \
  --name elasticsearch \
  --network elastic \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  docker.elastic.co/elasticsearch/elasticsearch:8.8.0

# 3. Executar Kibana
docker run -d \
  --name kibana \
  --network elastic \
  -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  docker.elastic.co/kibana/kibana:8.8.0

# 4. Verificar se estão funcionando
curl http://localhost:9200
curl http://localhost:5601
```

#### Instalação Nativa (Ubuntu/Debian)
```bash
# 1. Adicionar repositório ElasticSearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# 2. Instalar ElasticSearch
sudo apt update
sudo apt install elasticsearch

# 3. Configurar ElasticSearch
sudo nano /etc/elasticsearch/elasticsearch.yml
# Adicionar:
# network.host: 0.0.0.0
# discovery.type: single-node
# xpack.security.enabled: false

# 4. Iniciar ElasticSearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# 5. Instalar Kibana
sudo apt install kibana

# 6. Configurar Kibana
sudo nano /etc/kibana/kibana.yml
# Adicionar:
# server.host: "0.0.0.0"
# elasticsearch.hosts: ["http://localhost:9200"]

# 7. Iniciar Kibana
sudo systemctl enable kibana
sudo systemctl start kibana
```

### 2. **Verificar Conectividade**
```bash
# Testar ElasticSearch
curl -X GET "localhost:9200/_cluster/health?pretty"

# Testar Kibana
curl -X GET "localhost:5601/api/status"
```

## 📁 Arquivos Necessários no Databricks

### 1. **Estrutura de Arquivos no Workspace**

```
/Workspace/Shared/iris_monitoring/
├── log4j.properties                    # Configuração de logging
└── utils/
    └── monitoring.py                   # Utilitários de monitoramento
```

### 2. **log4j.properties** - Configuração de Logging

**Localização**: `/Workspace/Shared/iris_monitoring/log4j.properties`

```properties
# ElasticSearch Log4j Configuration for Databricks
# This file configures Spark to send logs to ElasticSearch

# Root logger configuration
log4j.rootLogger=INFO, console, ELASTIC

# Console appender (for local debugging)
log4j.appender.console=org.apache.log4j.ConsoleAppender
log4j.appender.console.layout=org.apache.log4j.PatternLayout
log4j.appender.console.layout.ConversionPattern=%d{ISO8601} [%t] %-5p %c %x - %m%n

# ElasticSearch Socket Appender
log4j.appender.ELASTIC=org.apache.log4j.net.SocketAppender
log4j.appender.ELASTIC.RemoteHost=${elasticsearch.host}
log4j.appender.ELASTIC.Port=${elasticsearch.port}
log4j.appender.ELASTIC.ReconnectionDelay=10000
log4j.appender.ELASTIC.LocationInfo=true
log4j.appender.ELASTIC.layout=org.apache.log4j.PatternLayout
log4j.appender.ELASTIC.layout.ConversionPattern=%d{ISO8601} [%t] %-5p %c{1} %x - %m%n

# Specific loggers for different components
log4j.logger.org.apache.spark=INFO, ELASTIC
log4j.logger.org.apache.spark.sql=INFO, ELASTIC
log4j.logger.org.apache.spark.scheduler=INFO, ELASTIC
log4j.logger.databricks=INFO, ELASTIC
log4j.logger.mlflow=INFO, ELASTIC

# Iris Pipeline specific logging
log4j.logger.iris.pipeline=INFO, ELASTIC
log4j.logger.iris.monitoring=INFO, ELASTIC

# Pipeline metrics logger
log4j.logger.iris.metrics=INFO, ELASTIC
log4j.additivity.iris.metrics=false
```

### 3. **monitoring.py** - Utilitários de Monitoramento

**Localização**: `/Workspace/Shared/iris_monitoring/utils/monitoring.py`

Este arquivo contém:
- `TeamsNotifier`: Class para envio de notificações Teams
- `PipelineMonitor`: Class principal de monitoramento
- `@monitor_pipeline`: Decorator para instrumentação automática
- Funções de logging para qualidade de dados e métricas ML

## 🔧 Configuração do Asset Bundle

### 1. **databricks.yml** - Variáveis de Monitoramento

```yaml
variables:
  # ElasticSearch Monitoring Configuration
  elasticsearch_host:
    description: "ElasticSearch host for log aggregation"
    default: "localhost"
  
  elasticsearch_port:
    description: "ElasticSearch port for log aggregation"
    default: "9200"
  
  teams_webhook:
    description: "Microsoft Teams webhook URL for notifications"
    default: ""
  
  log4j_path:
    description: "Path to log4j.properties configuration file"
    default: "/Workspace/Shared/iris_monitoring/log4j.properties"
  
  enable_monitoring:
    description: "Enable monitoring and logging infrastructure"
    default: true
```

### 2. **Job Configuration** - Exemplo bronze_job.yml

```yaml
resources:
  jobs:
    bronze_job:
      name: iris_bronze_ingestion
      
      # Configuração Spark com monitoramento (se usando clusters)
      # new_cluster:
      #   spark_conf:
      #     "spark.iris.elasticsearch.host": "${var.elasticsearch_host}"
      #     "spark.iris.elasticsearch.port": "${var.elasticsearch_port}"
      #     "spark.iris.teams.webhook": "${var.teams_webhook}"
      #     "spark.driver.extraJavaOptions": "-Dlog4j.configuration=file:${var.log4j_path}"
      #     "spark.executor.extraJavaOptions": "-Dlog4j.configuration=file:${var.log4j_path}"
      
      tasks:
        - task_key: ingest_bronze
          notebook_task:
            notebook_path: /path/to/notebook
            
      # Notificações
      email_notifications:
        on_failure:
          - "admin@company.com"
      
      # Teams webhooks (quando disponível)
      # webhook_notifications:
      #   on_failure:
      #     - id: "teams_webhook"
      #       url: "${var.teams_webhook}"
```

## 🚀 Processo de Deploy Completo

### 1. **Configurar Variáveis de Ambiente**

```bash
# Configurar hosts ElasticSearch e Kibana
export ELASTICSEARCH_HOST="localhost"    # ou IP do servidor
export ELASTICSEARCH_PORT="9200"
export KIBANA_HOST="localhost"           # ou IP do servidor
export KIBANA_PORT="5601"

# Teams webhook (quando disponível)
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."
```

### 2. **Executar Script de Deploy do Monitoramento**

```bash
# Executar o script automatizado
./scripts/deploy_monitoring.sh
```

O script realiza:
- ✅ Testa conectividade ElasticSearch/Kibana
- ✅ Cria index template no ElasticSearch
- ✅ Configura ILM (Index Lifecycle Management) policy
- ✅ Cria índice inicial `iris-pipeline-logs`
- ✅ Importa dashboard Kibana
- ✅ Tenta upload de arquivos para Databricks

### 3. **Criar Diretórios Manualmente (se necessário)**

Se o script falhar no upload, execute manualmente:

```bash
# Criar estrutura de diretórios no Databricks Workspace
databricks workspace mkdirs /Workspace/Shared/iris_monitoring/utils/

# Verificar se foi criado
databricks workspace list /Workspace/Shared/iris_monitoring/
```

### 4. **Upload Manual de Arquivos**

```bash
# Upload log4j.properties
databricks workspace import \
  --file config/log4j.properties \
  /Workspace/Shared/iris_monitoring/log4j.properties \
  --format RAW --overwrite

# Upload monitoring.py
databricks workspace import \
  --file utils/monitoring.py \
  /Workspace/Shared/iris_monitoring/utils/monitoring.py \
  --language PYTHON --format SOURCE --overwrite

# Verificar uploads
databricks workspace list /Workspace/Shared/iris_monitoring/
databricks workspace list /Workspace/Shared/iris_monitoring/utils/
```

### 5. **Deploy do Asset Bundle**

```bash
# Deploy com configurações de monitoramento
databricks bundle deploy --target dev

# Verificar se jobs foram criados
databricks jobs list
```

### 6. **Testar o Sistema**

```bash
# Executar um job para gerar logs
databricks jobs run-now <job-id>

# Verificar logs no ElasticSearch
curl -X GET "localhost:9200/iris-pipeline-logs/_search?pretty"

# Acessar dashboard Kibana
open http://localhost:5601/app/dashboards#/view/iris-pipeline-overview
```

## 🔗 Conexões e Endpoints

### 1. **ElasticSearch Endpoints**

```bash
# Health check
GET http://localhost:9200/_cluster/health

# Índices criados
GET http://localhost:9200/_cat/indices/iris-pipeline-*

# Buscar logs
GET http://localhost:9200/iris-pipeline-logs/_search
{
  "query": {
    "match": {
      "pipeline_name": "bronze_ingestion"
    }
  }
}

# Estatísticas do índice
GET http://localhost:9200/iris-pipeline-logs/_stats
```

### 2. **Kibana Endpoints**

```bash
# Status da aplicação
GET http://localhost:5601/api/status

# Dashboard Iris Pipeline
http://localhost:5601/app/dashboards#/view/iris-pipeline-overview

# Discover (exploração de logs)
http://localhost:5601/app/discover

# Visualizations
http://localhost:5601/app/visualize
```

### 3. **Databricks Workspace**

```bash
# Listar arquivos de monitoramento
databricks workspace list /Workspace/Shared/iris_monitoring/

# Ver conteúdo do log4j
databricks workspace export /Workspace/Shared/iris_monitoring/log4j.properties

# Ver código de monitoramento
databricks workspace export /Workspace/Shared/iris_monitoring/utils/monitoring.py
```

## 📊 Dashboard Kibana

### Visualizações Disponíveis

1. **Pipeline Status Overview**
   - Contadores de sucesso/falha
   - Status atual dos pipelines

2. **Data Quality Checks**
   - Histórico de validações
   - Alertas de qualidade

3. **Pipeline Execution Timeline**
   - Timeline de execuções
   - Duração dos jobs

4. **Model Performance Metrics**
   - Métricas ML ao longo do tempo
   - Comparação de modelos

5. **Error Logs and Alerts**
   - Logs de erro recentes
   - Classificação por severidade

### Acesso ao Dashboard

```
URL: http://localhost:5601/app/dashboards#/view/iris-pipeline-overview
Index Pattern: iris-pipeline-*
Time Field: @timestamp
```

## 🔔 Notificações Teams (Opcional)

### 1. **Configurar Webhook Teams**

1. No Microsoft Teams, vá ao canal desejado
2. Clique em "..." → "Connectors" → "Incoming Webhook"
3. Configure nome e imagem
4. Copie a URL do webhook

### 2. **Ativar no Asset Bundle**

```yaml
variables:
  teams_webhook:
    default: "https://outlook.office.com/webhook/sua-url-aqui"
```

### 3. **Descomentar Notificações nos Jobs**

```yaml
webhook_notifications:
  on_failure:
    - id: "teams_webhook"
      url: "${var.teams_webhook}"
  on_success:
    - id: "teams_success"
      url: "${var.teams_webhook}"
```

## 🧪 Testando o Sistema

### 1. **Teste de Conectividade**

```bash
# Testar ElasticSearch
curl -f http://localhost:9200/_cluster/health || echo "❌ ElasticSearch não acessível"

# Testar Kibana
curl -f http://localhost:5601/api/status || echo "❌ Kibana não acessível"
```

### 2. **Teste de Logs**

```bash
# Executar job bronze
databricks jobs run-now <bronze-job-id>

# Verificar logs no ElasticSearch
curl -X GET "localhost:9200/iris-pipeline-logs/_search?q=pipeline_name:bronze_ingestion&pretty"
```

### 3. **Teste de Dashboard**

1. Acesse: `http://localhost:5601`
2. Vá para "Dashboards"
3. Abra "Iris MLOps Pipeline Monitoring"
4. Verifique se dados aparecem após execução dos jobs

## ❗ Troubleshooting

### Problemas Comuns

1. **DBFS Root Bloqueado**
   ```
   Error: Public DBFS root is disabled
   ```
   **Solução**: Usar Workspace Files (`/Workspace/Shared/`) ao invés de DBFS

2. **ElasticSearch Inacessível**
   ```
   curl: (7) Failed to connect to localhost port 9200
   ```
   **Solução**: Verificar se ElasticSearch está rodando e na porta correta

3. **Sintaxe Terraform Inválida**
   ```
   Error: Invalid character in interpolation
   ```
   **Solução**: Usar sintaxe correta do Databricks Asset Bundle (não Terraform HCL)

4. **Arquivos Não Encontrados no Databricks**
   ```
   ImportError: No module named 'monitoring'
   ```
   **Solução**: Verificar se arquivos foram uploadados corretamente no Workspace

### Comandos de Verificação

```bash
# Verificar estrutura no Databricks
databricks workspace list /Workspace/Shared/iris_monitoring/ -l

# Verificar jobs criados
databricks jobs list --output json | jq '.jobs[] | {id: .job_id, name: .settings.name}'

# Verificar índices ElasticSearch
curl -X GET "localhost:9200/_cat/indices/iris-*?v"

# Verificar logs recentes
curl -X GET "localhost:9200/iris-pipeline-logs/_search?size=10&sort=@timestamp:desc&pretty"
```

## 🎯 Próximos Passos

1. **Execute um pipeline completo** para gerar dados de monitoramento
2. **Explore o dashboard Kibana** para entender as métricas
3. **Configure alertas Teams** quando tiver o webhook
4. **Customize visualizações** conforme necessidades específicas
5. **Configure retention policies** para gerenciar espaço em disco

O sistema está agora **100% configurado e pronto para monitoramento em produção**! 🎉
