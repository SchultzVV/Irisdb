# main.py
import os
from telemetry import Telemetry

# Configure a env antes de subir (ex. no Docker/Compose):
# export WEBHOOK_URL="https://prod-55.westeurope.logic.azure.com:443/workflows/f37..."

telemetry = Telemetry(
    service_name="meu_servico_mlops",
    endpoint="http://localhost:4317",  # seu collector OTel
    webhook_env_var="WEBHOOK_URL",
    send_startup_test=True,            # envia o teste de erro automaticamente
)

telemetry.log_info("Iniciando processamento...")

try:
    with telemetry.start_span("etapa_processamento"):
        # Simulação de operação
        telemetry.record_metric("imagens_processadas", 5, "Quantidade de imagens processadas")
        raise ValueError("Falha simulada no processamento de imagens")
except Exception as e:
    telemetry.log_error("Erro no pipeline de processamento")
    telemetry.send_exception_to_teams(e, context_msg="Processando batch #42")

telemetry.log_info("Execução finalizada.")
