from pyspark.sql import SparkSession
from non_agg_features import *

def main(spark: SparkSession):
  
  print(batch_source.name)
  df = spark.read.option('header', 'true').csv('wasbs://public@azurefeathrstorage.blob.core.windows.net/sample_data/green_tripdata_2020-04.csv')
  df = df.filter("tolls_amount > 0.0")
  df.write.mode('overwrite').csv('abfss://feathrazuretest3fs@feathrazuretest3storage.dfs.core.windows.net/UDF_output.csv')


if __name__ == "__main__":
  main(SparkSession.builder.getOrCreate())