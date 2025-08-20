# Databricks notebook source
# MAGIC %md
# MAGIC # 🔮 Iris Model Inference & Visualization with MLflow
# MAGIC 
# MAGIC Este notebook:
# MAGIC 1. Carrega modelo do MLflow Registry
# MAGIC 2. Faz inferências usando Spark UDF
# MAGIC 3. Visualiza os resultados com gráficos
# MAGIC 4. Calcula métricas de performance

# COMMAND ----------

# Imports necessários
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mlflow
import mlflow.pyfunc
from pyspark.sql import SparkSession
from pyspark.sql.functions import struct, col, rand, lit
from pyspark.sql.types import StructType, StructField, DoubleType, StringType, TimestampType, IntegerType
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Inicializar Spark session
spark = SparkSession.builder.appName("IrisMLflowInference").getOrCreate()

# Configurar MLflow
mlflow.set_tracking_uri("databricks")

# Configurar estilo dos gráficos
plt.style.use('default')
sns.set_palette("husl")

print("🔮 Iniciando job de inferência do modelo Iris com MLflow...")
print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Parâmetros do Job

# COMMAND ----------

# Parâmetros para inferência
MODEL_NAME = "iris_classifier"
NUM_SAMPLES = 100

print(f"🎯 Modelo: {MODEL_NAME}")
print(f"📊 Amostras: {NUM_SAMPLES}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Carregamento do Modelo via MLflow

# COMMAND ----------

print("🔍 Carregando modelo específico do MLflow...")

try:
    # Usar run ID específico que você encontrou
    specific_run_id = "158080ed85b2472081e739ff7eca2354"
    logged_model = f'runs:/{specific_run_id}/model'
    
    print(f"🎯 Usando run ID específico: {specific_run_id}")
    print(f"📦 Model URI: {logged_model}")
    
    # Carregar modelo como Spark UDF
    print("🚀 Carregando modelo como Spark UDF...")
    loaded_model = mlflow.pyfunc.spark_udf(spark, model_uri=logged_model)
    print("✅ Modelo carregado como Spark UDF com sucesso!")
    
    use_mlflow_model = True
        
except Exception as e:
    print(f"❌ Erro ao carregar modelo específico: {e}")
    print("💡 Tentando buscar modelo automaticamente...")
    
    # Fallback: buscar automaticamente
    try:
        from mlflow.tracking import MlflowClient
        client = MlflowClient()
        current_user = spark.sql('SELECT current_user()').collect()[0][0]
        
        print(f"👤 Usuário: {current_user}")
        
        # Buscar runs recentes em todos os experimentos
        experiments = client.search_experiments()
        logged_model = None
        
        for experiment in experiments:
            try:
                runs = client.search_runs(
                    experiment_ids=[experiment.experiment_id], 
                    order_by=["start_time DESC"], 
                    max_results=3
                )
                
                for run in runs:
                    run_id = run.info.run_id
                    try:
                        # Verificar se esta run tem um modelo
                        artifacts = client.list_artifacts(run_id)
                        model_artifacts = [a for a in artifacts if a.path == "model"]
                        if model_artifacts:
                            logged_model = f'runs:/{run_id}/model'
                            print(f"✅ Modelo encontrado automaticamente: {logged_model}")
                            break
                    except:
                        continue
                
                if logged_model:
                    break
                    
            except:
                continue
        
        if logged_model:
            loaded_model = mlflow.pyfunc.spark_udf(spark, model_uri=logged_model)
            print("✅ Modelo carregado automaticamente!")
            use_mlflow_model = True
        else:
            raise Exception("Nenhum modelo encontrado")
            
    except Exception as fallback_error:
        print(f"❌ Erro no fallback: {fallback_error}")
        print("❌ FALHA: Não foi possível carregar modelo do MLflow")
        print("💡 Certifique-se que o modelo foi treinado e registrado corretamente")
        raise Exception("Modelo MLflow obrigatório não encontrado. Execute o treinamento primeiro.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Geração de Dados Sintéticos para Inferência

# COMMAND ----------

print(f"🎲 Gerando {NUM_SAMPLES} amostras sintéticas em Spark DataFrame...")

# Schema para dados sintéticos
schema = StructType([
    StructField("sepal_length_cm", DoubleType(), True),
    StructField("sepal_width_cm", DoubleType(), True),
    StructField("petal_length_cm", DoubleType(), True),
    StructField("petal_width_cm", DoubleType(), True),
    StructField("sample_id", IntegerType(), True)
])

# Gerar dados sintéticos usando estatísticas realísticas do Iris
synthetic_data = []
np.random.seed(42)

# Estatísticas baseadas no dataset Iris real
sepal_length_stats = (5.84, 0.83)  # média, desvio
sepal_width_stats = (3.06, 0.44)
petal_length_stats = (3.76, 1.77)
petal_width_stats = (1.20, 0.76)

for i in range(NUM_SAMPLES):
    row = (
        float(max(0.1, np.random.normal(sepal_length_stats[0], sepal_length_stats[1]))),
        float(max(0.1, np.random.normal(sepal_width_stats[0], sepal_width_stats[1]))),
        float(max(0.1, np.random.normal(petal_length_stats[0], petal_length_stats[1]))),
        float(max(0.1, np.random.normal(petal_width_stats[0], petal_width_stats[1]))),
        i
    )
    synthetic_data.append(row)

# Criar Spark DataFrame
inference_df = spark.createDataFrame(synthetic_data, schema)

print(f"✅ DataFrame criado com {inference_df.count()} amostras!")
print("📊 Schema do DataFrame:")
inference_df.printSchema()

print("📈 Primeiras 5 amostras:")
inference_df.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔮 Execução da Inferência com MLflow

# COMMAND ----------

print("🚀 Executando inferência usando MLflow Spark UDF...")

# Usar modelo MLflow obrigatório
print("✅ Usando modelo do MLflow Registry/Run")

# Executar predição usando struct com todas as features
inference_with_predictions = inference_df.withColumn(
    'predictions', 
    loaded_model(struct(
        col("sepal_length_cm"),
        col("sepal_width_cm"), 
        col("petal_length_cm"),
        col("petal_width_cm")
    ))
)

# Adicionar metadados
inference_with_predictions = inference_with_predictions.withColumn(
    "inference_timestamp", 
    lit(datetime.now())
).withColumn(
    "model_name",
    lit(MODEL_NAME)
).withColumn(
    "model_source",
    lit("mlflow")
).withColumn(
    "model_uri",
    lit(logged_model)
)

print("✅ Inferência concluída!")
print("📊 Resultados da inferência:")
inference_with_predictions.show(5)

# Converter para pandas para análises e visualizações
results_pd = inference_with_predictions.toPandas()

print(f"📊 Total de predições: {len(results_pd)}")
print(f"📈 Distribuição das predições:")
print(results_pd['predictions'].value_counts().sort_index())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Visualizações dos Resultados

# COMMAND ----------

print("📈 Gerando visualizações...")

# Mapear predições para nomes das classes
class_names = ['setosa', 'versicolor', 'virginica']
results_pd['predicted_class'] = results_pd['predictions'].apply(lambda x: class_names[int(x)])

# Configurar plots
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('🔮 MLflow Model Inference - Análise dos Resultados', fontsize=16, fontweight='bold')

# 1. Distribuição das Predições
ax1 = axes[0, 0]
pred_counts = results_pd['predicted_class'].value_counts()
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
bars = ax1.bar(pred_counts.index, pred_counts.values, color=colors[:len(pred_counts)])
ax1.set_title('📊 Distribuição das Predições')
ax1.set_ylabel('Número de Amostras')
for bar, count in zip(bars, pred_counts.values):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{count}\n({count/len(results_pd)*100:.1f}%)',
             ha='center', va='bottom')

# 2. Boxplot das Features por Classe Predita
ax2 = axes[0, 1]
feature_data = [results_pd[results_pd['predicted_class'] == cls]['sepal_length_cm'].values 
                for cls in class_names if cls in results_pd['predicted_class'].values]
class_labels = [cls for cls in class_names if cls in results_pd['predicted_class'].values]
bp = ax2.boxplot(feature_data, labels=class_labels, patch_artist=True)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
ax2.set_title('📦 Sepal Length por Classe')
ax2.set_ylabel('Sepal Length (cm)')

# 3. Scatter plot 2D
ax3 = axes[0, 2]
for i, cls in enumerate(class_names):
    if cls in results_pd['predicted_class'].values:
        mask = results_pd['predicted_class'] == cls
        ax3.scatter(results_pd.loc[mask, 'sepal_length_cm'], 
                   results_pd.loc[mask, 'sepal_width_cm'], 
                   c=colors[i], label=cls, alpha=0.6, s=30)
ax3.set_xlabel('Sepal Length (cm)')
ax3.set_ylabel('Sepal Width (cm)')
ax3.set_title('🌐 Sepal Length vs Width')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Distribuição das Features
ax4 = axes[1, 0]
features = ['sepal_length_cm', 'sepal_width_cm', 'petal_length_cm', 'petal_width_cm']
ax4.hist([results_pd[feat] for feat in features], 
         bins=15, alpha=0.7, label=features, color=colors)
ax4.set_title('📊 Distribuição das Features')
ax4.set_xlabel('Valor')
ax4.set_ylabel('Frequência')
ax4.legend()

# 5. Heatmap de Correlação
ax5 = axes[1, 1]
corr_matrix = results_pd[features].corr()
im = ax5.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
ax5.set_xticks(range(len(features)))
ax5.set_yticks(range(len(features)))
ax5.set_xticklabels([f.replace('_', '\n') for f in features], rotation=45, ha='right')
ax5.set_yticklabels([f.replace('_', '\n') for f in features])
ax5.set_title('🔥 Correlação entre Features')

for i in range(len(features)):
    for j in range(len(features)):
        text = ax5.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                       ha="center", va="center", color="black", fontsize=8)

# 6. Estatísticas por Classe
ax6 = axes[1, 2]
class_stats = results_pd.groupby('predicted_class')[features].mean()
class_stats.plot(kind='bar', ax=ax6, color=colors[:len(class_stats)])
ax6.set_title('📈 Médias das Features por Classe')
ax6.set_ylabel('Valor Médio')
ax6.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax6.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()

print("✅ Visualizações geradas com sucesso!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Salvamento dos Resultados

# COMMAND ----------

print("💾 Salvando resultados da inferência no Unity Catalog...")

try:
    # Salvar como Delta Table
    results_table_name = f"workspace.default.iris_mlflow_inference_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    inference_with_predictions.write \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(results_table_name)
    
    print(f"✅ Resultados salvos em: {results_table_name}")
    print(f"📊 Total de registros salvos: {inference_with_predictions.count()}")
    
    # Mostrar uma amostra dos resultados
    print("\n📊 Amostra dos resultados de inferência:")
    inference_with_predictions.select(
        "sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm",
        "predictions", "model_source"
    ).show(5)
    
except Exception as e:
    print(f"⚠️ Erro ao salvar na tabela Delta: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Relatório Final

# COMMAND ----------

print("\n" + "="*70)
print("🔮 RELATÓRIO DE INFERÊNCIA - IRIS CLASSIFIER COM MLFLOW")
print("="*70)
print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🎯 Modelo: {MODEL_NAME}")
print(f"🔗 Fonte: MLflow Registry/Run")
print(f"📦 Model URI: {logged_model}")
print(f"📊 Total de amostras processadas: {len(results_pd)}")

print("\n📊 DISTRIBUIÇÃO POR CLASSE:")
for cls in class_names:
    if cls in results_pd['predicted_class'].values:
        count = len(results_pd[results_pd['predicted_class'] == cls])
        percentage = count / len(results_pd) * 100
        print(f"  {cls}: {count} amostras ({percentage:.1f}%)")

print("\n📈 ESTATÍSTICAS DAS FEATURES:")
feature_stats = results_pd[features].describe()
print(feature_stats)

print(f"\n✅ Modelo MLflow utilizado com sucesso!")
print(f"🔗 Model URI: {logged_model}")

print("\n🎉 Job de inferência MLflow concluído com sucesso!")
print(f"📅 Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
