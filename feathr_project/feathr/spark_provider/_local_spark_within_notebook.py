from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
from shlex import split
from subprocess import STDOUT, Popen
import time
from typing import Any, Dict, List, Optional

from loguru import logger
from pyspark import *

from feathr.constants import OUTPUT_PATH_TAG
from feathr.version import get_maven_artifact_fullname
from feathr.spark_provider._abc import SparkJobLauncher


from pyspark.sql import SparkSession, DataFrame, SQLContext
import sys
from pyspark.sql.functions import *

# This is executed in Spark driver
# The logger doesn't work in Pyspark so we just use print
print("Feathr Pyspark job started.")
spark = SparkSession.builder.getOrCreate()


def to_java_string_array(arr):
    """Convert a Python string list to a Java String array.
    """
    jarr = spark._sc._gateway.new_array(spark._sc._jvm.java.lang.String, len(arr))
    for i in range(len(arr)):
        jarr[i] = arr[i]
    return jarr


def submit_spark_job(feature_names_funcs):
    """Submit the Pyspark job to the cluster. This should be used when there is Python UDF preprocessing for sources.
    It loads the source DataFrame from Scala spark. Then preprocess the DataFrame with Python UDF in Pyspark. Later,
    the real Scala FeatureJoinJob or FeatureGenJob is executed with preprocessed DataFrames instead of the original
    source DataFrames.

        Args:
            feature_names_funcs: Map of feature names concatenated to preprocessing UDF function.
            For example {"f1,f2": df1, "f3,f4": df2} (the feature names in the key will be sorted)
    """
    # Prepare job parameters
    # sys.argv has all the arguments passed by submit job.
    # In pyspark job, the first param is the python file.
    # For example: ['pyspark_client.py', '--join-config', 'abfss://...', ...]
    has_gen_config = False
    has_join_config = False
    if '--generation-config' in sys.argv:
        has_gen_config = True
    if '--join-config' in sys.argv:
        has_join_config = True

    py4j_feature_job = None
    if has_gen_config and has_join_config:
        raise RuntimeError("Both FeatureGenConfig and FeatureJoinConfig are provided. "
                           "Only one of them should be provided.")
    elif has_gen_config:
        py4j_feature_job = spark._jvm.com.linkedin.feathr.offline.job.FeatureGenJob
        print("FeatureGenConfig is provided. Executing FeatureGenJob.")
    elif has_join_config:
        py4j_feature_job = spark._jvm.com.linkedin.feathr.offline.job.FeatureJoinJob
        print("FeatureJoinConfig is provided. Executing FeatureJoinJob.")
    else:
        raise RuntimeError("None of FeatureGenConfig and FeatureJoinConfig are provided. "
                           "One of them should be provided.")
    job_param_java_array = to_java_string_array(sys.argv)

    print("submit_spark_job: feature_names_funcs: ")
    print(feature_names_funcs)
    print("set(feature_names_funcs.keys()): ")
    print(set(feature_names_funcs.keys()))

    print("submit_spark_job: Load DataFrame from Scala engine.")

    dataframeFromSpark = py4j_feature_job.loadSourceDataframe(job_param_java_array, set(feature_names_funcs.keys())) # TODO: Add data handler support here
    print("Submit_spark_job: dataframeFromSpark: ")
    print(dataframeFromSpark)

    # per comment https://stackoverflow.com/a/54738984, use explicit way to initialize SQLContext
    # Otherwise it might fail when calling `DataFrame.collect()` or other APIs that's related with SQLContext
    # do not use `sql_ctx = SQLContext(spark)`
    sql_ctx = SQLContext(sparkContext=spark.sparkContext, sparkSession=spark)
    new_preprocessed_df_map = {}
    for feature_names, scala_dataframe in dataframeFromSpark.items():
        # Need to convert java DataFrame into python DataFrame
        py_df = DataFrame(scala_dataframe, sql_ctx)
        # Preprocess the DataFrame via UDF
        user_func = feature_names_funcs[feature_names]
        preprocessed_udf = user_func(py_df)
        new_preprocessed_df_map[feature_names] = preprocessed_udf._jdf

    print("submit_spark_job: running Feature job with preprocessed DataFrames:")
    print("Preprocessed DataFrames are: ")
    print(new_preprocessed_df_map)

    py4j_feature_job.mainWithPreprocessedDataFrame(job_param_java_array, new_preprocessed_df_map)
    return None




class _FeathrLocalSparkJobWithinNotebookLauncher(SparkJobLauncher):
    """Class to interact with local Spark. This class is not intended to be used in Production environments.
    It is intended to be used for testing and development purposes. No authentication is required to use this class.

    Args:
        workspace_path (str): Path to the workspace
    """

    def __init__(
        self,
        debug_folder: str = "debug",
        clean_up: bool = True,
    ):
        """Initialize the Local Spark job launcher"""
        self.debug_folder = debug_folder
        self.spark_job_num = 0
        self.clean_up = clean_up
        self.packages = self._get_default_package()
        self.job_tags = None

    def upload_or_get_cloud_path(self, local_path_or_http_path: str):
        """For Local Spark Case, no need to upload to cloud workspace."""
        return local_path_or_http_path

    def submit_feathr_job(
        self,
        job_name: str,
        main_jar_path: str,
        main_class_name: str,
        arguments: List[str] = None,
        python_files: List[str] = None,
        job_tags: Dict[str, str] = None,
        configuration: Dict[str, str] = {},
        properties: Dict[str, str] = {},
        **_,
    ) -> Any:
        """Submits the Feathr job to local spark, using subprocess args.
        Note that the Spark application will automatically run on YARN cluster mode. You cannot change it if
        you are running with Azure Synapse.

        Args:
            job_name: name of the job
            main_jar_path: main file paths, usually your main jar file
            main_class_name: name of your main class
            arguments: all the arguments you want to pass into the spark job
            python_files: required .zip, .egg, or .py files of spark job
            job_tags: tags of the job, for example you might want to put your user ID, or a tag with a certain information
            configuration: Additional configs for the spark job
            properties: System properties configuration
            **_: Not used arguments in local spark mode, such as reference_files_path
        """
        logger.warning(
            f"Local Spark Mode only support basic params right now and should be used only for testing purpose."
        )
        self.cmd_file, self.log_path = self._get_debug_file_name(self.debug_folder, prefix=job_name)

        # Get conf and package arguments
        cfg = configuration.copy() if configuration else {}
        maven_dependency = f"{cfg.pop('spark.jars.packages', self.packages)},{get_maven_artifact_fullname()}"
        # spark_args = self._init_args(job_name=job_name, confs=cfg)
        spark_args = []

        # TODO: currently everything is forced to set as UDF; we need to test the other path
        if not main_jar_path:
            # We don't have the main jar, use Maven
            if not python_files:
                # This is a JAR job
                # Azure Synapse/Livy doesn't allow JAR job starts from Maven directly, we must have a jar file uploaded.
                # so we have to use a dummy jar as the main file.
                # logger.info(f"Main JAR file is not set, using default package '{get_maven_artifact_fullname()}' from Maven")
                # Use the no-op jar as the main file
                # This is a dummy jar which contains only one `org.example.Noop` class with one empty `main` function
                # which does nothing
                # current_dir = Path(__file__).parent.resolve()
                # main_jar_path = os.path.join(current_dir, "noop-1.0.jar")
                # spark_args.extend(["--packages", maven_dependency, "--class", main_class_name, main_jar_path])
                # TODO: currently everything is forced to set as UDF; we need to test the other path
                pass
            else:
                # TODO: don't use maven as it's not supported in many of the environments
                # spark_args.extend(["--packages", maven_dependency])
                # This is a PySpark job, no more things to
                if python_files.__len__() > 1:
                    spark_args.extend(["--py-files", ",".join(python_files[1:])])
                print(python_files)
                spark_args.append(python_files[0])
        else:
            spark_args.extend(["--class", main_class_name, main_jar_path])

        if arguments:
            spark_args.extend(arguments)
        
        # turn arguments from list to dict
        # TODO: we assume the length is even number here
        arguments_dict = {}
        for i in range(0, len(arguments)-1, 2):
            arguments_dict[arguments[i]] = arguments[i+1]

        if properties:
            spark_args.extend(["--system-properties", json.dumps(properties)])

        cmd = " ".join(spark_args)

        python_file_path = python_files[0]
        import sys
        sys.argv=arguments
        exec(open(python_file_path).read())


        self.job_tags = deepcopy(job_tags)

        return

    def wait_for_completion(self, timeout_seconds: Optional[float] = 500) -> bool:
        """This function track local spark job commands and process status.
        Files will be write into `debug` folder under your workspace.
        """
        logger.info(f"{self.spark_job_num} local spark job(s) in this Launcher, only the latest will be monitored.")
        logger.info(f"Please check auto generated spark command in {self.cmd_file} and detail logs in {self.log_path}.")

        proc = self.latest_spark_proc
        start_time = time.time()
        retry = self.retry

        log_read = open(f"{self.log_path}_{self.spark_job_num-1}.txt", "r")
        while proc.poll() is None and (((timeout_seconds is None) or (time.time() - start_time < timeout_seconds))):
            time.sleep(1)
            try:
                if retry < 1:
                    logger.warning(
                        f"Spark job has hang for {self.retry * self.retry_sec} seconds. latest msg is {last_line}. \
                            Please check {log_read.name}"
                    )
                    if self.clean_up:
                        self._clean_up()
                        proc.wait()
                    break
                last_line = log_read.readlines()[-1]
                retry = self.retry
                if last_line == []:
                    print("_", end="")
                else:
                    print(">", end="")
                    if last_line.__contains__("Feathr Pyspark job completed"):
                        logger.info(f"Pyspark job Completed")
                        proc.terminate()
            except IndexError as e:
                print("x", end="")
                time.sleep(self.retry_sec)
                retry -= 1

        job_duration = time.time() - start_time
        log_read.close()

        if proc.returncode == None:
            logger.warning(
                f"Spark job with pid {self.latest_spark_proc.pid} not completed after {timeout_seconds} sec \
                    time out setting. Please check."
            )
            if self.clean_up:
                self._clean_up()
                proc.wait()
                return True
        elif proc.returncode == 1:
            logger.warning(f"Spark job with pid {self.latest_spark_proc.pid} is not successful. Please check.")
            return False
        else:
            logger.info(
                f"Spark job with pid {self.latest_spark_proc.pid} finished in: {int(job_duration)} seconds \
                    with returncode {proc.returncode}"
            )
            return True

    def _clean_up(self, proc: Popen = None):
        logger.warning(f"Terminate the spark job due to as clean_up is set to True.")
        if not proc:
            self.latest_spark_proc.terminate()
        else:
            proc.terminate()

    def get_status(self) -> str:
        """Get the status of the job, only a placeholder for local spark"""
        return self.latest_spark_proc.returncode

    def get_job_result_uri(self) -> str:
        """Get job output path

        Returns:
            str: output_path
        """
        return self.job_tags.get(OUTPUT_PATH_TAG, None) if self.job_tags else None

    def get_job_tags(self) -> Dict[str, str]:
        """Get job tags

        Returns:
            Dict[str, str]: a dict of job tags
        """
        return self.job_tags

    def _init_args(self, job_name: str, confs: Dict[str, str]) -> List[str]:
        logger.info(f"Spark job: {job_name} is running on local spark.")
        args = [
            "spark-submit",
            "--name",
            job_name,
            "--conf",
            "spark.hadoop.fs.wasbs.impl=org.apache.hadoop.fs.azure.NativeAzureFileSystem",
            "--conf",
            "spark.hadoop.fs.wasbs=org.apache.hadoop.fs.azure.NativeAzureFileSystem",
        ]

        for k, v in confs.items():
            args.extend(["--conf", f"{k}={v}"])

        return args

    def _get_debug_file_name(self, debug_folder: str = "debug", prefix: str = None):
        """Auto generated command will be write into cmd file.
        Spark job output will be write into log path with job number as suffix.
        """
        prefix += datetime.now().strftime("%Y%m%d%H%M%S")
        debug_path = os.path.join(debug_folder, prefix)

        print(debug_path)
        if not os.path.exists(debug_path):
            os.makedirs(debug_path)

        cmd_file = os.path.join(debug_path, f"command.sh")
        log_path = os.path.join(debug_path, f"log")

        return cmd_file, log_path

    def _get_default_package(self):
        # default packages of Feathr Core, requires manual update when new dependency introduced or package updated.
        # TODO: automate this process, e.g. read from pom.xml
        # TODO: dynamical modularization: add package only when it's used in the job, e.g. data source dependencies.
        packages = []
        packages.append("org.apache.spark:spark-avro_2.12:3.3.0")
        packages.append("com.microsoft.sqlserver:mssql-jdbc:10.2.0.jre8")
        packages.append("com.microsoft.azure:spark-mssql-connector_2.12:1.2.0")
        packages.append("org.apache.logging.log4j:log4j-core:2.17.2,com.typesafe:config:1.3.4")
        packages.append("com.fasterxml.jackson.core:jackson-databind:2.12.6.1")
        packages.append("org.apache.hadoop:hadoop-mapreduce-client-core:2.7.7")
        packages.append("org.apache.hadoop:hadoop-common:2.7.7")
        packages.append("org.apache.hadoop:hadoop-azure:3.2.0")
        packages.append("org.apache.avro:avro:1.8.2,org.apache.xbean:xbean-asm6-shaded:4.10")
        packages.append("org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.3")
        packages.append("com.microsoft.azure:azure-eventhubs-spark_2.12:2.3.21")
        packages.append("org.apache.kafka:kafka-clients:3.1.0")
        packages.append("com.google.guava:guava:31.1-jre")
        packages.append("it.unimi.dsi:fastutil:8.1.1")
        packages.append("org.mvel:mvel2:2.2.8.Final")
        packages.append("com.fasterxml.jackson.module:jackson-module-scala_2.12:2.13.3")
        packages.append("com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:2.12.6")
        packages.append("com.fasterxml.jackson.dataformat:jackson-dataformat-csv:2.12.6")
        packages.append("com.jasonclawson:jackson-dataformat-hocon:1.1.0")
        packages.append("com.redislabs:spark-redis_2.12:3.1.0")
        packages.append("org.apache.xbean:xbean-asm6-shaded:4.10")
        packages.append("com.google.protobuf:protobuf-java:3.19.4")
        packages.append("net.snowflake:snowflake-jdbc:3.13.18")
        packages.append("net.snowflake:spark-snowflake_2.12:2.10.0-spark_3.2")
        packages.append("org.apache.commons:commons-lang3:3.12.0")
        packages.append("org.xerial:sqlite-jdbc:3.36.0.3")
        packages.append("com.github.changvvb:jackson-module-caseclass_2.12:1.1.1")
        packages.append("com.azure.cosmos.spark:azure-cosmos-spark_3-1_2-12:4.11.1")
        packages.append("org.eclipse.jetty:jetty-util:9.3.24.v20180605")
        packages.append("commons-io:commons-io:2.6")
        packages.append("org.apache.hadoop:hadoop-azure:2.7.4")
        packages.append("com.microsoft.azure:azure-storage:8.6.4")
        return ",".join(packages)
