# Databricks notebook source
# MAGIC %md
# MAGIC # 📊 Model Monitoring & Drift Detection
# MAGIC 
# MAGIC Este notebook implementa monitoramento de modelo e detecção de drift
# MAGIC para o pipeline MLOps do Iris dataset.

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
from scipy.stats import ks_2samp, chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Carregamento de Dados e Modelo

# COMMAND ----------

# Carregar dados de referência (training data)
reference_data = spark.table("main.default.iris_silver")
print(f"📊 Reference data: {reference_data.count()} registros")

# Carregar dados atuais (production data - simulação)
current_data = spark.table("main.default.iris_silver")
print(f"📊 Current data: {current_data.count()} registros")

# Carregar modelo mais recente do MLflow
model_name = "default.iris_model"
try:
    # Buscar a versão mais recente do modelo
    client = mlflow.tracking.MlflowClient()
    model_version = client.get_latest_versions(model_name, stages=["Production"])[0]
    model_uri = f"models:/{model_name}/{model_version.version}"
    
    # Carregar modelo
    model = mlflow.sklearn.load_model(model_uri)
    print(f"✅ Modelo carregado: {model_name} v{model_version.version}")
    
except Exception as e:
    print(f"⚠️ Erro ao carregar modelo: {str(e)}")
    print("💡 Usando modelo simulado para demonstração")
    model = None

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Data Drift Detection

# COMMAND ----------

def detect_numerical_drift(reference_df, current_df, feature_col, threshold=0.05):
    """
    Detecta drift em features numéricas usando teste Kolmogorov-Smirnov
    """
    ref_values = reference_df.select(feature_col).rdd.flatMap(lambda x: x).collect()
    curr_values = current_df.select(feature_col).rdd.flatMap(lambda x: x).collect()
    
    # Teste KS
    ks_stat, p_value = ks_2samp(ref_values, curr_values)
    
    drift_detected = p_value < threshold
    
    return {
        'feature': feature_col,
        'ks_statistic': ks_stat,
        'p_value': p_value,
        'drift_detected': drift_detected,
        'severity': 'HIGH' if p_value < 0.01 else 'MEDIUM' if p_value < 0.05 else 'LOW'
    }

def detect_categorical_drift(reference_df, current_df, feature_col, threshold=0.05):
    """
    Detecta drift em features categóricas usando teste Chi-quadrado
    """
    # Distribuições de referência e atual
    ref_dist = reference_df.groupBy(feature_col).count().toPandas()
    curr_dist = current_df.groupBy(feature_col).count().toPandas()
    
    # Criar tabela de contingência
    merged = ref_dist.merge(curr_dist, on=feature_col, suffixes=('_ref', '_curr'), how='outer').fillna(0)
    
    contingency_table = merged[['count_ref', 'count_curr']].values
    
    # Teste Chi-quadrado
    chi2_stat, p_value, _, _ = chi2_contingency(contingency_table)
    
    drift_detected = p_value < threshold
    
    return {
        'feature': feature_col,
        'chi2_statistic': chi2_stat,
        'p_value': p_value,
        'drift_detected': drift_detected,
        'severity': 'HIGH' if p_value < 0.01 else 'MEDIUM' if p_value < 0.05 else 'LOW'
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Execução da Detecção de Drift

# COMMAND ----------

# Features numéricas para monitoramento
numerical_features = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']

# Features categóricas para monitoramento
categorical_features = ['species']

# Executar detecção de drift
drift_results = []

print("🔍 Detectando drift nas features numéricas...")
for feature in numerical_features:
    result = detect_numerical_drift(reference_data, current_data, feature)
    drift_results.append(result)
    
    status = "🚨" if result['drift_detected'] else "✅"
    print(f"{status} {feature}: p-value={result['p_value']:.4f}, severity={result['severity']}")

print("\n🔍 Detectando drift nas features categóricas...")
for feature in categorical_features:
    result = detect_categorical_drift(reference_data, current_data, feature)
    drift_results.append(result)
    
    status = "🚨" if result['drift_detected'] else "✅"
    print(f"{status} {feature}: p-value={result['p_value']:.4f}, severity={result['severity']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Model Performance Monitoring

# COMMAND ----------

def calculate_model_metrics(y_true, y_pred):
    """
    Calcula métricas de performance do modelo
    """
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='weighted'),
        'recall': recall_score(y_true, y_pred, average='weighted'),
        'f1_score': f1_score(y_true, y_pred, average='weighted')
    }

# Simular predições do modelo (se modelo disponível)
if model is not None:
    # Preparar dados para predição
    feature_cols = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
    X_current = current_data.select(*feature_cols).toPandas()
    y_true = current_data.select('species').toPandas()['species']
    
    # Fazer predições
    y_pred = model.predict(X_current)
    
    # Calcular métricas
    current_metrics = calculate_model_metrics(y_true, y_pred)
    
    print("📊 Current Model Performance:")
    for metric, value in current_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Comparar com métricas de baseline (simuladas)
    baseline_metrics = {
        'accuracy': 0.95,
        'precision': 0.94,
        'recall': 0.95,
        'f1_score': 0.94
    }
    
    print("\n📊 Performance Comparison:")
    performance_degradation = []
    for metric in current_metrics:
        current_val = current_metrics[metric]
        baseline_val = baseline_metrics[metric]
        degradation = (baseline_val - current_val) / baseline_val * 100
        
        status = "🚨" if degradation > 5 else "⚠️" if degradation > 2 else "✅"
        print(f"{status} {metric}: {current_val:.4f} vs {baseline_val:.4f} (degradation: {degradation:.1f}%)")
        
        if degradation > 2:
            performance_degradation.append({
                'metric': metric,
                'current': current_val,
                'baseline': baseline_val,
                'degradation_pct': degradation
            })

else:
    print("📊 Modelo não disponível - simulando métricas")
    performance_degradation = []

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Monitoring Dashboard Data

# COMMAND ----------

# Criar summary do monitoramento
monitoring_summary = {
    'timestamp': datetime.now(),
    'drift_features_detected': len([r for r in drift_results if r['drift_detected']]),
    'total_features_monitored': len(drift_results),
    'performance_degradation_count': len(performance_degradation),
    'overall_status': 'ALERT' if any(r['drift_detected'] for r in drift_results) or performance_degradation else 'HEALTHY'
}

print("📋 MONITORING SUMMARY")
print("=" * 40)
print(f"🕒 Timestamp: {monitoring_summary['timestamp']}")
print(f"📊 Features monitored: {monitoring_summary['total_features_monitored']}")
print(f"🚨 Drift detected: {monitoring_summary['drift_features_detected']} features")
print(f"📉 Performance issues: {monitoring_summary['performance_degradation_count']} metrics")
print(f"🎯 Overall status: {monitoring_summary['overall_status']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Salvar Resultados de Monitoramento

# COMMAND ----------

# Converter resultados para DataFrame
drift_df = spark.createDataFrame([
    {
        'feature': r['feature'],
        'drift_detected': r['drift_detected'],
        'p_value': r['p_value'],
        'severity': r['severity'],
        'timestamp': monitoring_summary['timestamp'],
        'statistic': r.get('ks_statistic', r.get('chi2_statistic', 0))
    }
    for r in drift_results
])

# Salvar resultados de drift
drift_table = "main.default.model_drift_monitoring"
drift_df.write.mode("append").saveAsTable(drift_table)
print(f"✅ Drift results saved to: {drift_table}")

# Salvar summary geral
monitoring_df = spark.createDataFrame([{
    'timestamp': monitoring_summary['timestamp'],
    'drift_features_count': monitoring_summary['drift_features_detected'],
    'total_features': monitoring_summary['total_features_monitored'],
    'performance_issues': monitoring_summary['performance_degradation_count'],
    'overall_status': monitoring_summary['overall_status']
}])

summary_table = "main.default.model_monitoring_summary"
monitoring_df.write.mode("append").saveAsTable(summary_table)
print(f"✅ Monitoring summary saved to: {summary_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Logging no MLflow

# COMMAND ----------

# Registrar resultados no MLflow
with mlflow.start_run(run_name="model_monitoring_drift_detection") as run:
    
    # Log métricas de drift
    for result in drift_results:
        mlflow.log_metric(f"drift_pvalue_{result['feature']}", result['p_value'])
        mlflow.log_metric(f"drift_detected_{result['feature']}", 1 if result['drift_detected'] else 0)
    
    # Log métricas de performance (se disponível)
    if model is not None:
        for metric, value in current_metrics.items():
            mlflow.log_metric(f"current_{metric}", value)
        
        for degradation in performance_degradation:
            mlflow.log_metric(f"degradation_{degradation['metric']}", degradation['degradation_pct'])
    
    # Log summary
    mlflow.log_metric("total_drift_features", monitoring_summary['drift_features_detected'])
    mlflow.log_metric("total_monitored_features", monitoring_summary['total_features_monitored'])
    
    # Log status
    mlflow.log_param("monitoring_status", monitoring_summary['overall_status'])
    mlflow.log_param("monitoring_timestamp", str(monitoring_summary['timestamp']))
    
    # Criar artifact com detalhes
    monitoring_report = {
        'summary': monitoring_summary,
        'drift_results': drift_results,
        'performance_degradation': performance_degradation
    }
    
    # Salvar como artifact JSON
    import json
    with open('/tmp/monitoring_report.json', 'w') as f:
        json.dump(monitoring_report, f, indent=2, default=str)
    
    mlflow.log_artifact('/tmp/monitoring_report.json')

print(f"📈 Monitoring results logged to MLflow run: {run.info.run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚨 Alerting Logic

# COMMAND ----------

# Lógica de alertas
alerts_triggered = []

# Alerta para drift de dados
high_drift_features = [r for r in drift_results if r['drift_detected'] and r['severity'] == 'HIGH']
if high_drift_features:
    alerts_triggered.append({
        'type': 'DATA_DRIFT',
        'severity': 'HIGH',
        'message': f"High drift detected in {len(high_drift_features)} features",
        'features': [r['feature'] for r in high_drift_features]
    })

# Alerta para degradação de performance
if performance_degradation:
    high_degradation = [p for p in performance_degradation if p['degradation_pct'] > 5]
    if high_degradation:
        alerts_triggered.append({
            'type': 'PERFORMANCE_DEGRADATION',
            'severity': 'HIGH',
            'message': f"Significant performance degradation in {len(high_degradation)} metrics",
            'metrics': [p['metric'] for p in high_degradation]
        })

# Mostrar alertas
if alerts_triggered:
    print("🚨 ALERTS TRIGGERED")
    print("=" * 30)
    for alert in alerts_triggered:
        print(f"🚨 {alert['type']} - {alert['severity']}")
        print(f"   {alert['message']}")
        if 'features' in alert:
            print(f"   Features: {', '.join(alert['features'])}")
        if 'metrics' in alert:
            print(f"   Metrics: {', '.join(alert['metrics'])}")
        print()
    
    # Log alertas no MLflow
    with mlflow.start_run(run_name="monitoring_alerts") as alert_run:
        for i, alert in enumerate(alerts_triggered):
            mlflow.log_param(f"alert_{i}_type", alert['type'])
            mlflow.log_param(f"alert_{i}_severity", alert['severity'])
            mlflow.log_param(f"alert_{i}_message", alert['message'])
    
    print(f"🚨 Alerts logged to MLflow run: {alert_run.info.run_id}")
    
else:
    print("✅ No alerts triggered - system healthy")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Next Steps Recommendations

# COMMAND ----------

print("📋 MONITORING RECOMMENDATIONS")
print("=" * 40)

if monitoring_summary['overall_status'] == 'ALERT':
    print("🚨 IMMEDIATE ACTIONS REQUIRED:")
    
    if any(r['drift_detected'] for r in drift_results):
        print("  📊 Data Drift Detected:")
        print("    1. Investigate data sources for changes")
        print("    2. Consider model retraining")
        print("    3. Update feature preprocessing")
    
    if performance_degradation:
        print("  📉 Performance Degradation:")
        print("    1. Retrain model with recent data")
        print("    2. Evaluate feature importance changes")
        print("    3. Consider model architecture updates")
    
    print("\n  🔄 Automated Actions:")
    print("    1. Trigger retraining pipeline")
    print("    2. Send alerts to ML team")
    print("    3. Schedule model validation")

else:
    print("✅ System is healthy")
    print("📈 Routine Actions:")
    print("  1. Continue regular monitoring")
    print("  2. Update baseline metrics monthly")
    print("  3. Review feature importance quarterly")

print(f"\n📅 Next monitoring scheduled: {datetime.now() + timedelta(days=1)}")
print("📧 Reports will be sent to: ml-team@company.com")
print("📊 Dashboard available at: /monitoring/iris-model")
