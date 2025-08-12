# Databricks notebook source
# MAGIC %md
# MAGIC # 🔮 Iris Model Inference & Visualization
# MAGIC 
# MAGIC Este notebook:
# MAGIC 1. Carrega um modelo pré-treinado (simulando MLflow)
# MAGIC 2. Faz inferências em novos dados
# MAGIC 3. Visualiza os resultados com gráficos
# MAGIC 4. Calcula métricas de performance

# COMMAND ----------

# Imports necessários
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.datasets import load_iris
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Inicializar Spark session
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("IrisInference").getOrCreate()

# Configurar estilo dos gráficos
plt.style.use('default')
sns.set_palette("husl")

print("🔮 Iniciando job de inferência do modelo Iris...")
print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Parâmetros do Job

# COMMAND ----------

# Parâmetros para inferência
MODEL_NAME = "iris_classifier"
MODEL_STAGE = "Production"
NUM_SAMPLES = 100

print(f"🎯 Modelo: {MODEL_NAME}")
print(f"🏷️ Stage: {MODEL_STAGE}")
print(f"📊 Amostras: {NUM_SAMPLES}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Carregamento do Modelo Pré-treinado

# COMMAND ----------

print("🔍 Carregando modelo pré-treinado...")

# Simular carregamento de modelo do MLflow Registry
# Em produção real, isso seria:
# model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")

# Por agora, vamos carregar um modelo de referência
iris_data = load_iris()
X = iris_data.data
y = iris_data.target
feature_names = iris_data.feature_names
target_names = iris_data.target_names

# Usar dados de treino fixos para consistência
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Carregar modelo pré-treinado (simulando MLflow)
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42
)

model.fit(X_train, y_train)

# Validar modelo
test_predictions = model.predict(X_test)
test_accuracy = accuracy_score(y_test, test_predictions)

print(f"✅ Modelo carregado com sucesso!")
print(f"🎯 Acurácia de referência: {test_accuracy:.3f}")
print(f"📊 Features: {feature_names}")
print(f"🏷️ Classes: {target_names}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Geração de Dados para Inferência

# COMMAND ----------

print(f"🎲 Gerando {NUM_SAMPLES} amostras sintéticas para inferência...")

# Gerar dados sintéticos baseados nas estatísticas do dataset original
np.random.seed(42)

# Calcular estatísticas dos dados originais
means = np.mean(X, axis=0)
stds = np.std(X, axis=0)

# Gerar amostras sintéticas com variação
synthetic_data = []
for i in range(NUM_SAMPLES):
    sample = []
    for j in range(len(feature_names)):
        # Adicionar variação aleatória às médias
        value = np.random.normal(means[j], stds[j] * 0.5)
        # Garantir valores positivos para características físicas
        value = max(0.1, value)
        sample.append(value)
    synthetic_data.append(sample)

synthetic_data = np.array(synthetic_data)

print(f"✅ Dados sintéticos gerados!")
print(f"📊 Shape: {synthetic_data.shape}")
print(f"📈 Range das features:")
for i, feature in enumerate(feature_names):
    print(f"  {feature}: {synthetic_data[:, i].min():.2f} - {synthetic_data[:, i].max():.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔮 Execução da Inferência

# COMMAND ----------

print("🚀 Executando inferência no modelo...")

# Fazer predições
predictions = model.predict(synthetic_data)
prediction_probas = model.predict_proba(synthetic_data)

# Obter nomes das classes preditas
predicted_classes = [target_names[pred] for pred in predictions]

# Calcular confiança (probabilidade máxima)
confidence_scores = np.max(prediction_probas, axis=1)

print(f"✅ Inferência concluída!")
print(f"📊 Distribuição das predições:")
unique, counts = np.unique(predictions, return_counts=True)
for i, (cls_idx, count) in enumerate(zip(unique, counts)):
    print(f"  {target_names[cls_idx]}: {count} amostras ({count/len(predictions)*100:.1f}%)")

print(f"🎯 Confiança média: {np.mean(confidence_scores):.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Visualizações dos Resultados

# COMMAND ----------

print("📈 Gerando visualizações...")

# Configurar plots
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('🔮 Iris Model Inference - Análise dos Resultados', fontsize=16, fontweight='bold')

# 1. Distribuição das Predições
ax1 = axes[0, 0]
unique, counts = np.unique(predicted_classes, return_counts=True)
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
bars = ax1.bar(unique, counts, color=colors[:len(unique)])
ax1.set_title('📊 Distribuição das Predições')
ax1.set_ylabel('Número de Amostras')
for bar, count in zip(bars, counts):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{count}\n({count/len(predictions)*100:.1f}%)',
             ha='center', va='bottom')

# 2. Distribuição da Confiança
ax2 = axes[0, 1]
ax2.hist(confidence_scores, bins=20, alpha=0.7, color='#95A5A6', edgecolor='black')
ax2.set_title('🎯 Distribuição da Confiança')
ax2.set_xlabel('Score de Confiança')
ax2.set_ylabel('Frequência')
ax2.axvline(np.mean(confidence_scores), color='red', linestyle='--', 
            label=f'Média: {np.mean(confidence_scores):.3f}')
ax2.legend()

# 3. Boxplot das Features por Classe Predita
ax3 = axes[0, 2]
# Usar primeira feature para demonstração
feature_idx = 0
data_by_class = [synthetic_data[predictions == i, feature_idx] for i in range(len(target_names))]
bp = ax3.boxplot(data_by_class, labels=target_names, patch_artist=True)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
ax3.set_title(f'📦 {feature_names[feature_idx]} por Classe')
ax3.set_ylabel(feature_names[feature_idx])

# 4. Scatter plot 2D das primeiras duas features
ax4 = axes[1, 0]
for i, target_name in enumerate(target_names):
    mask = predictions == i
    if np.any(mask):
        ax4.scatter(synthetic_data[mask, 0], synthetic_data[mask, 1], 
                   c=colors[i], label=target_name, alpha=0.6, s=30)
ax4.set_xlabel(feature_names[0])
ax4.set_ylabel(feature_names[1])
ax4.set_title('🌐 Scatter Plot: Features 1 vs 2')
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. Heatmap de Correlação das Features
ax5 = axes[1, 1]
correlation_matrix = np.corrcoef(synthetic_data.T)
im = ax5.imshow(correlation_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
ax5.set_xticks(range(len(feature_names)))
ax5.set_yticks(range(len(feature_names)))
ax5.set_xticklabels([name.replace(' ', '\n') for name in feature_names], rotation=45, ha='right')
ax5.set_yticklabels([name.replace(' ', '\n') for name in feature_names])
ax5.set_title('🔥 Correlação entre Features')

# Adicionar valores na heatmap
for i in range(len(feature_names)):
    for j in range(len(feature_names)):
        text = ax5.text(j, i, f'{correlation_matrix[i, j]:.2f}',
                       ha="center", va="center", color="black", fontsize=8)

# 6. Feature Importance
ax6 = axes[1, 2]
importances = model.feature_importances_
feature_importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances
}).sort_values('importance', ascending=True)

bars = ax6.barh(feature_importance_df['feature'], feature_importance_df['importance'])
ax6.set_title('⭐ Importância das Features')
ax6.set_xlabel('Importância')

# Colorir barras
for i, bar in enumerate(bars):
    bar.set_color(colors[i % len(colors)])

plt.tight_layout()
plt.show()

print("✅ Visualizações geradas com sucesso!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Relatório de Resultados

# COMMAND ----------

print("📋 Gerando relatório detalhado...")

# Criar DataFrame com resultados
inference_data = pd.DataFrame(synthetic_data, columns=feature_names)
inference_data['predicted_class'] = predicted_classes
inference_data['predicted_class_idx'] = predictions
inference_data['confidence'] = confidence_scores
inference_data['inference_timestamp'] = datetime.now()
inference_data['model_name'] = MODEL_NAME
inference_data['model_version'] = '1.0'

# Estatísticas gerais
print("\n" + "="*60)
print("📊 RELATÓRIO DE INFERÊNCIA - IRIS CLASSIFIER")
print("="*60)
print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🎯 Modelo: {MODEL_NAME}")
print(f"📊 Total de amostras processadas: {len(inference_data)}")
print(f"🎯 Confiança média: {np.mean(confidence_scores):.3f}")
print(f"🎯 Confiança mínima: {np.min(confidence_scores):.3f}")
print(f"🎯 Confiança máxima: {np.max(confidence_scores):.3f}")

print("\n📊 DISTRIBUIÇÃO POR CLASSE:")
for i, target_name in enumerate(target_names):
    count = sum(predictions == i)
    percentage = count / len(predictions) * 100
    avg_confidence = np.mean(confidence_scores[predictions == i]) if count > 0 else 0
    print(f"  {target_name}: {count} amostras ({percentage:.1f}%) - Confiança média: {avg_confidence:.3f}")

print("\n📈 ESTATÍSTICAS DAS FEATURES:")
for feature in feature_names:
    values = inference_data[feature]
    print(f"  {feature}:")
    print(f"    Média: {np.mean(values):.3f}")
    print(f"    Desvio padrão: {np.std(values):.3f}")
    print(f"    Min: {np.min(values):.3f}")
    print(f"    Max: {np.max(values):.3f}")

# Amostras com maior e menor confiança
print("\n🎯 AMOSTRAS COM MAIOR CONFIANÇA:")
top_confident = inference_data.nlargest(3, 'confidence')
for idx, row in top_confident.iterrows():
    print(f"  Amostra {idx}: {row['predicted_class']} (confiança: {row['confidence']:.3f})")

print("\n⚠️ AMOSTRAS COM MENOR CONFIANÇA:")
low_confident = inference_data.nsmallest(3, 'confidence')
for idx, row in low_confident.iterrows():
    print(f"  Amostra {idx}: {row['predicted_class']} (confiança: {row['confidence']:.3f})")

print("\n" + "="*60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Salvamento dos Resultados

# COMMAND ----------

print("💾 Salvando resultados da inferência...")

# Converter para Spark DataFrame e salvar
spark_df = spark.createDataFrame(inference_data)

try:
    # Salvar como Delta Table
    results_table_name = f"workspace.default.iris_inference_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    spark_df.write \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(results_table_name)
    
    print(f"✅ Resultados salvos em: {results_table_name}")
    print(f"📊 Total de registros salvos: {len(inference_data)}")
    
except Exception as e:
    print(f"⚠️ Erro ao salvar na tabela Delta: {e}")
    print("💾 Salvando em tabela alternativa...")
    
    # Fallback: usar formato simplificado para Unity Catalog
    fallback_table = f"workspace.default.iris_inference_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    spark_df.write.mode("overwrite").saveAsTable(fallback_table)
    print(f"✅ Resultados salvos em tabela alternativa: {fallback_table}")

# Mostrar uma amostra dos resultados
print("\n📊 Amostra dos resultados de inferência:")
spark_df.show(5)

print("\n🎉 Job de inferência concluído com sucesso!")
print(f"📅 Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📞 Monitoramento e Alertas
# MAGIC 
# MAGIC Em produção, aqui adicionaríamos:
# MAGIC - Métricas de drift dos dados
# MAGIC - Alertas para baixa confiança
# MAGIC - Logs de auditoria
# MAGIC - Notificações por email
