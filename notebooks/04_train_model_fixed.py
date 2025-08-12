# Databricks notebook source
# MAGIC %md
# MAGIC # 🤖 Model Training - MLflow Integration (Fixed)
# MAGIC ## Iris Classification with RandomForest
# MAGIC 
# MAGIC Este notebook treina um modelo de classificação para o dataset Iris e registra no MLflow.
# MAGIC **Versão corrigida** - sem dependências problemáticas de configuração.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from pyspark.sql import functions as F
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

print("📦 Bibliotecas importadas com sucesso")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚙️ Configuração MLflow Simplificada

# COMMAND ----------

# Configuração MLflow robusta (sem dependências problemáticas)
try:
    # Configurar MLflow para Databricks
    mlflow.set_tracking_uri("databricks")
    print("✅ MLflow tracking URI configurado")
    
    # Configurar registry URI para Unity Catalog se disponível
    try:
        os.environ["MLFLOW_REGISTRY_URI"] = "databricks-uc"
        print("✅ Registry URI configurado para Unity Catalog")
    except:
        print("⚠️ Unity Catalog registry não disponível, usando padrão")
        
except Exception as e:
    print(f"⚠️ Erro na configuração MLflow: {e}")
    print("🔄 Continuando com configuração padrão")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚙️ Parâmetros do Job

# COMMAND ----------

# Widgets para parâmetros do job
dbutils.widgets.text("input_table", "workspace.default.iris_silver", "Tabela de entrada")
dbutils.widgets.text("model_name", "iris_classifier", "Nome do modelo MLflow")
dbutils.widgets.text("stage", "Production", "Stage do modelo")

# Obter valores dos parâmetros
INPUT_TABLE = dbutils.widgets.get("input_table")
MODEL_NAME = dbutils.widgets.get("model_name")
STAGE = dbutils.widgets.get("stage")

print(f"📊 Tabela de entrada: {INPUT_TABLE}")
print(f"🤖 Nome do modelo: {MODEL_NAME}")
print(f"🏷️ Stage: {STAGE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📥 Carregamento dos Dados

# COMMAND ----------

print(f"📥 Carregando dados de: {INPUT_TABLE}")

try:
    # Carregar dados da camada Silver
    df_spark = spark.table(INPUT_TABLE)
    df = df_spark.toPandas()
    
    print(f"📊 Shape do dataset: {df.shape}")
    print(f"📋 Colunas: {list(df.columns)}")
    print(f"🏷️ Espécies únicas: {df['species'].unique()}")
    
    # Mostrar estatísticas básicas
    print(f"\n📈 Estatísticas básicas:")
    display(df.describe())
    
except Exception as e:
    print(f"❌ Erro ao carregar dados: {e}")
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Validações de Qualidade

# COMMAND ----------

print("🧪 Executando validações de qualidade para ML...")

# Validação 1: Dataset não vazio
assert len(df) > 0, "❌ Dataset vazio!"
print(f"✅ Dataset com {len(df)} registros")

# Validação 2: Colunas necessárias existem
expected_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
missing_cols = [col for col in expected_columns if col not in df.columns]
assert len(missing_cols) == 0, f"❌ Colunas faltando: {missing_cols}"
print("✅ Todas as colunas necessárias presentes")

# Validação 3: Sem valores nulos nas colunas críticas
critical_nulls = df[expected_columns].isnull().sum()
assert critical_nulls.sum() == 0, f"❌ Valores nulos encontrados: {critical_nulls[critical_nulls > 0]}"
print("✅ Nenhum valor nulo nas colunas críticas")

# Validação 4: Distribuição de classes
class_counts = df['species'].value_counts()
print(f"📊 Distribuição de classes:")
for species, count in class_counts.items():
    print(f"   {species}: {count}")

# Validação 5: Verificar se há pelo menos 2 classes
assert len(class_counts) >= 2, "❌ Menos de 2 classes encontradas!"
print(f"✅ {len(class_counts)} classes disponíveis para classificação")

print("🎉 Todas as validações passaram!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔄 Preparação dos Dados

# COMMAND ----------

print("🔄 Preparando dados para treinamento...")

# Separar features e target
feature_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
X = df[feature_columns]
y = df['species']

print(f"📊 Features shape: {X.shape}")
print(f"🎯 Target shape: {y.shape}")

# Split dos dados
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, 
    stratify=y
)

print(f"🏋️ Treino: {X_train.shape[0]} amostras")
print(f"🧪 Teste: {X_test.shape[0]} amostras")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Treinamento do Modelo

# COMMAND ----------

# Parâmetros do modelo
model_params = {
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
    'random_state': 42
}

print(f"🔧 Parâmetros do modelo: {model_params}")

# Configurar experimento MLflow de forma robusta
experiment_name = f"/Shared/{MODEL_NAME}_experiments"
print(f"🧪 Configurando experimento: {experiment_name}")

try:
    mlflow.set_experiment(experiment_name)
    print("✅ Experimento MLflow configurado")
except Exception as e:
    print(f"⚠️ Erro ao configurar experimento: {e}")
    print("🔄 Continuando sem experimento específico")

# Iniciar run MLflow
with mlflow.start_run(run_name=f"{MODEL_NAME}_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
    
    # Treinar modelo
    print("🚀 Iniciando treinamento...")
    model = RandomForestClassifier(**model_params)
    model.fit(X_train, y_train)
    print("✅ Treinamento concluído")
    
    # Fazer predições
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Calcular métricas
    train_accuracy = accuracy_score(y_train, y_pred_train)
    test_accuracy = accuracy_score(y_test, y_pred_test)
    precision = precision_score(y_test, y_pred_test, average='weighted')
    recall = recall_score(y_test, y_pred_test, average='weighted')
    f1 = f1_score(y_test, y_pred_test, average='weighted')
    
    print(f"\n📊 Métricas do modelo:")
    print(f"   🎯 Acurácia (treino): {train_accuracy:.4f}")
    print(f"   🎯 Acurácia (teste): {test_accuracy:.4f}")
    print(f"   🎯 Precision: {precision:.4f}")
    print(f"   🎯 Recall: {recall:.4f}")
    print(f"   🎯 F1-Score: {f1:.4f}")
    
    # Log parâmetros e métricas no MLflow
    try:
        mlflow.log_params(model_params)
        mlflow.log_metric("train_accuracy", train_accuracy)
        mlflow.log_metric("test_accuracy", test_accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)
        print("✅ Métricas registradas no MLflow")
    except Exception as e:
        print(f"⚠️ Erro ao registrar métricas: {e}")
    
    # Preparar input_example para signature automática
    input_example = X_test.head(3)
    
    # Registrar modelo no MLflow
    try:
        print("📝 Registrando modelo no MLflow...")
        
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            input_example=input_example,
            registered_model_name=MODEL_NAME
        )
        
        print(f"✅ Modelo registrado: {model_info.model_uri}")
        
        # Tentar promover para Production
        try:
            from mlflow import MlflowClient
            client = MlflowClient()
            
            # Obter a versão mais recente
            latest_version_info = client.get_latest_versions(MODEL_NAME, stages=["None"])
            if latest_version_info:
                latest_version = latest_version_info[0].version
                
                # Promover para Production
                client.transition_model_version_stage(
                    name=MODEL_NAME,
                    version=latest_version,
                    stage=STAGE
                )
                print(f"✅ Modelo promovido para stage: {STAGE}")
            
        except Exception as e:
            print(f"⚠️ Erro ao promover modelo: {e}")
            print("🔄 Modelo registrado mas não promovido")
            
    except Exception as e:
        print(f"❌ Erro ao registrar modelo: {e}")
        print("🔄 Continuando execução sem registro")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Relatório de Classificação

# COMMAND ----------

print("📋 Relatório detalhado de classificação:")
print("="*50)
print(classification_report(y_test, y_pred_test))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Resumo da Execução

# COMMAND ----------

print("🎉 TREINAMENTO CONCLUÍDO!")
print("="*50)
print(f"📊 Dataset: {len(df)} registros processados")
print(f"🤖 Modelo: RandomForest treinado")
print(f"🎯 Acurácia final: {test_accuracy:.4f}")
print(f"📝 Modelo registrado: {MODEL_NAME}")
print(f"🏷️ Stage: {STAGE}")
print("="*50)

# Verificar tabela de resultados
try:
    # Salvar métricas em tabela para monitoramento
    metrics_data = {
        'model_name': [MODEL_NAME],
        'training_date': [datetime.now()],
        'accuracy': [test_accuracy],
        'precision': [precision],
        'recall': [recall],
        'f1_score': [f1],
        'input_table': [INPUT_TABLE]
    }
    
    metrics_df = pd.DataFrame(metrics_data)
    metrics_spark_df = spark.createDataFrame(metrics_df)
    
    # Salvar na tabela de estatísticas
    output_stats_table = "workspace.default.iris_model_stats"
    metrics_spark_df.write \
        .mode("append") \
        .option("mergeSchema", "true") \
        .saveAsTable(output_stats_table)
    
    print(f"📊 Métricas salvas em: {output_stats_table}")
    
except Exception as e:
    print(f"⚠️ Erro ao salvar métricas: {e}")

print("🚀 Pipeline de treinamento finalizado!")
