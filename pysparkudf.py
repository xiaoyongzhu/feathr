from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
if __name__ == "__main__":
  spark = SparkSession.builder.appName('SparkByExamples.com').getOrCreate()
  df = spark.read.option('header', 'true').csv('wasbs://public@azurefeathrstorage.blob.core.windows.net/sample_data/green_tripdata_2020-04.csv')
  df = df.filter("tolls_amount > 0.0")
  df.write.csv('abfss://feathrazuretest3fs@feathrazuretest3storage.dfs.core.windows.net/UDF_output.csv')
