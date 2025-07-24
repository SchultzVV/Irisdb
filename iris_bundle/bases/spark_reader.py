from pyspark.sql.dataframe import DataFrame as SparkDataFrame
from datetime import timedelta, datetime, date
# import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.dbutils import DBUtils


class spark_IO:
    """
    Classe para leitura e escrita de arquivos parquet no Databricks

    Parâmetros
    ---
    spark: SparkSession
    cluster: Cluster do Databricks 
    ambiente: Ambiente do Datalake (prd ou dev)
    path: Caminho do arquivo no Datalake
    file_name: Nome do arquivo no Datalake
    temp_path: Caminho temporário, onde o arquivo será salvo com nome aleatório
    pelo databricks (comportamento inevitável)
    """

    def __init__(
        self,
        cluster: str,
        ambiente: str,
        path: str,
        file_name: str,
        temp_path: str,
    ) -> None:
        self.spark = SparkSession.builder.getOrCreate()
        self.cluster = cluster
        self.path = path
        self.file_name = file_name
        self.path_not_full = "/".join(["/mnt", cluster, ambiente, path])
        self.temp_path_not_full = "/".join(["/mnt", cluster, ambiente, temp_path])
        self.full_path = "/".join(["/mnt", cluster, ambiente, path, file_name])
        self.full_temp_path = "/".join(
            ["/mnt", cluster, ambiente, temp_path, file_name]
        )

    def read_parquet(self) -> DataFrame:
        """
        Leitura de arquivos no formato parquet com spark.
        """
        return self.spark.read.parquet(self.full_path)

    def read_parquet_months(self, n_months, days=False) -> SparkDataFrame:
        data = datetime.now().replace(day=1)
        # data = date(2024, 9, 15)
        # day = str(data.date().strftime('%d'))
        mes = str(data.strftime('%m'))
        ano = str(data.year)
        caminho = f"{self.path_not_full}/{ano}/{mes}/{self.file_name}_{ano}{mes}.parquet"
        # print(caminho)
        df = self.spark.read.parquet(caminho)
        return df
    
    def read_parquet_months_old(self, n_months, days=False) -> SparkDataFrame:
        hoje = date.today()
        mes_n_meses_atras = hoje.replace(day=1) - timedelta(days=n_months * 30)  # Aproximando 30 dias por mês
        data_inicio = mes_n_meses_atras.replace(day=1)
        
        # Calcule o fim do intervalo desejado (último dia do mês corrente)
        proximo_mes = (hoje.replace(day=28) + timedelta(days=4)).replace(day=1)
        data_fim = proximo_mes - timedelta(days=1)
        
        caminhos = []
        data_atual = data_inicio
    
        while data_atual <= data_fim:
            if not days:
                caminho_mes = f"{self.full_path}/{data_atual.year}/{data_atual.month:02}/*.parquet"
            else:
                caminho_mes = f"{self.full_path}/{data_atual.year}/{data_atual.month:02}/*/*.parquet"
            caminhos.append(caminho_mes)
            
            # Avançar para o próximo mês
            proximo_mes = data_atual.month + 1 if data_atual.month < 12 else 1
            proximo_ano = data_atual.year + 1 if proximo_mes == 1 else data_atual.year
            data_atual = data_atual.replace(year=proximo_ano, month=proximo_mes, day=1)
        # print(caminhos)
        df = self.spark.read.parquet(*caminhos)
        return df    


    def save_parquet_dat(self, df: SparkDataFrame) -> SparkDataFrame:
        data = datetime.now().replace(day=1)
        day = str(data.date().strftime('%d'))
        mes = str(data.date().strftime('%m'))
        ano = str(data.date().year)
        folder_file_name = self.file_name.replace("rf_","").replace(".parquet","")
        file_name_with_date = f"rf_{folder_file_name}_{ano}-{mes}-{day}.parquet"
        path_composto = "/".join([self.path_not_full, ano, mes, day, folder_file_name, file_name_with_date])

        temp_path =  "/".join([self.temp_path_not_full, ano, mes, day, folder_file_name, file_name_with_date])
        df.coalesce(1).write.mode("overwrite").parquet(temp_path)

        dbutils = DBUtils(self.spark)
        files = dbutils.fs.ls(temp_path)
        for i in range(len(files)):
            file = files[i].name

            if "parquet" in file:
                dbutils.fs.cp(files[i].path, path_composto)
        return None

    def save_parquet(self, df: DataFrame) -> None:
        """
        Salvamento de arquivos no formato parquet com spark.
        Por padrão, os arquivos não podem ser salvos com nomes específicos,
        por tal motivo é necessário informar um caminho temporário,
        a camada transient, para salvar arquivo intermediário.

        Parâmetros
        ---
        df: DataFrame a salvar.
        """
        df.coalesce(1).write.mode("overwrite").parquet(self.full_temp_path)
        dbutils = DBUtils(self.spark)
        files = dbutils.fs.ls(self.full_temp_path)
        print(self.full_temp_path)
        print(self.full_path)
        for i in range(len(files)):
            file = files[i].name

            if "parquet" in file:
                dbutils.fs.cp(files[i].path, self.full_path)
    