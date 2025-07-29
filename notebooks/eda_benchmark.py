# Databricks notebook source
# MAGIC %md
# MAGIC # 📊 EDA & Benchmark - Feature Store Analysis
# MAGIC 
# MAGIC Este notebook realiza análise exploratória das features do Feature Store
# MAGIC e executa benchmark de múltiplos modelos de Machine Learning.

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
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("✅ Bibliotecas importadas com sucesso!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Carregamento dos Dados da Feature Store

# COMMAND ----------

# Carregar dados da Feature Store
feature_table_name = "iris_features"  # Tabela criada pelo Feature Store

try:
    features_df = spark.table(feature_table_name)
    print(f"✅ Feature Store carregada: {feature_table_name}")
    print(f"📊 Total de registros: {features_df.count()}")
    print(f"📊 Total de features: {len(features_df.columns)}")
    
    # Mostrar schema
    print("\n📋 Schema das Features:")
    features_df.printSchema()
    
    # Converter para Pandas para análises
    features_pdf = features_df.toPandas()
    print(f"✅ Dados convertidos para Pandas: {features_pdf.shape}")
    
except Exception as e:
    print(f"❌ Erro ao carregar Feature Store: {str(e)}")
    raise notebook source
# MAGIC %md
# MAGIC # 📊 EDA & Model Benchmark - Feature Store Analysis
# MAGIC 
# MAGIC Este notebook realiza Análise Exploratória de Dados (EDA) das features da Feature Store
# MAGIC e executa um benchmark completo de modelos de Machine Learning.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📦 Imports e Configurações

# COMMAND ----------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

# Scikit-learn imports
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA

# Warnings
import warnings
warnings.filterwarnings('ignore')

print("✅ Bibliotecas importadas com sucesso!")
print(f"🕒 Timestamp: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Carregamento da Feature Store

# COMMAND ----------

# Configuração da Feature Store
feature_table_name = "iris_features"
print(f"🏪 Carregando dados da Feature Store: {feature_table_name}")

try:
    # Carregar dados da Feature Store
    features_df = spark.table(feature_table_name)
    print(f"✅ Feature Store carregada: {features_df.count()} registros")
    
    # Converter para Pandas para análise
    features_pdf = features_df.toPandas()
    print(f"📊 Dados convertidos para Pandas: {features_pdf.shape}")
    
    # Informações básicas
    print("\n📋 Informações do Dataset:")
    print(f"   Registros: {len(features_pdf)}")
    print(f"   Features: {len(features_pdf.columns)}")
    print(f"   Memória: {features_pdf.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
except Exception as e:
    print(f"❌ Erro ao carregar Feature Store: {str(e)}")
    print("🔄 Verificando tabelas disponíveis...")
    
    # Listar tabelas disponíveis
    available_tables = spark.sql("SHOW TABLES").collect()
    print("📋 Tabelas disponíveis:")
    for table in available_tables:
        print(f"   - {table.tableName}")
    
    # Usar fallback se necessário
    raise Exception("Feature Store não encontrada")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Análise Exploratória de Dados (EDA)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Visão Geral do Dataset

# COMMAND ----------

print("🔍 ANÁLISE EXPLORATÓRIA DE DADOS")
print("=" * 50)

# Informações gerais
print(f"\n📊 Shape do dataset: {features_pdf.shape}")
print(f"📊 Tipos de dados:")
print(features_pdf.dtypes.value_counts())

# Estatísticas descritivas
print(f"\n📈 Estatísticas Descritivas:")
display(features_pdf.describe())

# Verificar valores ausentes
print(f"\n🔍 Valores Ausentes:")
missing_values = features_pdf.isnull().sum()
missing_percent = (missing_values / len(features_pdf)) * 100
missing_df = pd.DataFrame({
    'Coluna': missing_values.index,
    'Valores Ausentes': missing_values.values,
    'Percentual': missing_percent.values
}).sort_values('Valores Ausentes', ascending=False)

print(missing_df[missing_df['Valores Ausentes'] > 0])

if missing_df['Valores Ausentes'].sum() == 0:
    print("✅ Nenhum valor ausente encontrado!")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Análise de Features Numéricas

# COMMAND ----------

# Identificar features numéricas (excluindo ID e target)
numeric_features = features_pdf.select_dtypes(include=[np.number]).columns.tolist()
exclude_cols = ['iris_id', 'feature_timestamp']
numeric_features = [col for col in numeric_features if col not in exclude_cols]

print(f"📊 Features Numéricas Identificadas ({len(numeric_features)}):")
for i, feature in enumerate(numeric_features, 1):
    print(f"   {i:2d}. {feature}")

# Criar visualizações das features numéricas
plt.figure(figsize=(20, 15))

# Histogramas
for i, feature in enumerate(numeric_features[:16], 1):  # Limitar a 16 para não sobrecarregar
    plt.subplot(4, 4, i)
    plt.hist(features_pdf[feature], bins=20, alpha=0.7, edgecolor='black')
    plt.title(f'Distribuição: {feature}')
    plt.xlabel(feature)
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# COMMAND ----------

# Matriz de correlação das features numéricas
plt.figure(figsize=(16, 12))

# Calcular matriz de correlação
correlation_matrix = features_pdf[numeric_features].corr()

# Heatmap
sns.heatmap(correlation_matrix, 
            annot=True, 
            cmap='coolwarm', 
            center=0,
            square=True,
            fmt='.2f',
            cbar_kws={"shrink": .8})

plt.title('Matriz de Correlação - Features Numéricas', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Identificar correlações altas
print("\n🔍 Correlações Altas (|r| > 0.8):")
high_corr_pairs = []
for i in range(len(correlation_matrix.columns)):
    for j in range(i+1, len(correlation_matrix.columns)):
        corr_value = correlation_matrix.iloc[i, j]
        if abs(corr_value) > 0.8:
            high_corr_pairs.append((correlation_matrix.columns[i], 
                                  correlation_matrix.columns[j], 
                                  corr_value))

if high_corr_pairs:
    for feat1, feat2, corr in high_corr_pairs:
        print(f"   {feat1} ↔ {feat2}: {corr:.3f}")
else:
    print("   ✅ Nenhuma correlação alta encontrada")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🏷️ Análise da Variável Target

# COMMAND ----------

# Analisar a variável target (species)
target_col = 'species'

if target_col in features_pdf.columns:
    print("🏷️ ANÁLISE DA VARIÁVEL TARGET")
    print("=" * 40)
    
    # Distribuição das classes
    class_counts = features_pdf[target_col].value_counts()
    print(f"\n📊 Distribuição das Classes:")
    for class_name, count in class_counts.items():
        percentage = (count / len(features_pdf)) * 100
        print(f"   {class_name}: {count} ({percentage:.1f}%)")
    
    # Verificar balanceamento
    balance_ratio = class_counts.max() / class_counts.min()
    print(f"\n⚖️ Razão de Balanceamento: {balance_ratio:.2f}")
    if balance_ratio <= 1.5:
        print("✅ Dataset bem balanceado")
    elif balance_ratio <= 3.0:
        print("⚠️ Dataset moderadamente desbalanceado")
    else:
        print("❌ Dataset muito desbalanceado")
    
    # Visualização da distribuição
    plt.figure(figsize=(12, 5))
    
    # Gráfico de barras
    plt.subplot(1, 2, 1)
    class_counts.plot(kind='bar', color=['skyblue', 'lightgreen', 'salmon'])
    plt.title('Distribuição das Classes')
    plt.xlabel('Espécies')
    plt.ylabel('Contagem')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # Gráfico de pizza
    plt.subplot(1, 2, 2)
    plt.pie(class_counts.values, labels=class_counts.index, autopct='%1.1f%%', 
            colors=['skyblue', 'lightgreen', 'salmon'])
    plt.title('Proporção das Classes')
    
    plt.tight_layout()
    plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Análise de Features por Classe

# COMMAND ----------

# Análise das features por classe
if target_col in features_pdf.columns:
    print("📊 ANÁLISE DAS FEATURES POR CLASSE")
    print("=" * 40)
    
    # Estatísticas por classe
    print("\n📈 Médias por Classe:")
    class_means = features_pdf.groupby(target_col)[numeric_features[:8]].mean()  # Primeiras 8 features
    display(class_means)
    
    # Visualização: Box plots das principais features
    main_features = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
    
    if all(feat in features_pdf.columns for feat in main_features):
        plt.figure(figsize=(16, 10))
        
        for i, feature in enumerate(main_features, 1):
            plt.subplot(2, 2, i)
            sns.boxplot(data=features_pdf, x=target_col, y=feature, palette='Set2')
            plt.title(f'Distribuição de {feature} por Espécie')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    # Análise de separabilidade das classes
    print("\n🎯 Análise de Separabilidade:")
    separability_scores = {}
    
    for feature in numeric_features[:10]:  # Analisar primeiras 10 features
        try:
            # ANOVA F-statistic como proxy para separabilidade
            from scipy.stats import f_oneway
            groups = [features_pdf[features_pdf[target_col] == cls][feature].values 
                     for cls in features_pdf[target_col].unique()]
            f_stat, p_value = f_oneway(*groups)
            separability_scores[feature] = f_stat
        except:
            separability_scores[feature] = 0
    
    # Ordenar por separabilidade
    sorted_features = sorted(separability_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("🏆 Top 10 Features mais discriminativas:")
    for i, (feature, score) in enumerate(sorted_features[:10], 1):
        print(f"   {i:2d}. {feature}: {score:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🔬 Análise de Componentes Principais (PCA)

# COMMAND ----------

# PCA para visualização
print("🔬 ANÁLISE DE COMPONENTES PRINCIPAIS")
print("=" * 40)

# Preparar dados para PCA
features_for_pca = features_pdf[numeric_features].fillna(0)

# Padronizar os dados
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features_for_pca)

# Aplicar PCA
pca = PCA()
pca_result = pca.fit_transform(features_scaled)

# Variância explicada
explained_variance = pca.explained_variance_ratio_
cumulative_variance = np.cumsum(explained_variance)

print(f"📊 Variância explicada pelos primeiros componentes:")
for i in range(min(10, len(explained_variance))):
    print(f"   PC{i+1}: {explained_variance[i]:.3f} ({cumulative_variance[i]:.3f} acumulado)")

# Visualização da variância explicada
plt.figure(figsize=(15, 5))

# Variância por componente
plt.subplot(1, 3, 1)
plt.bar(range(1, min(21, len(explained_variance)+1)), explained_variance[:20])
plt.title('Variância Explicada por Componente')
plt.xlabel('Componente Principal')
plt.ylabel('Variância Explicada')
plt.grid(True, alpha=0.3)

# Variância acumulada
plt.subplot(1, 3, 2)
plt.plot(range(1, min(21, len(cumulative_variance)+1)), cumulative_variance[:20], 'o-')
plt.axhline(y=0.95, color='r', linestyle='--', label='95% da variância')
plt.title('Variância Acumulada')
plt.xlabel('Número de Componentes')
plt.ylabel('Variância Acumulada')
plt.legend()
plt.grid(True, alpha=0.3)

# Visualização 2D com as duas primeiras componentes
if target_col in features_pdf.columns:
    plt.subplot(1, 3, 3)
    
    # Criar DataFrame com PCA
    pca_df = pd.DataFrame({
        'PC1': pca_result[:, 0],
        'PC2': pca_result[:, 1],
        'species': features_pdf[target_col]
    })
    
    # Scatter plot
    for species in pca_df['species'].unique():
        mask = pca_df['species'] == species
        plt.scatter(pca_df[mask]['PC1'], pca_df[mask]['PC2'], 
                   label=species, alpha=0.7, s=50)
    
    plt.title('Visualização PCA (2D)')
    plt.xlabel(f'PC1 ({explained_variance[0]:.1%} da variância)')
    plt.ylabel(f'PC2 ({explained_variance[1]:.1%} da variância)')
    plt.legend()
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Número de componentes para 95% da variância
n_components_95 = np.argmax(cumulative_variance >= 0.95) + 1
print(f"\n🎯 Componentes necessários para 95% da variância: {n_components_95}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🤖 Benchmark de Modelos de Machine Learning

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🎯 Preparação dos Dados para Modelagem

# COMMAND ----------

print("🤖 BENCHMARK DE MODELOS DE MACHINE LEARNING")
print("=" * 50)

# Preparar dados para modelagem
if target_col in features_pdf.columns:
    
    # Selecionar features para modelagem (excluir ID, timestamp e target)
    feature_cols = [col for col in features_pdf.columns 
                   if col not in ['iris_id', 'feature_timestamp', target_col]]
    
    print(f"📊 Features selecionadas para modelagem ({len(feature_cols)}):")
    for i, feat in enumerate(feature_cols[:15], 1):  # Mostrar primeiras 15
        print(f"   {i:2d}. {feat}")
    if len(feature_cols) > 15:
        print(f"   ... e mais {len(feature_cols) - 15} features")
    
    # Preparar X e y
    X = features_pdf[feature_cols].fillna(0)  # Preencher NAs se houver
    y = features_pdf[target_col]
    
    # Encoding da variável target se necessário
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    print(f"\n📊 Shape dos dados:")
    print(f"   X (features): {X.shape}")
    print(f"   y (target): {y.shape}")
    print(f"   Classes: {list(le.classes_)}")
    
    # Split dos dados
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded
    )
    
    print(f"\n🔄 Split dos dados:")
    print(f"   Treino: {X_train.shape[0]} amostras")
    print(f"   Teste: {X_test.shape[0]} amostras")
    
    # Padronização dos dados
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("✅ Dados preparados para modelagem!")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🏆 Execução do Benchmark

# COMMAND ----------

# Definir modelos para benchmark
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'Extra Trees': ExtraTreesClassifier(n_estimators=100, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', random_state=42),
    'SVM (Linear)': SVC(kernel='linear', random_state=42),
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=5),
    'Naive Bayes': GaussianNB(),
    'Decision Tree': DecisionTreeClassifier(random_state=42),
    'Neural Network': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500)
}

print(f"🏆 EXECUTANDO BENCHMARK COM {len(models)} MODELOS")
print("=" * 60)

# Inicializar MLflow
mlflow.set_experiment("/iris_model_benchmark")

results = []
model_objects = {}

for model_name, model in models.items():
    print(f"\n🔄 Treinando: {model_name}")
    
    with mlflow.start_run(run_name=f"benchmark_{model_name}"):
        try:
            # Treinar modelo
            if 'SVM' in model_name or 'Neural Network' in model_name:
                # Usar dados padronizados para SVM e Neural Network
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                # Cross-validation com dados padronizados
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            else:
                # Usar dados originais para modelos baseados em árvore
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                # Cross-validation com dados originais
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            # Calcular métricas
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Salvar métricas no MLflow
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f1)
            mlflow.log_metric("cv_score_mean", cv_scores.mean())
            mlflow.log_metric("cv_score_std", cv_scores.std())
            
            # Salvar modelo
            mlflow.sklearn.log_model(model, f"model_{model_name.lower().replace(' ', '_')}")
            
            # Armazenar resultados
            results.append({
                'Model': model_name,
                'Accuracy': accuracy,
                'Precision': precision,
                'Recall': recall,
                'F1-Score': f1,
                'CV Score (mean)': cv_scores.mean(),
                'CV Score (std)': cv_scores.std()
            })
            
            model_objects[model_name] = model
            
            print(f"   ✅ Accuracy: {accuracy:.4f}")
            print(f"   📊 CV Score: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            continue

print(f"\n✅ Benchmark concluído! {len(results)} modelos avaliados.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 Resultados do Benchmark

# COMMAND ----------

# Criar DataFrame com resultados
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Accuracy', ascending=False)

print("🏆 RESULTADOS DO BENCHMARK")
print("=" * 50)

# Exibir tabela de resultados
display(results_df)

# Identificar melhor modelo
best_model_name = results_df.iloc[0]['Model']
best_accuracy = results_df.iloc[0]['Accuracy']

print(f"\n🥇 MELHOR MODELO: {best_model_name}")
print(f"📊 Accuracy: {best_accuracy:.4f}")

# Visualizações dos resultados
plt.figure(figsize=(20, 12))

# Gráfico de barras - Accuracy
plt.subplot(2, 3, 1)
bars = plt.bar(range(len(results_df)), results_df['Accuracy'], 
               color=['gold' if i == 0 else 'skyblue' for i in range(len(results_df))])
plt.title('Accuracy por Modelo')
plt.xlabel('Modelos')
plt.ylabel('Accuracy')
plt.xticks(range(len(results_df)), results_df['Model'], rotation=45, ha='right')
plt.grid(True, alpha=0.3)

# Adicionar valores nas barras
for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.005,
             f'{height:.3f}', ha='center', va='bottom', fontsize=9)

# Gráfico de barras - F1-Score
plt.subplot(2, 3, 2)
plt.bar(range(len(results_df)), results_df['F1-Score'], 
        color=['gold' if i == 0 else 'lightgreen' for i in range(len(results_df))])
plt.title('F1-Score por Modelo')
plt.xlabel('Modelos')
plt.ylabel('F1-Score')
plt.xticks(range(len(results_df)), results_df['Model'], rotation=45, ha='right')
plt.grid(True, alpha=0.3)

# Cross-validation scores
plt.subplot(2, 3, 3)
plt.errorbar(range(len(results_df)), results_df['CV Score (mean)'], 
             yerr=results_df['CV Score (std)'], fmt='o', capsize=5)
plt.title('Cross-Validation Scores')
plt.xlabel('Modelos')
plt.ylabel('CV Score')
plt.xticks(range(len(results_df)), results_df['Model'], rotation=45, ha='right')
plt.grid(True, alpha=0.3)

# Heatmap de todas as métricas
plt.subplot(2, 3, 4)
metrics_for_heatmap = results_df[['Accuracy', 'Precision', 'Recall', 'F1-Score']].T
sns.heatmap(metrics_for_heatmap, annot=True, fmt='.3f', cmap='RdYlGn', 
            xticklabels=results_df['Model'], cbar_kws={"shrink": .8})
plt.title('Heatmap de Métricas')
plt.xticks(rotation=45, ha='right')

# Scatter plot: Accuracy vs F1-Score
plt.subplot(2, 3, 5)
plt.scatter(results_df['Accuracy'], results_df['F1-Score'], 
           s=100, alpha=0.7, c=range(len(results_df)), cmap='viridis')
for i, model in enumerate(results_df['Model']):
    plt.annotate(model, (results_df['Accuracy'].iloc[i], results_df['F1-Score'].iloc[i]),
                xytext=(5, 5), textcoords='offset points', fontsize=8)
plt.xlabel('Accuracy')
plt.ylabel('F1-Score')
plt.title('Accuracy vs F1-Score')
plt.grid(True, alpha=0.3)

# Box plot das métricas
plt.subplot(2, 3, 6)
metrics_melted = results_df[['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].melt(
    id_vars=['Model'], var_name='Metric', value_name='Score'
)
sns.boxplot(data=metrics_melted, x='Metric', y='Score')
plt.title('Distribuição das Métricas')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🔍 Análise Detalhada do Melhor Modelo

# COMMAND ----------

# Análise detalhada do melhor modelo
if best_model_name in model_objects:
    best_model = model_objects[best_model_name]
    
    print(f"🔍 ANÁLISE DETALHADA: {best_model_name}")
    print("=" * 50)
    
    # Predições do melhor modelo
    if 'SVM' in best_model_name or 'Neural Network' in best_model_name:
        y_pred_best = best_model.predict(X_test_scaled)
    else:
        y_pred_best = best_model.predict(X_test)
    
    # Relatório de classificação
    print("\n📊 Relatório de Classificação:")
    print(classification_report(y_test, y_pred_best, 
                              target_names=le.classes_))
    
    # Matriz de confusão
    cm = confusion_matrix(y_test, y_pred_best)
    
    plt.figure(figsize=(12, 5))
    
    # Matriz de confusão
    plt.subplot(1, 2, 1)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=le.classes_, yticklabels=le.classes_)
    plt.title(f'Matriz de Confusão - {best_model_name}')
    plt.xlabel('Predição')
    plt.ylabel('Real')
    
    # Feature importance (se disponível)
    plt.subplot(1, 2, 2)
    
    if hasattr(best_model, 'feature_importances_'):
        # Para modelos baseados em árvore
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.bar(range(min(10, len(importances))), importances[indices[:10]])
        plt.title(f'Top 10 Feature Importances - {best_model_name}')
        plt.xlabel('Features')
        plt.ylabel('Importância')
        feature_names = [feature_cols[i] for i in indices[:10]]
        plt.xticks(range(len(feature_names)), feature_names, rotation=45, ha='right')
        
    elif hasattr(best_model, 'coef_'):
        # Para modelos lineares
        if len(best_model.coef_.shape) > 1:
            # Multi-class
            coef_abs = np.abs(best_model.coef_).mean(axis=0)
        else:
            coef_abs = np.abs(best_model.coef_[0])
        
        indices = np.argsort(coef_abs)[::-1]
        plt.bar(range(min(10, len(coef_abs))), coef_abs[indices[:10]])
        plt.title(f'Top 10 Coeficientes - {best_model_name}')
        plt.xlabel('Features')
        plt.ylabel('|Coeficiente|')
        feature_names = [feature_cols[i] for i in indices[:10]]
        plt.xticks(range(len(feature_names)), feature_names, rotation=45, ha='right')
    
    else:
        plt.text(0.5, 0.5, 'Feature importance\nnão disponível\npara este modelo', 
                ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)
        plt.title(f'Feature Importance - {best_model_name}')
    
    plt.tight_layout()
    plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📋 Resumo e Recomendações

# COMMAND ----------

print("📋 RESUMO E RECOMENDAÇÕES")
print("=" * 50)

# Resumo do EDA
print("\n🔍 RESUMO DO EDA:")
print(f"   📊 Dataset: {len(features_pdf)} registros, {len(features_pdf.columns)} features")
print(f"   🏷️ Classes: {len(features_pdf[target_col].unique())} classes balanceadas")
print(f"   📈 Features numéricas: {len(numeric_features)}")
print(f"   🔬 Componentes PCA (95% variância): {n_components_95}")

# Resumo do Benchmark
print(f"\n🏆 RESUMO DO BENCHMARK:")
print(f"   🤖 Modelos testados: {len(results)}")
print(f"   🥇 Melhor modelo: {best_model_name} ({best_accuracy:.4f})")
print(f"   📊 Accuracy média: {results_df['Accuracy'].mean():.4f}")
print(f"   📈 Desvio padrão: {results_df['Accuracy'].std():.4f}")

# Top 3 modelos
print(f"\n🏆 TOP 3 MODELOS:")
for i in range(min(3, len(results_df))):
    model = results_df.iloc[i]
    print(f"   {i+1}. {model['Model']}: {model['Accuracy']:.4f}")

# Recomendações
print(f"\n💡 RECOMENDAÇÕES:")

if best_accuracy > 0.95:
    print("   ✅ Excelente performance! Modelo pronto para produção.")
elif best_accuracy > 0.90:
    print("   ✅ Boa performance! Considere otimização de hiperparâmetros.")
else:
    print("   ⚠️ Performance moderada. Considere feature engineering adicional.")

if len(high_corr_pairs) > 0:
    print("   📊 Há features altamente correlacionadas - considere remoção.")

if n_components_95 < len(numeric_features) * 0.5:
    print("   🔬 PCA pode reduzir dimensionalidade significativamente.")

print("\n🎯 PRÓXIMOS PASSOS:")
print("   1. Otimização de hiperparâmetros do melhor modelo")
print("   2. Validação cruzada mais robusta")
print("   3. Ensemble methods")
print("   4. Deploy em produção com MLflow")

print(f"\n✅ Análise completa finalizada em {datetime.now()}")
