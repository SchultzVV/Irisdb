# =====================================
# 🌐 Variáveis de ambiente
# =====================================
-include .env
export

# =====================================
# 🧪 Comandos principais
# =====================================

# Caminho padrão onde a CLI será instalada
DATABRICKS_CLI_DIR := $(HOME)/.databricks/bin
DATABRICKS_BIN := databricks
OS := $(shell uname -s | tr A-Z a-z)

# 🛠️ Instala Databricks CLI v0.205+ com curl
install-databricks:
	@echo "🚀 Instalando Databricks CLI oficial (v0.205+)..."
# 	@which databricks >/dev/null 2>&1 && databricks version && echo "✅ Já instalada!" && exit 0
	@curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
	@echo "✅ Databricks CLI instalada com sucesso!"
	@echo "🔍 Verificando versão..."
	@which databricks && databricks version



# ✅ Alvo de login com verificação de autenticação usando variáveis do .env
login:
	@echo "🔐 Carregando credenciais do .env..."
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && \
		databricks workspace list /; \
	else \
		echo "❌ Arquivo .env não encontrado!"; \
		exit 1; \
	fi

# 🔐 Teste simples de autenticação sem validação do bundle
test-auth:
	@echo "🔐 Testando autenticação..."
	@set -a && . ./.env && set +a && \
	cd /tmp && databricks current-user me

# Alvo para validar, fazer deploy e rodar pipeline
validate:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle validate

deploy:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle deploy --target dev

run:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run iris_pipeline --target dev

test-pipeline:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run test_pipeline --target dev

run_bronze:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run bronze_job --target dev

run_silver:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run silver_job --target dev

run_gold:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run gold_job --target dev 

training_job:
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run training_job --target dev

# 🧪 Validação de qualidade de dados com Great Expectations
run_data_quality:
	@echo "🧪 Executando validação de qualidade de dados..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run data_quality_job --target dev

# 🏪 Feature Store - Criação e atualização
run_feature_store:
	@echo "🏪 Criando/atualizando Feature Store..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run feature_store_job --target dev

# 🤖 AutoML - Seleção automática de modelos
run_automl:
	@echo "🤖 Executando AutoML para seleção de modelos..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run automl_job --target dev

# 📊 Model Monitoring - Drift detection
run_monitoring:
	@echo "📊 Executando monitoramento de modelo..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run model_monitoring_job --target dev

# 🚀 MLOps Pipeline Completo
run_mlops_full:
	@echo "🚀 Executando pipeline MLOps completo..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run mlops_full_pipeline --target dev

# 🔄 Workflow completo com dependências (Bronze → Silver → Gold → Training)
run_workflow:
	@echo "🚀 Executando workflow completo: Bronze → Silver → Gold → Training..."
	@set -a && . ./.env && set +a && \
	$(DATABRICKS_BIN) bundle run iris_workflow --target dev

# 🔗 Execução sequencial dos jobs individuais
run_pipeline_sequence:
	@echo "🔗 Executando pipeline em sequência..."
	@echo "1️⃣ Executando Bronze Job..."
	@$(MAKE) run_bronze
	@echo "2️⃣ Executando Silver Job..."
	@$(MAKE) run_silver
	@echo "3️⃣ Executando Gold Job..."
	@$(MAKE) run_gold
	@echo "4️⃣ Executando Training Job..."
	@$(MAKE) training_job
	@echo "✅ Pipeline completo executado com sucesso!"


list_tables:
	@set -a && . ./.env && set +a && \
	databricks workspace list /Workspace/Users/xultezz@gmail.com/.bundle/iris_bundle/dev/files/notebooks

list_jobs:
	@echo "📋 Listando todos os jobs do bundle..."
	@set -a && . ./.env && set +a && \
	databricks jobs list


schedule_enable:
	@echo "✅ Habilitando agendamento do workflow..."
	@set -a && . ./.env && set +a && \
	JOB_ID=$$(databricks jobs list --output json | jq -r '.jobs[] | select(.settings.name=="iris_complete_workflow") | .job_id'); \
	if [ "$$JOB_ID" != "" ] && [ "$$JOB_ID" != "null" ]; then \
		databricks jobs reset --job-id $$JOB_ID --json-file resources/jobs/iris_workflow.yml; \
		echo "✅ Agendamento habilitado para job ID: $$JOB_ID"; \
	else \
		echo "❌ Job 'iris_complete_workflow' não encontrado"; \
	fi

schedule_disable:
	@echo "⏸️ Desabilitando agendamento do workflow..."
	@set -a && . ./.env && set +a && \
	JOB_ID=$$(databricks jobs list --output json | jq -r '.jobs[] | select(.settings.name=="iris_complete_workflow") | .job_id'); \
	if [ "$$JOB_ID" != "" ] && [ "$$JOB_ID" != "null" ]; then \
		databricks jobs update --job-id $$JOB_ID --json '{"schedule": {"pause_status": "PAUSED"}}'; \
		echo "⏸️ Agendamento desabilitado para job ID: $$JOB_ID"; \
	else \
		echo "❌ Job 'iris_complete_workflow' não encontrado"; \
	fi

check_schedule:
	@echo "🔍 Verificando status do agendamento do job 'iris_complete_workflow'..."
	@set -a && . ./.env && set +a && \
	databricks jobs get 709121597410934

list_runs:
	@echo "📊 Listando execuções recentes do workflow..."
	@set -a && . ./.env && set +a && \
	databricks jobs list-runs --job-id 709121597410934 --limit 10

# =====================================
# 🧹 Limpeza e debug
# =====================================

clean:
	rm -rf __pycache__ dist *.egg-info .pytest_cache .mypy_cache .coverage

# =====================================
# 💡 Ajuda
# =====================================

help:
	@echo "Comandos disponíveis:"
	@echo "  make login               -> Autentica via token"
	@echo "  make validate            -> Valida a estrutura do bundle"
	@echo "  make deploy              -> Sobe código e recursos para o Databricks"
	@echo "  make run-pipeline        -> Executa pipeline principal"
	@echo "  make run-test-pipeline   -> Executa pipeline de teste com dados mock"
	@echo "  make logout              -> Remove autenticação local"
	@echo "  make clean               -> Remove arquivos temporários"

# =====================================
# ⚙️ Instalação do Databricks CLI v2
# =====================================
