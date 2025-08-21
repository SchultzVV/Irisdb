import numpy as np
import logging
import os

# Threshold para alarme
THRESHOLD = float(os.getenv("ALERT_THRESHOLD", 10.0))

# Configuração de logger para Azure Monitor
logger = logging.getLogger("vector_logger")
logger.setLevel(logging.INFO)

def produto_interno_com_alarme():
    for i in range(4):
        v1 = np.random.rand(10)
        v2 = np.random.rand(10)
        produto = np.dot(v1, v2)

        logger.info(f"Iteração {i+1}: Produto interno = {produto:.4f}")

        if produto > THRESHOLD:
            logger.warning(f"🚨 ALERTA: Produto interno {produto:.4f} excedeu o threshold de {THRESHOLD}")

