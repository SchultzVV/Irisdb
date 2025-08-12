# Databricks notebook source
from pyspark.sql.functions import avg, count

# Get parameters from job (with fallback)
try:
    input_silver_table = dbutils.widgets.get("input_silver_table")
    output_gold_table = dbutils.widgets.get("output_gold_table")
except:
    input_silver_table = "workspace.default.iris_silver"
    output_gold_table = "workspace.default.iris_gold"

# Load data from Silver table (Unity Catalog)
df = spark.table(input_silver_table)

# Aggregation by species
df_gold = (
    df.groupBy("species")
      .agg(
          avg("sepal_length").alias("avg_sepal_length"),
          avg("sepal_width").alias("avg_sepal_width"),
          avg("petal_length").alias("avg_petal_length"),
          avg("petal_width").alias("avg_petal_width"),
          count("*").alias("count_records")
      )
)

# Save to Gold layer (Unity Catalog table)
df_gold.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(output_gold_table)

print("✅ Gold aggregation complete")
print(f"✅ Data saved to table: {output_gold_table}")
print(f"✅ Aggregated {df_gold.count()} species")

# Mostrar preview dos dados agregados
print("\n📊 Preview dos dados Gold:")
df_gold.show(truncate=False)

# 🧪 VALIDAÇÕES GOLD
print("\n🧪 Executando validações Gold...")

# Validação 1: Exatamente 3 espécies
gold_count = df_gold.count()
assert gold_count == 3, f"❌ Gold deve ter 3 registros, encontrou: {gold_count}"
print(f"✅ Gold: Exatamente 3 espécies agregadas")

# Validação 2: Todas as espécies presentes
species_in_gold = [row['species'] for row in df_gold.select("species").collect()]
expected_species = ["setosa", "versicolor", "virginica"]
for species in expected_species:
    assert species in species_in_gold, f"❌ Espécie {species} não encontrada no Gold"
print(f"✅ Gold: Todas as espécies presentes: {species_in_gold}")

# Validação 3: Contagens por espécie são razoáveis
from pyspark.sql.functions import col

for row in df_gold.collect():
    species = row.species
    count_records = row.count_records
    assert count_records >= 40 and count_records <= 60, f"❌ Contagem anormal para {species}: {count_records}"

print("✅ Gold: Contagens por espécie são válidas")

# Validação 4: Médias são positivas
avg_cols = [c for c in df_gold.columns if c.startswith("avg_")]
for col_name in avg_cols:
    min_avg = df_gold.select(col(col_name)).agg({col_name: "min"}).collect()[0][0]
    assert min_avg > 0, f"❌ Média negativa em {col_name}: {min_avg}"

print("✅ Gold: Todas as médias são positivas")

print("🎉 GOLD: Todas as validações passaram!")
