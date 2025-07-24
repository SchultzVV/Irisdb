
class spark_IO_UC:
    def __init__(self, catalog: str, schema: str, volume: str, file_name: str):
        self.spark = SparkSession.builder.getOrCreate()
        self.volume_path = f"/Volumes/{catalog}/{schema}/{volume}/{file_name}"
        self.catalog_table = f"{catalog}.{schema}.{file_name.replace('.parquet', '')}"

    def read_parquet(self) -> DataFrame:
        return self.spark.read.parquet(self.volume_path)

    def read_table(self) -> DataFrame:
        return self.spark.read.table(self.catalog_table)

    def save_parquet(self, df: DataFrame) -> None:
        df.coalesce(1).write.mode("overwrite").parquet(self.volume_path)

    def save_as_table(self, df: DataFrame) -> None:
        df.write.mode("overwrite").saveAsTable(self.catalog_table)
