# Databricks notebook source

# Load data from Bronze layer (Unity Catalog)
from pyspark.sql import SparkSession

# Get parameters from job (with fallback)
try:
    input_bronze_table = dbutils.widgets.get("input_bronze_table")
    output_silver_table = dbutils.widgets.get("output_silver_table")
except:
    input_bronze_table = "default.iris_bronze"
    output_silver_table = "default.iris_silver"

# Load data from Bronze table (not DBFS path)
df = spark.table(input_bronze_table)

# Validação de schema esperada
expected_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
assert df.columns == expected_columns, "❌ Schema inesperado na Bronze table"

# Exemplo de transformação
df_clean = df.dropna()

# Data cleaning and validation
from pyspark.sql.functions import col
df_clean = (
    df.dropna()
      .filter(col("sepal_length") > 0)
      .filter(col("sepal_width") > 0)
      .filter(col("petal_length") > 0)
      .filter(col("petal_width") > 0)
)

# Save to Silver layer (Unity Catalog table)
df_clean.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_silver_table)

print("✅ Silver transformation complete")
print(f"✅ Data saved to table: {output_silver_table}")
print(f"✅ Cleaned {df_clean.count()} rows")

# 🧪 VALIDAÇÃO DE QUALIDADE DE DADOS SILVER
print("\n🧪 Executando validações Silver...")

try:
    import great_expectations as gx
    from great_expectations.core.batch import RuntimeBatchRequest
    
    # Configurar contexto GE
    context_root_dir = "/Workspace/Users/xultezz@gmail.com/.bundle/iris_bundle/dev/files/great_expectations"
    context = gx.get_context(context_root_dir=context_root_dir)
    
    # Criar batch request para a tabela Silver
    batch_request = RuntimeBatchRequest(
        datasource_name="iris_data",
        data_connector_name="default_runtime_data_connector_name",
        data_asset_name=output_silver_table,
        runtime_parameters={"query": f"SELECT * FROM {output_silver_table}"},
        batch_identifiers={"default_identifier_name": "silver_batch"}
    )
    
    # Executar checkpoint de validação
    results = context.run_checkpoint(
        checkpoint_name="iris_silver_checkpoint",
        validations=[
            {
                "batch_request": batch_request,
                "expectation_suite_name": "iris_silver_suite"
            }
        ]
    )
    
    if results["success"]:
        print("✅ VALIDAÇÃO SILVER: Todos os testes passaram!")
        stats = results.get("statistics", {})
        print(f"📊 Expectativas avaliadas: {stats.get('evaluated_expectations', 'N/A')}")
        print(f"✅ Taxa de sucesso: {stats.get('success_percent', 'N/A')}%")
    else:
        print("❌ VALIDAÇÃO SILVER: Algumas validações falharam!")
        
except Exception as e:
    print(f"⚠️ Validação Silver falhou: {e}")
    print("📝 Continuando execução...")
