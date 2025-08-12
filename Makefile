# =====================================
# 🌸 Iris MLOps Pipeline - Makefile Clean
# =====================================
-include .env
export

# =====================================
# 🛠️ Configuração
# =====================================
DATABRICKS_BIN := databricks
TARGET ?= dev

# =====================================
# 🔧 Setup e Autenticação
# =====================================

# 🛠️ Instala Databricks CLI v0.205+
install-databricks:
	@echo "🚀 Instalando Databricks CLI oficial..."
	@curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
	@echo "✅ Databricks CLI instalada!"
	@databricks version

# 🔐 Teste de autenticação
test-auth:
	@echo "🔐 Testando autenticação..."
	@set -a && . ./.env && set +a && \
	databricks current-user me

# =====================================
# 📦 Deploy e Validação
# =====================================

# ✅ Validar bundle
validate:
	@echo "🔍 Validando bundle..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle validate

# 🚀 Deploy do bundle
deploy:
	@echo "🚀 Fazendo deploy para target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle deploy --target $(TARGET)

# =====================================
# 🎯 Jobs Essenciais
# =====================================

# 🥉 Bronze job (Ingestão)
run_bronze:
	@echo "🥉 Executando Bronze job no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run bronze_job --target $(TARGET)

# 🥈 Silver job (Transformação)
run_silver:
	@echo "🥈 Executando Silver job no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run silver_job --target $(TARGET)

# 🥇 Gold job (Agregação)
run_gold:
	@echo "🥇 Executando Gold job no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run gold_job --target $(TARGET)

# 🤖 Training job (ML)
run_training:
	@echo "🤖 Executando Training job no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run training_job --target $(TARGET)

# 🔮 Inference job
run_inference:
	@echo "🔮 Executando Inference job no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run inference_job --target $(TARGET)

# 🧪 Test runner job
run_tests:
	@echo "🧪 Executando testes no target $(TARGET)..."
	@set -a && . ./.env && set +a && \
	databricks bundle run test_runner_job --target $(TARGET)

# =====================================
# 🚀 Pipeline Workflows
# =====================================

# 🔄 Pipeline sequencial básico
run_pipeline:
	@echo "🚀 Executando pipeline sequencial no target $(TARGET)..."
	@$(MAKE) run_bronze TARGET=$(TARGET)
	@$(MAKE) run_silver TARGET=$(TARGET)
	@$(MAKE) run_gold TARGET=$(TARGET)
	@$(MAKE) run_training TARGET=$(TARGET)
	@$(MAKE) run_inference TARGET=$(TARGET)

# 🤖 CI/CD: Deploy e executar pipeline
ci_deploy_and_run:
	@echo "🤖 CI/CD: Deploy, testes e execução do pipeline..."
	@$(MAKE) validate TARGET=$(TARGET)
	@$(MAKE) deploy TARGET=$(TARGET)
	@$(MAKE) run_tests TARGET=$(TARGET)
	@$(MAKE) run_pipeline TARGET=$(TARGET)

# =====================================
# 🧹 Utilitários
# =====================================

# 📋 Listar jobs disponíveis
list-jobs:
	@echo "📋 Jobs disponíveis:"
	@echo "  🥉 run_bronze    - Ingestão de dados (01_ingest_bronze)"
	@echo "  🥈 run_silver    - Transformação (02_transform_silver)"
	@echo "  🥇 run_gold      - Agregação (03_aggregate_gold)"
	@echo "  🤖 run_training  - Treinamento ML (04_train_model)"
	@echo "  🔮 run_inference - Inferência ML (05_model_inference)"
	@echo "  🚀 run_pipeline  - Pipeline completo sequencial"

# 📊 Status do projeto
status:
	@echo "📊 Status do Projeto Iris MLOps:"
	@echo "  📁 Notebooks: 6 arquivos (5 pipeline + 1 teste)"
	@echo "  ⚙️ Jobs: 6 configurados (5 pipeline + 1 teste)"
	@echo "  🔧 Pipeline: Bronze → Silver → Gold → Training → Inference"
	@echo "  🧪 Testes: Notebook automatizado para validação"
	@echo "  🖥️ Compute: Serverless (configuração de cluster comentada)"
	@echo "  🚀 CI/CD: Deploy automático no push para main"
	@echo "  ✅ Status: Pronto para produção"

# 🆘 Ajuda
help:
	@echo "🌸 Iris MLOps Pipeline - Comandos disponíveis:"
	@echo ""
	@echo "🔧 Setup:"
	@echo "  make install-databricks  - Instalar Databricks CLI"
	@echo "  make test-auth          - Testar autenticação"
	@echo ""
	@echo "📦 Deploy:"
	@echo "  make validate           - Validar bundle"
	@echo "  make deploy             - Deploy do bundle"
	@echo ""
	@echo "🎯 Jobs individuais:"
	@echo "  make run_bronze         - Executar ingestão"
	@echo "  make run_silver         - Executar transformação"
	@echo "  make run_gold           - Executar agregação"
	@echo "  make run_training       - Executar treinamento ML"
	@echo "  make run_inference      - Executar inferência ML"
	@echo "  make run_tests          - Executar testes"
	@echo ""
	@echo "🚀 Pipelines:"
	@echo "  make run_pipeline       - Pipeline completo"
	@echo "  make ci_deploy_and_run  - CI/CD completo"
	@echo ""
	@echo "💡 Exemplos com TARGET:"
	@echo "  make deploy TARGET=prod          - Deploy para produção"
	@echo "  make run_pipeline TARGET=dev     - Pipeline em dev (padrão)"
	@echo "  make ci_deploy_and_run TARGET=prod - CI/CD completo para prod"
	@echo ""
	@echo "🧹 Utilitários:"
	@echo "  make list-jobs          - Listar jobs"
	@echo "  make status             - Status do projeto"
	@echo "  make help               - Esta ajuda"

.PHONY: install-databricks test-auth validate deploy run_bronze run_silver run_gold run_training run_inference run_tests run_pipeline ci_deploy_and_run list-jobs status help
