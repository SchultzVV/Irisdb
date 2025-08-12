# Databricks notebook source
# MAGIC %md
# MAGIC # 📊 Model Monitoring with Email Notifications
# MAGIC 
# MAGIC Este notebook monitora o modelo em produção e envia notificações por email:
# MAGIC - ✅ **Sucesso**: Modelo funcionando corretamente
# MAGIC - ❌ **Erro**: Problemas detectados no modelo
# MAGIC 
# MAGIC ### 📧 Configuração de Email
# MAGIC - Email configurado via variável de ambiente `EMAIL_TO_REPORT`
# MAGIC - Utiliza SMTP do Gmail (pode ser configurado para outros provedores)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Configurações e Importações

# COMMAND ----------

import os
import smtplib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mlflow
from mlflow import MlflowClient
import json
import random
from pyspark.sql import SparkSession

# Configurações
spark = SparkSession.builder.appName("ModelMonitoring").getOrCreate()
EMAIL_TO_REPORT = os.getenv("EMAIL_TO_REPORT", "xultezz@gmail.com")
MODEL_NAME = "iris_classifier"
MONITORING_THRESHOLD = 0.85  # Acurácia mínima aceitável

print(f"📧 Email configurado para: {EMAIL_TO_REPORT}")
print(f"🤖 Monitorando modelo: {MODEL_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📧 Função de Envio de Email

# COMMAND ----------

def send_email(subject, body, to_email, is_html=True, attachment_data=None):
    """
    Envia email de notificação sobre o status do modelo
    """
    try:
        # Configurações SMTP (usando Gmail como exemplo)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Para produção, usar credenciais seguras
        # Aqui simulamos o envio (em produção configurar App Password do Gmail)
        from_email = "iris.mlops@company.com"
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Adicionar corpo do email
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Adicionar anexo se fornecido
        if attachment_data:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(attachment_data)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename=model_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            msg.attach(attachment)
        
        # SIMULAÇÃO: Em produção, descomentar as linhas abaixo
        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(from_email, app_password)
        # server.send_message(msg)
        # server.quit()
        
        print(f"✅ Email simulado enviado para: {to_email}")
        print(f"📧 Assunto: {subject}")
        print(f"📝 Preview do corpo:\n{body[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Verificação do Modelo MLflow

# COMMAND ----------

def check_model_health():
    """
    Verifica a saúde do modelo registrado no MLflow
    """
    try:
        client = MlflowClient()
        
        # Buscar modelo registrado
        model_versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        
        if not model_versions:
            raise Exception(f"Modelo '{MODEL_NAME}' não encontrado no MLflow")
        
        # Pegar a versão em produção
        production_version = None
        for version in model_versions:
            if version.current_stage == "Production":
                production_version = version
                break
        
        if not production_version:
            raise Exception(f"Nenhuma versão do modelo '{MODEL_NAME}' em produção")
        
        model_info = {
            "name": MODEL_NAME,
            "version": production_version.version,
            "stage": production_version.current_stage,
            "creation_timestamp": production_version.creation_timestamp,
            "last_updated": production_version.last_updated_timestamp,
            "run_id": production_version.run_id
        }
        
        print(f"✅ Modelo encontrado: {MODEL_NAME} v{production_version.version}")
        return model_info, None
        
    except Exception as e:
        error_msg = f"❌ Erro ao verificar modelo: {e}"
        print(error_msg)
        return None, str(e)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Simulação de Métricas de Performance

# COMMAND ----------

def simulate_model_performance():
    """
    Simula métricas de performance do modelo
    """
    # Simular cenário baseado em timestamp (para demonstração)
    current_hour = datetime.now().hour
    
    # Simular degradação em determinados horários (para demonstrar erro)
    if current_hour >= 22 or current_hour <= 6:  # Horário noturno - simular problema
        accuracy = random.uniform(0.70, 0.82)  # Abaixo do threshold
        precision = random.uniform(0.68, 0.80)
        recall = random.uniform(0.65, 0.78)
        f1_score = random.uniform(0.67, 0.79)
        
        # Simular dados de drift
        data_drift_detected = True
        drift_score = random.uniform(0.15, 0.25)  # Alto drift
        
    else:  # Horário normal - modelo saudável
        accuracy = random.uniform(0.88, 0.95)  # Acima do threshold
        precision = random.uniform(0.87, 0.94)
        recall = random.uniform(0.86, 0.93)
        f1_score = random.uniform(0.87, 0.94)
        
        # Dados normais
        data_drift_detected = False
        drift_score = random.uniform(0.02, 0.08)  # Baixo drift
    
    # Métricas simuladas
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "data_drift_detected": data_drift_detected,
        "drift_score": round(drift_score, 4),
        "threshold_met": accuracy >= MONITORING_THRESHOLD,
        "predictions_last_24h": random.randint(1000, 5000),
        "avg_response_time_ms": random.randint(50, 200)
    }
    
    return metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Verificação dos Dados de Entrada

# COMMAND ----------

def check_data_quality():
    """
    Verifica a qualidade dos dados de entrada recentes
    """
    try:
        # Verificar se tabela Silver existe e tem dados recentes
        df = spark.sql("""
            SELECT 
                COUNT(*) as total_records,
                MAX(timestamp) as last_update
            FROM workspace.default.iris_silver 
            WHERE timestamp >= current_timestamp() - INTERVAL 1 DAY
        """)
        
        result = df.collect()[0]
        
        data_quality = {
            "table_accessible": True,
            "recent_records": result["total_records"],
            "last_update": result["last_update"].isoformat() if result["last_update"] else None,
            "data_freshness_ok": result["total_records"] > 0
        }
        
        return data_quality, None
        
    except Exception as e:
        error_msg = f"Erro ao verificar qualidade dos dados: {e}"
        data_quality = {
            "table_accessible": False,
            "recent_records": 0,
            "last_update": None,
            "data_freshness_ok": False,
            "error": error_msg
        }
        return data_quality, error_msg

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 Execução do Monitoramento Principal

# COMMAND ----------

def run_monitoring():
    """
    Execução principal do monitoramento
    """
    print("🔍 Iniciando monitoramento do modelo...")
    print("=" * 50)
    
    # 1. Verificar modelo MLflow
    model_info, model_error = check_model_health()
    
    # 2. Verificar qualidade dos dados
    data_quality, data_error = check_data_quality()
    
    # 3. Simular métricas de performance
    performance_metrics = simulate_model_performance()
    
    # 4. Criar relatório completo
    monitoring_report = {
        "monitoring_timestamp": datetime.now().isoformat(),
        "model_info": model_info,
        "data_quality": data_quality,
        "performance_metrics": performance_metrics,
        "errors": {
            "model_error": model_error,
            "data_error": data_error
        }
    }
    
    # 5. Determinar status geral
    has_errors = bool(model_error or data_error or not performance_metrics["threshold_met"])
    
    return monitoring_report, has_errors

# Executar monitoramento
report, has_errors = run_monitoring()

# Mostrar resumo
print("\n📊 RESUMO DO MONITORAMENTO")
print("=" * 50)
print(f"Timestamp: {report['monitoring_timestamp']}")
print(f"Modelo: {report['model_info']['name'] if report['model_info'] else 'ERRO'}")
print(f"Acurácia: {report['performance_metrics']['accuracy']:.4f}")
print(f"Threshold atingido: {'✅' if report['performance_metrics']['threshold_met'] else '❌'}")
print(f"Drift detectado: {'⚠️ SIM' if report['performance_metrics']['data_drift_detected'] else '✅ NÃO'}")
print(f"Status geral: {'❌ PROBLEMAS DETECTADOS' if has_errors else '✅ TUDO OK'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📧 Envio de Notificações

# COMMAND ----------

# Preparar templates de email
def create_success_email(report):
    """Cria email de sucesso"""
    metrics = report['performance_metrics']
    model = report['model_info']
    
    subject = f"✅ Model Monitoring OK - {MODEL_NAME}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #28a745;">✅ Modelo em Produção Funcionando Corretamente</h2>
        
        <h3>📊 Resumo do Monitoramento</h3>
        <ul>
            <li><strong>Modelo:</strong> {model['name']} v{model['version']}</li>
            <li><strong>Timestamp:</strong> {report['monitoring_timestamp']}</li>
            <li><strong>Status:</strong> <span style="color: #28a745;">SAUDÁVEL</span></li>
        </ul>
        
        <h3>📈 Métricas de Performance</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 8px;">Métrica</th>
                <th style="padding: 8px;">Valor</th>
                <th style="padding: 8px;">Status</th>
            </tr>
            <tr>
                <td style="padding: 8px;">Acurácia</td>
                <td style="padding: 8px;">{metrics['accuracy']:.4f}</td>
                <td style="padding: 8px; color: #28a745;">✅ OK</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Precisão</td>
                <td style="padding: 8px;">{metrics['precision']:.4f}</td>
                <td style="padding: 8px; color: #28a745;">✅ OK</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Recall</td>
                <td style="padding: 8px;">{metrics['recall']:.4f}</td>
                <td style="padding: 8px; color: #28a745;">✅ OK</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Data Drift</td>
                <td style="padding: 8px;">{metrics['drift_score']:.4f}</td>
                <td style="padding: 8px; color: #28a745;">✅ Baixo</td>
            </tr>
        </table>
        
        <h3>📊 Estatísticas de Uso</h3>
        <ul>
            <li><strong>Predições (últimas 24h):</strong> {metrics['predictions_last_24h']:,}</li>
            <li><strong>Tempo médio de resposta:</strong> {metrics['avg_response_time_ms']}ms</li>
        </ul>
        
        <hr>
        <p style="color: #6c757d; font-size: 12px;">
            Este é um relatório automático do sistema de monitoramento MLOps.<br>
            Próxima verificação programada para: {(datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """
    
    return subject, body

def create_error_email(report):
    """Cria email de erro"""
    metrics = report['performance_metrics']
    errors = report['errors']
    
    subject = f"🚨 Model Monitoring ALERT - {MODEL_NAME}"
    
    # Determinar problemas específicos
    problems = []
    if metrics['accuracy'] < MONITORING_THRESHOLD:
        problems.append(f"Acurácia baixa: {metrics['accuracy']:.4f} < {MONITORING_THRESHOLD}")
    if metrics['data_drift_detected']:
        problems.append(f"Data drift detectado: {metrics['drift_score']:.4f}")
    if errors['model_error']:
        problems.append(f"Erro no modelo: {errors['model_error']}")
    if errors['data_error']:
        problems.append(f"Erro nos dados: {errors['data_error']}")
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #dc3545;">🚨 ALERTA: Problemas Detectados no Modelo</h2>
        
        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px;">
            <strong>⚠️ AÇÃO NECESSÁRIA:</strong> O modelo em produção apresenta problemas que requerem atenção imediata.
        </div>
        
        <h3>🔍 Problemas Identificados</h3>
        <ul style="color: #dc3545;">
    """
    
    for problem in problems:
        body += f"            <li><strong>{problem}</strong></li>\n"
    
    body += f"""
        </ul>
        
        <h3>📊 Métricas Atuais</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 8px;">Métrica</th>
                <th style="padding: 8px;">Valor</th>
                <th style="padding: 8px;">Threshold</th>
                <th style="padding: 8px;">Status</th>
            </tr>
            <tr>
                <td style="padding: 8px;">Acurácia</td>
                <td style="padding: 8px;">{metrics['accuracy']:.4f}</td>
                <td style="padding: 8px;">{MONITORING_THRESHOLD}</td>
                <td style="padding: 8px; color: {'#dc3545' if metrics['accuracy'] < MONITORING_THRESHOLD else '#28a745'};">
                    {'❌ BAIXA' if metrics['accuracy'] < MONITORING_THRESHOLD else '✅ OK'}
                </td>
            </tr>
            <tr>
                <td style="padding: 8px;">Data Drift</td>
                <td style="padding: 8px;">{metrics['drift_score']:.4f}</td>
                <td style="padding: 8px;">< 0.10</td>
                <td style="padding: 8px; color: {'#dc3545' if metrics['data_drift_detected'] else '#28a745'};">
                    {'❌ ALTO' if metrics['data_drift_detected'] else '✅ BAIXO'}
                </td>
            </tr>
        </table>
        
        <h3>🔧 Ações Recomendadas</h3>
        <ol>
            <li><strong>Verificar dados de entrada:</strong> Confirmar qualidade dos dados recentes</li>
            <li><strong>Analisar drift:</strong> Investigar mudanças no padrão dos dados</li>
            <li><strong>Retreinar modelo:</strong> Considerar retreinamento com dados atualizados</li>
            <li><strong>Rollback:</strong> Se necessário, reverter para versão anterior estável</li>
        </ol>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px; margin-top: 20px;">
            <strong>📧 Para suporte:</strong> Responda este email ou entre em contato com a equipe MLOps
        </div>
        
        <hr>
        <p style="color: #6c757d; font-size: 12px;">
            Alerta gerado em: {report['monitoring_timestamp']}<br>
            Sistema: Iris MLOps Pipeline<br>
            Próxima verificação: {(datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')} (verificação mais frequente devido ao erro)
        </p>
    </body>
    </html>
    """
    
    return subject, body

# Determinar tipo de email e enviar
if has_errors:
    subject, body = create_error_email(report)
    print("\n🚨 Problemas detectados - enviando alerta...")
else:
    subject, body = create_success_email(report)
    print("\n✅ Modelo saudável - enviando confirmação...")

# Enviar email
email_sent = send_email(
    subject=subject,
    body=body,
    to_email=EMAIL_TO_REPORT,
    is_html=True,
    attachment_data=json.dumps(report, indent=2).encode()
)

if email_sent:
    print(f"📧 Notificação enviada com sucesso para: {EMAIL_TO_REPORT}")
else:
    print("❌ Falha ao enviar notificação")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📝 Log Final do Monitoramento

# COMMAND ----------

print("\n" + "="*60)
print("📊 RELATÓRIO FINAL DE MONITORAMENTO")
print("="*60)
print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🤖 Modelo: {MODEL_NAME}")
print(f"📧 Email enviado para: {EMAIL_TO_REPORT}")
print(f"📊 Status: {'❌ ALERTA' if has_errors else '✅ OK'}")

if has_errors:
    print(f"⚠️ Problemas detectados:")
    if report['errors']['model_error']:
        print(f"   - Modelo: {report['errors']['model_error']}")
    if report['errors']['data_error']:
        print(f"   - Dados: {report['errors']['data_error']}")
    if not report['performance_metrics']['threshold_met']:
        print(f"   - Performance: Acurácia {report['performance_metrics']['accuracy']:.4f} < {MONITORING_THRESHOLD}")
else:
    print(f"✅ Todas as verificações passaram:")
    print(f"   - Modelo: Funcionando normalmente")
    print(f"   - Acurácia: {report['performance_metrics']['accuracy']:.4f}")
    print(f"   - Data drift: {report['performance_metrics']['drift_score']:.4f}")

print("="*60)
print("🎯 Monitoramento concluído com sucesso!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Salvar Relatório para Auditoria

# COMMAND ----------

# Salvar relatório em tabela para histórico
try:
    # Criar DataFrame com o relatório
    report_df = spark.createDataFrame([{
        "timestamp": report['monitoring_timestamp'],
        "model_name": MODEL_NAME,
        "model_version": report['model_info']['version'] if report['model_info'] else None,
        "accuracy": report['performance_metrics']['accuracy'],
        "precision": report['performance_metrics']['precision'],
        "recall": report['performance_metrics']['recall'],
        "f1_score": report['performance_metrics']['f1_score'],
        "data_drift_score": report['performance_metrics']['drift_score'],
        "data_drift_detected": report['performance_metrics']['data_drift_detected'],
        "threshold_met": report['performance_metrics']['threshold_met'],
        "has_errors": has_errors,
        "email_sent": email_sent,
        "email_recipient": EMAIL_TO_REPORT,
        "predictions_24h": report['performance_metrics']['predictions_last_24h'],
        "avg_response_time_ms": report['performance_metrics']['avg_response_time_ms'],
        "report_json": json.dumps(report)
    }])
    
    # Salvar na tabela de monitoramento
    report_df.write \
        .mode("append") \
        .option("mergeSchema", "true") \
        .saveAsTable("workspace.default.model_monitoring_history")
    
    print("💾 Relatório salvo no histórico de monitoramento")
    
except Exception as e:
    print(f"⚠️ Erro ao salvar relatório: {e}")

print("\n🎉 Monitoramento completo finalizado!")
