# Databricks notebook source
import seaborn as sns
import pandas as pd

# Load Iris dataset via seaborn
df = sns.load_dataset("iris")

# Convert to Spark DataFrame
df_spark = spark.createDataFrame(df)

# Save as managed table in Unity Catalog (avoids DBFS issues)
# This will work in UC-enabled workspaces
output_table = "default.iris_bronze"

try:
    # Try to save as managed table
    df_spark.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_table)
    print(f"✅ Bronze ingestion complete - saved to table: {output_table}")
    
    # Show count to verify
    count = spark.table(output_table).count()
    print(f"✅ Table contains {count} rows")
    
    # 🧪 VALIDAÇÃO DE QUALIDADE DE DADOS
    print("\n🧪 Executando validações de qualidade de dados...")
    
    try:
        import great_expectations as gx
        from great_expectations.core.batch import RuntimeBatchRequest
        
        # Configurar contexto GE
        context_root_dir = "/Workspace/Users/xultezz@gmail.com/.bundle/iris_bundle/dev/files/great_expectations"
        context = gx.get_context(context_root_dir=context_root_dir)
        
        # Criar batch request para a tabela Bronze
        batch_request = RuntimeBatchRequest(
            datasource_name="iris_data",
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name=output_table,
            runtime_parameters={"query": f"SELECT * FROM {output_table}"},
            batch_identifiers={"default_identifier_name": "bronze_batch"}
        )
        
        # Executar checkpoint de validação
        results = context.run_checkpoint(
            checkpoint_name="iris_bronze_checkpoint",
            validations=[
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": "iris_bronze_suite"
                }
            ]
        )
        
        if results["success"]:
            print("✅ VALIDAÇÃO: Todos os testes de qualidade passaram!")
            stats = results.get("statistics", {})
            print(f"📊 Expectativas avaliadas: {stats.get('evaluated_expectations', 'N/A')}")
            print(f"✅ Taxa de sucesso: {stats.get('success_percent', 'N/A')}%")
        else:
            print("❌ VALIDAÇÃO: Algumas validações falharam!")
            print("🔍 Verifique os logs de Great Expectations para detalhes")
            
    except Exception as e:
        print(f"⚠️ Validação Great Expectations falhou: {e}")
        print("📝 Continuando execução sem validação...")
    
except Exception as e:
    print(f"❌ Error saving to table: {e}")
    # Fallback: try to save to workspace tmp location
    fallback_path = "/tmp/iris_bronze_data"
    df_spark.write.mode("overwrite").format("parquet").save(fallback_path)
    print(f"✅ Saved to fallback location: {fallback_path}")
