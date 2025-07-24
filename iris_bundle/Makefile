# =====================================
# 🌐 Variáveis de ambiente
# =====================================
export $(shell sed 's/=.*//' .env)
include .env
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
