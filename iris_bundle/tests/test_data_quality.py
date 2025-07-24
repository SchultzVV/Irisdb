import pyspark.sql.functions as F

def test_no_nulls_in_silver(spark):
    df = spark.read.format("delta").load("/mnt/datalake/iris/silver")
    null_count = df.select([F.count(F.when(F.col(c).isNull(), c)) for c in df.columns])
    assert all([row == 0 for row in null_count.collect()[0]])