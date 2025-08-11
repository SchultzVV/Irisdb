# Databricks notebook source
# MAGIC %md
# MAGIC # 🚨 Advanced Model Monitoring with Teams Notifications
# MAGIC 
# MAGIC Este notebook implementa monitoramento avançado de modelo com notificações automáticas
# MAGIC para Microsoft Teams quando há degradação de métricas ou drift detectado.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
from pyspark.sql import functions as F
from pyspark.sql.types import *
import mlflow
import mlflow.sklearn
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from scipy.stats import ks_2samp, chi2_contingency, anderson_ksamp
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import requests
import warnings
warnings.filterwarnings('ignore')

print("✅ Bibliotecas importadas com sucesso!")
print(f"🕒 Timestamp: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Configurações de Notificação

# COMMAND ----------

# Configurações do Microsoft Teams Webhook
# Em produção, estas configurações devem vir de secrets do Databricks
TEAMS_WEBHOOK_URL = dbutils.secrets.get(scope="teams", key="webhook_url") if dbutils.secrets.get(scope="teams", key="webhook_url") else "https://outlook.office.com/webhook/YOUR_WEBHOOK_URL"

# Thresholds para alertas
METRIC_DEGRADATION_THRESHOLD = 0.05  # 5% de degradação
DRIFT_P_VALUE_THRESHOLD = 0.05       # p-value para detectar drift significativo
MIN_SAMPLES_FOR_ANALYSIS = 30        # Mínimo de amostras para análise válida

print("🔧 Configurações carregadas:")
print(f"   📉 Threshold degradação: {METRIC_DEGRADATION_THRESHOLD}")
print(f"   📊 Threshold drift p-value: {DRIFT_P_VALUE_THRESHOLD}")
print(f"   📦 Mínimo amostras: {MIN_SAMPLES_FOR_ANALYSIS}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Carregamento de Dados

# COMMAND ----------

def load_monitoring_data():
    """
    Carrega dados para monitoramento
    """
    print("📥 Carregando dados para monitoramento...")
    
    try:
        # Verificar se a tabela silver existe
        tables = spark.sql("SHOW TABLES IN hive_metastore.default").collect()
        silver_exists = any("iris_silver" in str(row) for row in tables)
        
        if not silver_exists:
            print("⚠️ Tabela Silver não existe. Criando dados de exemplo...")
            # Criar dados de exemplo se a tabela não existir
            import seaborn as sns
            df_iris = sns.load_dataset("iris")
            reference_data = spark.createDataFrame(df_iris)
            
            # Salvar como tabela silver
            reference_data.write.mode("overwrite").saveAsTable("hive_metastore.default.iris_silver")
            print("✅ Tabela Silver criada com dados de exemplo")
        else:
            # Dados de referência (baseline)
            reference_data = spark.table("hive_metastore.default.iris_silver")
            
        print(f"📊 Dados de referência: {reference_data.count()} registros")
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {str(e)}")
        print("🔄 Criando tabela com dados de exemplo...")
        # Fallback para dados de exemplo
        import seaborn as sns
        df_iris = sns.load_dataset("iris")
        reference_data = spark.createDataFrame(df_iris)
        reference_data.write.mode("overwrite").saveAsTable("hive_metastore.default.iris_silver")
        print("✅ Tabela Silver criada como fallback")
    
    # Dados atuais (últimas 24 horas - simulação)
    # Em produção, filtrar por timestamp da última execução
    current_data = spark.table("hive_metastore.default.iris_silver")
    print(f"📊 Dados atuais: {current_data.count()} registros")
    
    # Validar se há dados suficientes
    if current_data.count() < MIN_SAMPLES_FOR_ANALYSIS:
        print(f"⚠️ Poucos dados para análise: {current_data.count()} < {MIN_SAMPLES_FOR_ANALYSIS}")
        return None, None
    
    return reference_data, current_data

reference_df, current_df = load_monitoring_data()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Carregamento do Modelo

# COMMAND ----------

def load_latest_model():
    """
    Carrega o modelo mais recente do MLflow
    """
    try:
        print("🤖 Carregando modelo mais recente...")
        
        # Buscar modelo registrado
        model_name = "iris_model"
        client = mlflow.tracking.MlflowClient()
        
        # Tentar buscar versão em Production primeiro
        try:
            latest_versions = client.get_latest_versions(model_name, stages=["Production"])
            if latest_versions:
                model_version = latest_versions[0]
                print(f"📦 Modelo Production encontrado: v{model_version.version}")
            else:
                # Se não há modelo em Production, buscar a versão mais recente
                latest_versions = client.get_latest_versions(model_name)
                model_version = latest_versions[0]
                print(f"📦 Modelo mais recente: v{model_version.version}")
        except:
            print("⚠️ Nenhum modelo registrado encontrado")
            return None, None
        
        model_uri = f"models:/{model_name}/{model_version.version}"
        model = mlflow.sklearn.load_model(model_uri)
        
        print(f"✅ Modelo carregado: {model_uri}")
        return model, model_version
        
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {str(e)}")
        return None, None

model, model_version = load_latest_model()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Análise de Drift

# COMMAND ----------

def detect_data_drift(reference_df, current_df):
    """
    Detecta drift nos dados usando testes estatísticos
    """
    print("🔍 Detectando drift nos dados...")
    
    drift_results = {
        'has_drift': False,
        'drift_features': [],
        'drift_details': {},
        'overall_drift_score': 0.0
    }
    
    if reference_df is None or current_df is None:
        return drift_results
    
    # Features numéricas para análise
    numeric_features = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
    
    drift_scores = []
    
    for feature in numeric_features:
        try:
            # Converter para Pandas para análise estatística
            ref_values = reference_df.select(feature).toPandas()[feature].values
            curr_values = current_df.select(feature).toPandas()[feature].values
            
            # Teste Kolmogorov-Smirnov
            ks_stat, ks_p_value = ks_2samp(ref_values, curr_values)
            
            # Anderson-Darling test (mais sensível)
            try:
                ad_stat, ad_p_value = anderson_ksamp([ref_values, curr_values])
            except:
                ad_stat, ad_p_value = 0, 1
            
            # Calcular diferenças nas estatísticas descritivas
            ref_mean = np.mean(ref_values)
            curr_mean = np.mean(curr_values)
            mean_diff = abs(ref_mean - curr_mean) / ref_mean if ref_mean != 0 else 0
            
            ref_std = np.std(ref_values)
            curr_std = np.std(curr_values)
            std_diff = abs(ref_std - curr_std) / ref_std if ref_std != 0 else 0
            
            # Determinar se há drift significativo
            has_drift = (ks_p_value < DRIFT_P_VALUE_THRESHOLD or 
                        mean_diff > 0.1 or std_diff > 0.2)
            
            if has_drift:
                drift_results['drift_features'].append(feature)
                drift_results['has_drift'] = True
            
            # Calcular score de drift (0-1, onde 1 é máximo drift)
            drift_score = min(1.0, (1 - ks_p_value) + mean_diff + std_diff)
            drift_scores.append(drift_score)
            
            drift_results['drift_details'][feature] = {
                'ks_statistic': ks_stat,
                'ks_p_value': ks_p_value,
                'ad_statistic': ad_stat,
                'mean_shift': mean_diff,
                'std_shift': std_diff,
                'drift_score': drift_score,
                'has_drift': has_drift,
                'ref_mean': ref_mean,
                'curr_mean': curr_mean,
                'ref_std': ref_std,
                'curr_std': curr_std
            }
            
            print(f"   📊 {feature}:")
            print(f"      KS p-value: {ks_p_value:.4f}")
            print(f"      Mean shift: {mean_diff:.4f}")
            print(f"      Drift: {'🚨 SIM' if has_drift else '✅ NÃO'}")
            
        except Exception as e:
            print(f"   ❌ Erro analisando {feature}: {str(e)}")
    
    # Score geral de drift
    drift_results['overall_drift_score'] = np.mean(drift_scores) if drift_scores else 0.0
    
    print(f"\n📊 Resultado da análise de drift:")
    print(f"   🎯 Score geral: {drift_results['overall_drift_score']:.4f}")
    print(f"   🚨 Drift detectado: {'SIM' if drift_results['has_drift'] else 'NÃO'}")
    print(f"   📋 Features com drift: {drift_results['drift_features']}")
    
    return drift_results

drift_analysis = detect_data_drift(reference_df, current_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 Análise de Performance do Modelo

# COMMAND ----------

def evaluate_model_performance(model, current_df, reference_df):
    """
    Avalia a performance atual do modelo comparando com baseline
    """
    print("🎯 Avaliando performance do modelo...")
    
    performance_results = {
        'current_metrics': {},
        'baseline_metrics': {},
        'metric_degradation': {},
        'has_degradation': False,
        'degraded_metrics': []
    }
    
    if model is None or current_df is None:
        return performance_results
    
    try:
        # Preparar dados atuais
        current_pandas = current_df.select('sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species').toPandas()
        X_current = current_pandas[['sepal_length', 'sepal_width', 'petal_length', 'petal_width']]
        y_current = current_pandas['species']
        
        # Preparar dados de referência
        reference_pandas = reference_df.select('sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species').toPandas()
        X_reference = reference_pandas[['sepal_length', 'sepal_width', 'petal_length', 'petal_width']]
        y_reference = reference_pandas['species']
        
        # Predições
        y_pred_current = model.predict(X_current)
        y_pred_reference = model.predict(X_reference)
        
        # Métricas atuais
        current_metrics = {
            'accuracy': accuracy_score(y_current, y_pred_current),
            'precision': precision_score(y_current, y_pred_current, average='weighted'),
            'recall': recall_score(y_current, y_pred_current, average='weighted'),
            'f1': f1_score(y_current, y_pred_current, average='weighted')
        }
        
        # Métricas baseline
        baseline_metrics = {
            'accuracy': accuracy_score(y_reference, y_pred_reference),
            'precision': precision_score(y_reference, y_pred_reference, average='weighted'),
            'recall': recall_score(y_reference, y_pred_reference, average='weighted'),
            'f1': f1_score(y_reference, y_pred_reference, average='weighted')
        }
        
        performance_results['current_metrics'] = current_metrics
        performance_results['baseline_metrics'] = baseline_metrics
        
        print("📊 Métricas atuais:")
        for metric, value in current_metrics.items():
            print(f"   {metric}: {value:.4f}")
        
        print("\n📊 Métricas baseline:")
        for metric, value in baseline_metrics.items():
            print(f"   {metric}: {value:.4f}")
        
        # Análise de degradação
        print("\n📉 Análise de degradação:")
        for metric in current_metrics.keys():
            degradation = baseline_metrics[metric] - current_metrics[metric]
            degradation_pct = degradation / baseline_metrics[metric] if baseline_metrics[metric] != 0 else 0
            
            performance_results['metric_degradation'][metric] = {
                'absolute': degradation,
                'percentage': degradation_pct,
                'is_degraded': degradation_pct > METRIC_DEGRADATION_THRESHOLD
            }
            
            if degradation_pct > METRIC_DEGRADATION_THRESHOLD:
                performance_results['has_degradation'] = True
                performance_results['degraded_metrics'].append(metric)
            
            status = "🚨 DEGRADOU" if degradation_pct > METRIC_DEGRADATION_THRESHOLD else "✅ OK"
            print(f"   {metric}: {degradation_pct:+.2%} {status}")
        
        return performance_results
        
    except Exception as e:
        print(f"❌ Erro na avaliação: {str(e)}")
        return performance_results

performance_analysis = evaluate_model_performance(model, current_df, reference_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📲 Notificações Microsoft Teams

# COMMAND ----------

def create_teams_message(drift_analysis, performance_analysis, model_version):
    """
    Cria mensagem formatada para Microsoft Teams
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determinar cor do card baseado na severidade
    if drift_analysis['has_drift'] or performance_analysis['has_degradation']:
        theme_color = "FF0000"  # Vermelho para alertas
        status_emoji = "🚨"
        status_text = "ALERTA"
    else:
        theme_color = "00FF00"  # Verde para OK
        status_emoji = "✅"
        status_text = "OK"
    
    # Criar seções da mensagem
    sections = []
    
    # Seção de status geral
    sections.append({
        "activityTitle": f"{status_emoji} Monitoramento de Modelo Iris - {status_text}",
        "activitySubtitle": f"Executado em {timestamp}",
        "activityImage": "https://img.icons8.com/color/96/000000/artificial-intelligence.png",
        "facts": [
            {"name": "Modelo", "value": f"v{model_version.version if model_version else 'N/A'}"},
            {"name": "Timestamp", "value": timestamp},
            {"name": "Status Drift", "value": "🚨 DETECTADO" if drift_analysis['has_drift'] else "✅ OK"},
            {"name": "Status Performance", "value": "🚨 DEGRADAÇÃO" if performance_analysis['has_degradation'] else "✅ OK"}
        ]
    })
    
    # Seção de drift (se detectado)
    if drift_analysis['has_drift']:
        drift_facts = [
            {"name": "Score Geral de Drift", "value": f"{drift_analysis['overall_drift_score']:.4f}"},
            {"name": "Features Afetadas", "value": ", ".join(drift_analysis['drift_features'])}
        ]
        
        for feature in drift_analysis['drift_features']:
            details = drift_analysis['drift_details'][feature]
            drift_facts.append({
                "name": f"📊 {feature}",
                "value": f"p-value: {details['ks_p_value']:.4f}, Mean shift: {details['mean_shift']:.4f}"
            })
        
        sections.append({
            "activityTitle": "🔍 Análise de Drift",
            "facts": drift_facts
        })
    
    # Seção de performance (se há degradação)
    if performance_analysis['has_degradation']:
        perf_facts = [
            {"name": "Métricas Degradadas", "value": ", ".join(performance_analysis['degraded_metrics'])}
        ]
        
        for metric in performance_analysis['current_metrics'].keys():
            current = performance_analysis['current_metrics'][metric]
            baseline = performance_analysis['baseline_metrics'][metric]
            degradation = performance_analysis['metric_degradation'][metric]
            
            perf_facts.append({
                "name": f"📈 {metric.upper()}",
                "value": f"Atual: {current:.4f} | Baseline: {baseline:.4f} | Mudança: {degradation['percentage']:+.2%}"
            })
        
        sections.append({
            "activityTitle": "🎯 Análise de Performance",
            "facts": perf_facts
        })
    
    # Estrutura completa da mensagem
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": theme_color,
        "summary": f"Monitoramento Modelo Iris - {status_text}",
        "sections": sections,
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Ver Dashboard MLflow",
                "targets": [
                    {"os": "default", "uri": "https://your-databricks-workspace.com"}
                ]
            }
        ]
    }
    
    return message

def send_teams_notification(message):
    """
    Envia notificação para Microsoft Teams
    """
    try:
        if TEAMS_WEBHOOK_URL == "https://outlook.office.com/webhook/YOUR_WEBHOOK_URL":
            print("⚠️ Webhook URL não configurada. Simulando envio...")
            print("📧 Mensagem que seria enviada:")
            print(json.dumps(message, indent=2))
            return True
        
        response = requests.post(
            TEAMS_WEBHOOK_URL,
            data=json.dumps(message),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Notificação enviada com sucesso para Teams!")
            return True
        else:
            print(f"❌ Erro ao enviar notificação: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar notificação: {str(e)}")
        return False

# Gerar e enviar notificação
teams_message = create_teams_message(drift_analysis, performance_analysis, model_version)
notification_sent = send_teams_notification(teams_message)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Logging de Métricas no MLflow

# COMMAND ----------

def log_monitoring_metrics(drift_analysis, performance_analysis):
    """
    Registra métricas de monitoramento no MLflow
    """
    try:
        with mlflow.start_run(run_name="model_monitoring"):
            # Log drift metrics
            mlflow.log_metric("drift_overall_score", drift_analysis['overall_drift_score'])
            mlflow.log_metric("drift_detected", 1 if drift_analysis['has_drift'] else 0)
            mlflow.log_metric("num_drift_features", len(drift_analysis['drift_features']))
            
            # Log detailed drift metrics
            for feature, details in drift_analysis['drift_details'].items():
                mlflow.log_metric(f"drift_{feature}_ks_pvalue", details['ks_p_value'])
                mlflow.log_metric(f"drift_{feature}_mean_shift", details['mean_shift'])
                mlflow.log_metric(f"drift_{feature}_score", details['drift_score'])
            
            # Log performance metrics
            for metric, value in performance_analysis['current_metrics'].items():
                mlflow.log_metric(f"current_{metric}", value)
                
            for metric, value in performance_analysis['baseline_metrics'].items():
                mlflow.log_metric(f"baseline_{metric}", value)
            
            # Log degradation metrics
            mlflow.log_metric("performance_degradation", 1 if performance_analysis['has_degradation'] else 0)
            mlflow.log_metric("num_degraded_metrics", len(performance_analysis['degraded_metrics']))
            
            for metric, details in performance_analysis['metric_degradation'].items():
                mlflow.log_metric(f"degradation_{metric}_pct", details['percentage'])
            
            # Log monitoring metadata
            mlflow.log_param("monitoring_timestamp", datetime.now().isoformat())
            mlflow.log_param("drift_threshold", DRIFT_P_VALUE_THRESHOLD)
            mlflow.log_param("degradation_threshold", METRIC_DEGRADATION_THRESHOLD)
            mlflow.log_param("teams_notification_sent", notification_sent)
            
            print("📊 Métricas de monitoramento registradas no MLflow")
            
    except Exception as e:
        print(f"❌ Erro ao registrar métricas: {str(e)}")

log_monitoring_metrics(drift_analysis, performance_analysis)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Resumo da Execução

# COMMAND ----------

print("🎯 RESUMO DO MONITORAMENTO")
print("=" * 50)
print(f"🕒 Timestamp: {datetime.now()}")
print(f"🤖 Modelo: v{model_version.version if model_version else 'N/A'}")
print(f"📊 Dados analisados: {current_df.count() if current_df else 0} registros")

print(f"\n🔍 ANÁLISE DE DRIFT:")
print(f"   Status: {'🚨 DETECTADO' if drift_analysis['has_drift'] else '✅ OK'}")
print(f"   Score geral: {drift_analysis['overall_drift_score']:.4f}")
print(f"   Features afetadas: {len(drift_analysis['drift_features'])}")

print(f"\n🎯 ANÁLISE DE PERFORMANCE:")
print(f"   Status: {'🚨 DEGRADAÇÃO' if performance_analysis['has_degradation'] else '✅ OK'}")
print(f"   Métricas degradadas: {len(performance_analysis['degraded_metrics'])}")

if performance_analysis['current_metrics']:
    print(f"\n📈 MÉTRICAS ATUAIS:")
    for metric, value in performance_analysis['current_metrics'].items():
        baseline = performance_analysis['baseline_metrics'].get(metric, 0)
        change = ((value - baseline) / baseline * 100) if baseline != 0 else 0
        print(f"   {metric.upper()}: {value:.4f} ({change:+.2f}%)")

print(f"\n📲 NOTIFICAÇÃO:")
print(f"   Teams: {'✅ ENVIADA' if notification_sent else '❌ FALHOU'}")

# Determinar status geral
overall_status = "🚨 ALERTA" if (drift_analysis['has_drift'] or performance_analysis['has_degradation']) else "✅ SAUDÁVEL"
print(f"\n🏥 STATUS GERAL: {overall_status}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔄 Próximos Passos Automáticos
# MAGIC 
# MAGIC Se alertas foram detectados:
# MAGIC 1. **Drift detectado**: Considerar retreinamento do modelo
# MAGIC 2. **Performance degradada**: Investigar causas e atualizar modelo
# MAGIC 3. **Notificação enviada**: Equipe será alertada via Teams
# MAGIC 
# MAGIC ### 📅 Agendamento Recomendado:
# MAGIC - **Frequência**: A cada modificação na tabela Silver
# MAGIC - **Trigger**: File arrival trigger no Delta Lake
# MAGIC - **Fallback**: Execução diária às 8:00 AM
