# 📋 Apresentação: Iris MLOps Pipeline - Databricks Asset Bundles

## 🎯 Slide 1: Título e Objetivos

### 🌸 Iris MLOps Pipeline com Databricks Asset Bundles

**Demonstração Completa de Pipeline MLOps**
- ✅ Arquitetura Medallion (Bronze → Silver → Gold)
- ✅ Unity Catalog para Governança de Dados
- ✅ MLflow para Tracking de Modelos
- ✅ Workflow Automatizado com Dependências
- ✅ Infrastructure as Code (IaC)

---

## 🏗️ Slide 2: Arquitetura do Sistema

### Componentes Principais:

```
📊 Raw Data (Seaborn Iris) 
    ↓
🔵 Bronze Layer (default.iris_bronze)
    ↓ [Data Validation]
🥈 Silver Layer (default.iris_silver)
    ↓ [Business Logic]
🥇 Gold Layer (default.iris_gold)
    ↓ [ML Training]
🤖 MLflow Model Registry
```

**Tecnologias:**
- Databricks Asset Bundles
- Unity Catalog
- Serverless Compute
- MLflow
- Delta Lake

---

## 📁 Slide 3: Estrutura do Projeto

### Organização de Arquivos:

```
iris_bundle/
├── 📄 databricks.yml          # Bundle configuration
├── 🔧 Makefile               # Automation commands
├── notebooks/                # Data processing
│   ├── 01_ingest_bronze.py   # Raw data ingestion
│   ├── 02_transform_silver.py # Data cleaning
│   ├── 03_aggregate_gold.py  # Business aggregations
│   └── 04_train_model.py     # ML model training
└── resources/jobs/           # Job definitions
    ├── bronze_job.yml
    ├── silver_job.yml
    ├── gold_job.yml
    ├── training_job.yml
    └── iris_workflow.yml     # Complete workflow
```

---

## 🔵 Slide 4: Bronze Layer - Raw Data Ingestion

### Características:
- **Fonte**: Dataset Iris do seaborn (150 registros)
- **Formato**: Dados brutos preservados
- **Localização**: `default.iris_bronze`

### Código Principal:
```python
# 01_ingest_bronze.py
import seaborn as sns
df = sns.load_dataset('iris')
spark_df = spark.createDataFrame(df)
spark_df.write.mode("overwrite").saveAsTable(output_table)
```

### Comando de Execução:
```bash
make run_bronze
```

---

## 🥈 Slide 5: Silver Layer - Data Cleaning & Validation

### Transformações Aplicadas:
- ✅ Remoção de valores nulos
- ✅ Validação de schema
- ✅ Filtros de qualidade (valores > 0)
- ✅ Padronização de tipos

### Código Principal:
```python
# 02_transform_silver.py
df = spark.table(input_bronze_table)
df_clean = (df.dropna()
             .filter(col("sepal_length") > 0)
             .filter(col("sepal_width") > 0))
df_clean.write.mode("overwrite").saveAsTable(output_silver_table)
```

---

## 🥇 Slide 6: Gold Layer - Business Aggregations

### Métricas Calculadas:
- 📊 Estatísticas por espécie (mean, std, count)
- 📈 Features engineered (ratios, areas)
- 🔢 Agregações de negócio

### Código Principal:
```python
# 03_aggregate_gold.py
stats_by_species = df.groupBy("species").agg(
    avg("sepal_length").alias("avg_sepal_length"),
    avg("sepal_width").alias("avg_sepal_width"),
    count("*").alias("count")
)
```

---

## 🤖 Slide 7: ML Training - Model Development

### Características do Modelo:
- **Algoritmo**: Random Forest Classifier
- **Features**: 4 características físicas da íris
- **Target**: 3 espécies (setosa, versicolor, virginica)
- **Tracking**: MLflow integration completo

### Código Principal:
```python
# 04_train_model.py
rf = RandomForestClassifier(n_estimators=100)
rf.fit(X_train, y_train)
mlflow.sklearn.log_model(rf, "random_forest_model")
mlflow.log_metrics({"accuracy": accuracy, "precision": precision})
```

---

## ⚙️ Slide 8: Workflow com Dependências

### iris_workflow.yml:
```yaml
name: iris_complete_workflow
tasks:
  - task_key: bronze_ingestion
    
  - task_key: silver_transform
    depends_on: [bronze_ingestion]
    
  - task_key: gold_aggregate
    depends_on: [silver_transform]
    
  - task_key: model_training
    depends_on: [gold_aggregate]
```

### Execução:
```bash
make run_workflow  # Pipeline completo automático
```

---

## 🔧 Slide 9: Comandos de Automação (Makefile)

### Comandos Principais:

```bash
# Setup inicial
make install-databricks
make login
make validate
make deploy

# Execução
make run_workflow              # Workflow completo (recomendado)
make run_pipeline_sequence     # Sequencial sem dependências

# Jobs individuais
make run_bronze
make run_silver
make run_gold
make training_job
```

---

## 📊 Slide 10: Unity Catalog & Governança

### Benefícios:
- 🔐 **Controle de Acesso**: Permissões granulares
- 📈 **Data Lineage**: Rastreabilidade completa
- 🏷️ **Schema Evolution**: Versionamento de estruturas
- 🔍 **Data Discovery**: Catálogo centralizado

### Tabelas Criadas:
- `default.iris_bronze` (dados brutos)
- `default.iris_silver` (dados limpos)
- `default.iris_gold` (agregações)

---

## 📈 Slide 11: MLflow Integration

### Funcionalidades:
- 🏷️ **Model Registry**: Versionamento automático
- 📊 **Experiment Tracking**: Métricas e parâmetros
- 📦 **Artifact Storage**: Modelos e outputs
- 🚀 **Model Serving**: Preparado para produção

### Métricas Registradas:
- Accuracy, Precision, Recall, F1-Score
- Feature Importance
- Confusion Matrix
- Training Parameters

---

## 🧪 Slide 12: Testes e Qualidade

### Validações Implementadas:
- ✅ **Schema Validation**: Estrutura de dados
- ✅ **Data Quality**: Completeness, consistency
- ✅ **Business Rules**: Regras de negócio
- ✅ **Unit Tests**: Testes automatizados

### Arquivos de Teste:
```
tests/
├── test_data_quality.py     # Qualidade de dados
├── test_iris_reader.py      # Testes unitários
└── mock_db.py              # Mock para testes
```

---

## 🚀 Slide 13: Demo ao Vivo

### Passos da Demonstração:

1. **Verificar Status Inicial**
   ```bash
   make validate
   ```

2. **Deploy do Pipeline**
   ```bash
   make deploy
   ```

3. **Executar Workflow Completo**
   ```bash
   make run_workflow
   ```

4. **Verificar Resultados no Databricks UI**
   - Jobs executados
   - Tabelas criadas no Unity Catalog
   - Modelo registrado no MLflow

---

## 📊 Slide 14: Resultados Esperados

### Métricas de Sucesso:
- ✅ **4 Jobs executados** em sequência com dependências
- ✅ **3 Tabelas criadas** no Unity Catalog
- ✅ **1 Modelo treinado** e registrado no MLflow
- ✅ **100% de Accuracy** no dataset Iris (esperado)

### Evidências:
- Logs de execução sem erros
- Tabelas populadas com dados corretos
- Modelo versionado no MLflow Registry
- Lineage completo no Unity Catalog

---

## 🔮 Slide 15: Próximos Passos e Extensões

### Melhorias Futuras:

**🔄 CI/CD Integration**
- GitHub Actions para deployment automático
- Testes automatizados em PRs

**📊 Advanced Monitoring**
- Data drift detection
- Model performance monitoring
- Alertas automáticos

**🚀 Production Features**
- Multi-environment (dev/staging/prod)
- Real-time inference endpoints
- Feature Store integration

**🧠 Advanced ML**
- AutoML capabilities
- A/B testing framework
- Hyperparameter optimization

---

## 💡 Slide 16: Pontos-Chave e Takeaways

### Benefícios Demonstrados:

**🏗️ Infrastructure as Code**
- Configuração versionada e reproduzível
- Deploy automatizado e consistente

**🔄 Pipeline Automation**
- Dependências automáticas entre jobs
- Execução orquestrada e confiável

**📊 Data Governance**
- Unity Catalog para controle e lineage
- Qualidade de dados garantida

**🤖 MLOps Best Practices**
- Model tracking e versionamento
- Reproducibilidade e auditoria

---

## ❓ Slide 17: Q&A

### Perguntas Frequentes:

**Q: Como adaptar para outros datasets?**
A: Modificar notebooks e ajustar variáveis no databricks.yml

**Q: Como escalar para produção?**
A: Configurar ambientes múltiplos e compute otimizado

**Q: Como adicionar novos steps?**
A: Criar novo notebook + job YAML + atualizar workflow

**Q: Como monitora falhas?**
A: Logs nativos do Databricks + alertas personalizados

---

## 📞 Slide 18: Contato e Recursos

### Recursos Úteis:
- 📖 [Databricks Asset Bundles Docs](https://docs.databricks.com/dev-tools/bundles/)
- 🏛️ [Unity Catalog Guide](https://docs.databricks.com/data-governance/unity-catalog/)
- 🧪 [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- 🏗️ [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

### Código do Projeto:
- 📂 GitHub Repository: `[link-do-repositorio]`
- 📋 README completo com instruções detalhadas
- 🧪 Testes automatizados inclusos

**Obrigado! 🙏**
