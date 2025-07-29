# Databricks notebook source
# MAGIC %md
# MAGIC # 🤖 AutoML - Automated Model Selection
# MAGIC 
# MAGIC Este notebook implementa AutoML para seleção automática de modelos,
# MAGIC comparando múltiplos algoritmos e escolhendo o melhor performer.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
from pyspark.sql import functions as F
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Carregamento de Dados

# COMMAND ----------

# Carregar dados da Feature Store
feature_table = "main.default.iris_features_selected"
data_df = spark.table(feature_table)

print(f"📊 Dataset loaded: {data_df.count()} registros")
print(f"📊 Features disponíveis: {len(data_df.columns)} colunas")

# Converter para Pandas para sklearn
pandas_df = data_df.toPandas()

# Preparar features e target
feature_columns = [col for col in pandas_df.columns if col not in ['iris_id', 'species', 'feature_timestamp']]
X = pandas_df[feature_columns]
y = pandas_df['species']

print(f"🎯 Features para treinamento: {len(feature_columns)}")
print(f"📊 Classes: {y.nunique()} ({list(y.unique())})")
print(f"📦 Shape do dataset: {X.shape}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏗️ Configuração do AutoML

# COMMAND ----------

class AutoMLPipeline:
    """
    Pipeline AutoML para seleção automática de modelos
    """
    
    def __init__(self, cv_folds=5, random_state=42):
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.results = {}
        self.best_model = None
        self.best_score = 0
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Definir modelos para comparação
        self.models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=random_state
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=random_state
            ),
            'SVM': SVC(
                kernel='rbf',
                random_state=random_state
            ),
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                random_state=random_state
            ),
            'K-Nearest Neighbors': KNeighborsClassifier(
                n_neighbors=5
            ),
            'Naive Bayes': GaussianNB()
        }
    
    def evaluate_model(self, model, X, y, model_name):
        """
        Avalia um modelo usando cross-validation
        """
        print(f"🔄 Avaliando {model_name}...")
        
        # Cross-validation scores
        cv_scores = cross_val_score(
            model, X, y, 
            cv=StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state),
            scoring='accuracy'
        )
        
        # Calcular métricas
        mean_score = cv_scores.mean()
        std_score = cv_scores.std()
        
        # Treinar modelo completo para métricas detalhadas
        model.fit(X, y)
        y_pred = model.predict(X)
        
        # Métricas detalhadas
        precision = precision_score(y, y_pred, average='weighted')
        recall = recall_score(y, y_pred, average='weighted')
        f1 = f1_score(y, y_pred, average='weighted')
        
        results = {
            'model': model,
            'cv_mean': mean_score,
            'cv_std': std_score,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cv_scores': cv_scores.tolist()
        }
        
        print(f"  ✅ Accuracy: {mean_score:.4f} (±{std_score:.4f})")
        
        return results
    
    def run_automl(self, X, y):
        """
        Executa o pipeline AutoML completo
        """
        print("🤖 Iniciando AutoML Pipeline...")
        print(f"📊 Dataset: {X.shape[0]} amostras, {X.shape[1]} features")
        
        # Preprocessamento
        print("🔧 Preprocessando dados...")
        X_scaled = self.scaler.fit_transform(X)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Avaliar todos os modelos
        print("\n🔍 Avaliando modelos...")
        for model_name, model in self.models.items():
            try:
                results = self.evaluate_model(model, X_scaled, y_encoded, model_name)
                self.results[model_name] = results
                
                # Atualizar melhor modelo
                if results['cv_mean'] > self.best_score:
                    self.best_score = results['cv_mean']
                    self.best_model = model_name
                    
            except Exception as e:
                print(f"  ❌ Erro em {model_name}: {str(e)}")
        
        print(f"\n🏆 Melhor modelo: {self.best_model} (Score: {self.best_score:.4f})")
        
        return self.results
    
    def get_model_comparison(self):
        """
        Retorna comparação detalhada dos modelos
        """
        comparison_data = []
        for model_name, results in self.results.items():
            comparison_data.append({
                'Model': model_name,
                'CV_Mean': results['cv_mean'],
                'CV_Std': results['cv_std'],
                'Precision': results['precision'],
                'Recall': results['recall'],
                'F1_Score': results['f1_score']
            })
        
        return pd.DataFrame(comparison_data).sort_values('CV_Mean', ascending=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚀 Execução do AutoML

# COMMAND ----------

# Inicializar e executar AutoML
automl = AutoMLPipeline(cv_folds=5, random_state=42)
results = automl.run_automl(X, y)

# Obter comparação de modelos
comparison_df = automl.get_model_comparison()
print("\n📊 COMPARAÇÃO DE MODELOS")
print("=" * 60)
print(comparison_df.round(4))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📈 Visualização dos Resultados

# COMMAND ----------

# Criar visualizações dos resultados
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. Accuracy comparison
ax1 = axes[0, 0]
models = comparison_df['Model']
scores = comparison_df['CV_Mean']
errors = comparison_df['CV_Std']

bars = ax1.bar(range(len(models)), scores, yerr=errors, capsize=5, 
               color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
ax1.set_xlabel('Models')
ax1.set_ylabel('Accuracy')
ax1.set_title('Model Comparison - Cross-Validation Accuracy')
ax1.set_xticks(range(len(models)))
ax1.set_xticklabels(models, rotation=45, ha='right')
ax1.grid(True, alpha=0.3)

# Adicionar valores nas barras
for i, (score, error) in enumerate(zip(scores, errors)):
    ax1.text(i, score + error + 0.01, f'{score:.3f}', ha='center', va='bottom')

# 2. Precision vs Recall
ax2 = axes[0, 1]
ax2.scatter(comparison_df['Precision'], comparison_df['Recall'], 
           s=100, alpha=0.7, c=range(len(comparison_df)))
for i, model in enumerate(comparison_df['Model']):
    ax2.annotate(model, (comparison_df.iloc[i]['Precision'], comparison_df.iloc[i]['Recall']),
                xytext=(5, 5), textcoords='offset points', fontsize=9)
ax2.set_xlabel('Precision')
ax2.set_ylabel('Recall')
ax2.set_title('Precision vs Recall')
ax2.grid(True, alpha=0.3)

# 3. F1-Score comparison
ax3 = axes[1, 0]
f1_scores = comparison_df['F1_Score']
bars = ax3.barh(range(len(models)), f1_scores, 
                color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
ax3.set_ylabel('Models')
ax3.set_xlabel('F1-Score')
ax3.set_title('F1-Score Comparison')
ax3.set_yticks(range(len(models)))
ax3.set_yticklabels(models)
ax3.grid(True, alpha=0.3)

# Adicionar valores nas barras
for i, score in enumerate(f1_scores):
    ax3.text(score + 0.01, i, f'{score:.3f}', va='center', ha='left')

# 4. CV Scores distribution
ax4 = axes[1, 1]
cv_data = []
model_labels = []
for model_name, results in automl.results.items():
    cv_data.extend(results['cv_scores'])
    model_labels.extend([model_name] * len(results['cv_scores']))

cv_df = pd.DataFrame({'Model': model_labels, 'CV_Score': cv_data})
sns.boxplot(data=cv_df, x='Model', y='CV_Score', ax=ax4)
ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right')
ax4.set_title('Cross-Validation Score Distribution')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/tmp/automl_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print("📊 Visualizações salvas em /tmp/automl_comparison.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏆 Seleção do Melhor Modelo

# COMMAND ----------

# Obter o melhor modelo
best_model_name = automl.best_model
best_model_results = automl.results[best_model_name]
best_model = best_model_results['model']

print(f"🏆 MELHOR MODELO SELECIONADO: {best_model_name}")
print("=" * 50)
print(f"📊 Accuracy: {best_model_results['cv_mean']:.4f} (±{best_model_results['cv_std']:.4f})")
print(f"📊 Precision: {best_model_results['precision']:.4f}")
print(f"📊 Recall: {best_model_results['recall']:.4f}")
print(f"📊 F1-Score: {best_model_results['f1_score']:.4f}")

# Treinar modelo final
print("\n🔧 Treinando modelo final...")
X_scaled = automl.scaler.fit_transform(X)
y_encoded = automl.label_encoder.fit_transform(y)
best_model.fit(X_scaled, y_encoded)

# Predições finais
y_pred = best_model.predict(X_scaled)
y_pred_labels = automl.label_encoder.inverse_transform(y_pred)

# Relatório de classificação
print("\n📋 Classification Report:")
print(classification_report(y, y_pred_labels))

# Matriz de confusão
print("\n📊 Confusion Matrix:")
cm = confusion_matrix(y, y_pred_labels)
print(cm)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 💾 Registrar Modelos no MLflow

# COMMAND ----------

# Registrar todos os modelos no MLflow
experiment_name = "/iris_automl_experiment"
mlflow.set_experiment(experiment_name)

print("📈 Registrando modelos no MLflow...")

# Registrar cada modelo
for model_name, results in automl.results.items():
    with mlflow.start_run(run_name=f"automl_{model_name.lower().replace(' ', '_')}") as run:
        
        # Log parâmetros do modelo
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("cv_folds", automl.cv_folds)
        mlflow.log_param("feature_count", X.shape[1])
        mlflow.log_param("sample_count", X.shape[0])
        
        # Log métricas
        mlflow.log_metric("cv_accuracy_mean", results['cv_mean'])
        mlflow.log_metric("cv_accuracy_std", results['cv_std'])
        mlflow.log_metric("precision", results['precision'])
        mlflow.log_metric("recall", results['recall'])
        mlflow.log_metric("f1_score", results['f1_score'])
        
        # Log scores individuais de CV
        for i, score in enumerate(results['cv_scores']):
            mlflow.log_metric(f"cv_fold_{i+1}", score)
        
        # Log modelo
        mlflow.sklearn.log_model(
            results['model'], 
            "model",
            registered_model_name=f"iris_automl_{model_name.lower().replace(' ', '_')}"
        )
        
        # Marcar o melhor modelo
        if model_name == best_model_name:
            mlflow.set_tag("best_model", "true")
            mlflow.set_tag("model_stage", "champion")
        
        print(f"  ✅ {model_name} registrado (Run ID: {run.info.run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏆 Registrar Modelo Campeão

# COMMAND ----------

# Registrar o modelo campeão com metadados especiais
with mlflow.start_run(run_name="iris_automl_champion") as champion_run:
    
    # Log informações do AutoML
    mlflow.log_param("automl_pipeline", "iris_feature_store_automl")
    mlflow.log_param("best_model", best_model_name)
    mlflow.log_param("models_compared", len(automl.results))
    mlflow.log_param("selection_criteria", "cv_accuracy")
    
    # Log métricas do campeão
    mlflow.log_metric("champion_accuracy", best_model_results['cv_mean'])
    mlflow.log_metric("champion_precision", best_model_results['precision'])
    mlflow.log_metric("champion_recall", best_model_results['recall'])
    mlflow.log_metric("champion_f1", best_model_results['f1_score'])
    
    # Log comparação de modelos
    comparison_df.to_csv('/tmp/model_comparison.csv', index=False)
    mlflow.log_artifact('/tmp/model_comparison.csv')
    
    # Log visualizações
    mlflow.log_artifact('/tmp/automl_comparison.png')
    
    # Log modelo campeão
    mlflow.sklearn.log_model(
        best_model,
        "champion_model",
        registered_model_name="iris_automl_champion",
        signature=mlflow.models.infer_signature(X_scaled, y_pred)
    )
    
    # Log preprocessors
    import pickle
    with open('/tmp/scaler.pkl', 'wb') as f:
        pickle.dump(automl.scaler, f)
    with open('/tmp/label_encoder.pkl', 'wb') as f:
        pickle.dump(automl.label_encoder, f)
    
    mlflow.log_artifact('/tmp/scaler.pkl')
    mlflow.log_artifact('/tmp/label_encoder.pkl')
    
    # Tags especiais
    mlflow.set_tag("model_type", "automl_champion")
    mlflow.set_tag("deployment_ready", "true")
    mlflow.set_tag("feature_store_version", "v1.0")

print(f"🏆 Modelo campeão registrado (Run ID: {champion_run.info.run_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 AutoML Summary Report

# COMMAND ----------

# Criar relatório final do AutoML
automl_summary = {
    'timestamp': pd.Timestamp.now(),
    'total_models_evaluated': len(automl.results),
    'best_model': best_model_name,
    'best_accuracy': best_model_results['cv_mean'],
    'feature_count': X.shape[1],
    'sample_count': X.shape[0],
    'cv_folds': automl.cv_folds,
    'model_rankings': comparison_df.to_dict('records')
}

print("🤖 AUTOML SUMMARY REPORT")
print("=" * 50)
print(f"🕒 Timestamp: {automl_summary['timestamp']}")
print(f"🔍 Models Evaluated: {automl_summary['total_models_evaluated']}")
print(f"🏆 Best Model: {automl_summary['best_model']}")
print(f"📊 Best Accuracy: {automl_summary['best_accuracy']:.4f}")
print(f"📦 Features Used: {automl_summary['feature_count']}")
print(f"📊 Training Samples: {automl_summary['sample_count']}")

print(f"\n🥇 TOP 3 MODELS:")
top_3 = comparison_df.head(3)
for i, (_, row) in enumerate(top_3.iterrows(), 1):
    print(f"  {i}. {row['Model']}: {row['CV_Mean']:.4f} accuracy")

print(f"\n📈 Model Performance Summary:")
print(f"  - Best Accuracy: {comparison_df['CV_Mean'].max():.4f}")
print(f"  - Worst Accuracy: {comparison_df['CV_Mean'].min():.4f}")
print(f"  - Average Accuracy: {comparison_df['CV_Mean'].mean():.4f}")
print(f"  - Std Dev: {comparison_df['CV_Mean'].std():.4f}")

# Salvar summary
summary_df = spark.createDataFrame([{
    'timestamp': automl_summary['timestamp'],
    'best_model': automl_summary['best_model'],
    'best_accuracy': automl_summary['best_accuracy'],
    'models_evaluated': automl_summary['total_models_evaluated'],
    'feature_count': automl_summary['feature_count'],
    'mlflow_run_id': champion_run.info.run_id
}])

automl_table = "main.default.automl_results"
summary_df.write.mode("append").saveAsTable(automl_table)
print(f"\n✅ AutoML summary saved to: {automl_table}")

print(f"\n🎯 NEXT STEPS:")
print(f"  1. Deploy champion model to production")
print(f"  2. Set up A/B testing with current model")
print(f"  3. Monitor model performance in production")
print(f"  4. Schedule periodic AutoML runs")
print(f"  5. Update feature store with new features")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚀 Deployment Preparation

# COMMAND ----------

# Preparar modelo para deployment
deployment_info = {
    'model_name': 'iris_automl_champion',
    'model_version': 'latest',
    'mlflow_run_id': champion_run.info.run_id,
    'features_required': feature_columns,
    'preprocessing_required': ['StandardScaler', 'LabelEncoder'],
    'model_type': best_model_name,
    'accuracy': best_model_results['cv_mean'],
    'deployment_ready': True
}

print("🚀 DEPLOYMENT INFORMATION")
print("=" * 40)
for key, value in deployment_info.items():
    print(f"{key}: {value}")

# Salvar informações de deployment
import json
with open('/tmp/deployment_info.json', 'w') as f:
    json.dump(deployment_info, f, indent=2, default=str)

print(f"\n✅ Deployment info saved to /tmp/deployment_info.json")
print(f"📦 Model artifacts available in MLflow run: {champion_run.info.run_id}")
print(f"🔗 Model registry: iris_automl_champion")

print(f"\n🎉 AutoML Pipeline completed successfully!")
print(f"🏆 Champion model: {best_model_name} with {best_model_results['cv_mean']:.4f} accuracy")
