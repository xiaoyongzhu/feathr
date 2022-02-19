package com.linkedin.feathr.offline.job

import com.linkedin.feathr.common.TaggedFeatureName
import com.linkedin.feathr.common.configObj.configbuilder.FeatureGenConfigBuilder
import com.linkedin.feathr.offline.client.FeathrClient
import com.linkedin.feathr.offline.config.FeathrConfigLoader
import com.linkedin.feathr.offline.job.FeatureJoinJob._
import com.linkedin.feathr.offline.job.FeatureStoreConfigUtil.{REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_SSL_ENABLED, S3_ACCESS_KEY, S3_ENDPOINT, S3_SECRET_KEY}
import com.linkedin.feathr.offline.util.{CmdLineParser, OptionParam, SparkFeaturizedDataset}
import com.typesafe.config.{ConfigFactory, ConfigRenderOptions}
import org.apache.avro.generic.GenericRecord
import org.apache.commons.cli.{Option => CmdOption}
import org.apache.log4j.Logger
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession

import scala.collection.JavaConverters._

object FeatureGenJob {

  type ApplicationConfigPath = String
  val logger: Logger = Logger.getLogger(getClass)
  /**
   * Parse command line arguments, which includes application config,
   * Feathr feature definition configs and other settings
   *
   * @param args command line arguments
   * @return (applicationConfigPath, feature defintions and FeatureGenJobContext)
   * Results wil be used to construct FeathrFeatureGenJobContext
   */
  private[feathr] def parseInputArguments(args: Array[String]): (ApplicationConfigPath, FeatureDefinitionsInput, FeatureGenJobContext) = {
    val params = Map(
      // option long name, short name, description, arg name (null means not argument), default value (null means required)
      "feathr-config" -> OptionParam("lf", "Path of the feathr local config file", "FCONF", ""),
      "feature-config" -> OptionParam("f", "Names of the feathr feature config files", "EFCONF", ""),
      "local-override-all" -> OptionParam("loa", "Local config overrides all other configs", "LOCAL_OVERRIDE", "true"),
      "work-dir" -> OptionParam ("wd", "work directory, used to store temporary results, etc.", "WORK_DIR", ""),
      "generation-config" -> OptionParam("gc", "Path of the feature generation config file", "JCONF", null),
      "params-override" -> OptionParam("ac", "parameter to override in feature generation config", "PARAM_OVERRIDE", "[]"),
      "feature-conf-override" -> OptionParam("fco", "parameter to override in feature definition config", "FEATURE_CONF_OVERRIDE", "[]"),
      "redis-config" -> OptionParam("ac", "Authentication config for Redis", "REDIS_CONFIG", ""),
      "s3-config" -> OptionParam("ac", "Authentication config for S3", "S3_CONFIG", ""))
    val extraOptions = List(new CmdOption("LOCALMODE", "local-mode", false, "Run in local mode"))

    val cmdParser = new CmdLineParser(args, params, extraOptions)

    val applicationConfigPath = cmdParser.extractRequiredValue("generation-config")
    val featureDefinitionsInput = new FeatureDefinitionsInput(
      cmdParser.extractOptionalValue("feathr-config"),
      cmdParser.extractOptionalValue("feature-config"),
      cmdParser.extractRequiredValue("local-override-all"))
    val paramsOverride = cmdParser.extractOptionalValue("params-override")
    val featureConfOverride = cmdParser.extractOptionalValue("feature-conf-override").map(convertToHoconConfig)
    val workDir = cmdParser.extractRequiredValue("work-dir")
    val redisConfig = cmdParser.extractOptionalValue("redis-config")
    val s3Config = cmdParser.extractOptionalValue("s3-config")
    val featureGenJobContext = new FeatureGenJobContext(workDir, paramsOverride, featureConfOverride, redisConfig, s3Config)

    (applicationConfigPath, featureDefinitionsInput, featureGenJobContext)
  }

  // Convert parameters passed from hadoop template into global vars section for feature conf
  def convertToHoconConfig(params: String): String = {
    params.stripPrefix("[").stripSuffix("]")
  }

  /**
   * generate Feathr features according to config file paths and jobContext
   * @param ss spark session
   * @param featureGenConfigPath  feature generation config file path
   * @param featureDefInputs contains feature definition file paths and settings
   * @param jobContext job context
   * @return generated feature data
   */
  def run(
      ss: SparkSession,
      featureGenConfigPath: String,
      featureDefInputs: FeatureDefinitionsInput,
      jobContext: FeatureGenJobContext):  Map[TaggedFeatureName, SparkFeaturizedDataset] = {
    // load feature definitions input files
    val applicationConfig = hdfsFileReader(ss, featureGenConfigPath)
    val featureConfig = featureDefInputs.feathrFeatureDefPaths.map(path => hdfsFileReader(ss, path))
    val localFeatureConfig = featureDefInputs.feathrLocalFeatureDefPath.map(path => hdfsFileReader(ss, path))
    val (featureConfigWithOverride, localFeatureConfigWithOverride) = overrideFeatureDefs(featureConfig, localFeatureConfig, jobContext)
    run(ss, applicationConfig, featureConfigWithOverride, localFeatureConfigWithOverride, jobContext)
  }

  private[feathr] def overrideFeatureDefs(featureConfig: Option[String], localFeatureConfig: Option[String], jobContext: FeatureGenJobContext) = {
    val featureConfigWithOverride = if (featureConfig.isDefined && jobContext.featureConfOverride.isDefined) {
      Some(FeathrConfigLoader.resolveOverride(featureConfig.get, jobContext.featureConfOverride.get))
    } else {
      featureConfig
    }
    val localFeatureConfigWithOverride = if (localFeatureConfig.isDefined && jobContext.featureConfOverride.isDefined) {
      Some(FeathrConfigLoader.resolveOverride(localFeatureConfig.get, jobContext.featureConfOverride.get))
    } else {
      localFeatureConfig
    }
    (featureConfigWithOverride, localFeatureConfigWithOverride)
  }

  /**
   * generate Feathr features according to config file contents and jobContext
   * @param ss spark session
   * @param featureGenConfig feature generation config as a string
   * @param featureDefConfig feature definition config, comes from feature repo
   * @param localFeatureConfig feature definition config, comes from local feature definition files
   * @param jobContext job context
   * @return generated feature data
   */
  private[feathr] def run(
      ss: SparkSession,
      featureGenConfig: String,
      featureDefConfig: Option[String],
      localFeatureConfig: Option[String],
      jobContext: FeatureGenJobContext): Map[TaggedFeatureName, SparkFeaturizedDataset] = {

    print("featureDefConfig", featureDefConfig)
    print("localFeatureConfig",localFeatureConfig)
    val feathrClient =
        FeathrClient.builder(ss)
          .addFeatureDef(featureDefConfig)
          .addLocalOverrideDef(localFeatureConfig)
          .build()
    val featureGenSpec = parseFeatureGenApplicationConfig(featureGenConfig, jobContext)
    feathrClient.generateFeatures(featureGenSpec)
  }

  /**
   * parsing feature generation config string to [[FeatureGenSpec]]
   * @param featureGenConfigStr feature generation config as a string
   * @param featureGenJobContext feature generation context
   * @return Feature generation Specifications
   */
  private[feathr] def parseFeatureGenApplicationConfig(featureGenConfigStr: String, featureGenJobContext: FeatureGenJobContext): FeatureGenSpec = {
    val withParamsOverrideConfigStr = overrideFeatureGeneration(featureGenConfigStr, featureGenJobContext.paramsOverride)
    val withParamsOverrideConfig = ConfigFactory.parseString(withParamsOverrideConfigStr)
    val featureGenConfig = FeatureGenConfigBuilder.build(withParamsOverrideConfig)
    new FeatureGenSpec(featureGenConfig)
  }

  private[feathr] def overrideFeatureGeneration(featureGenConfigStr: String, paramsOverride: Option[String]): String = {
    val fullConfig = ConfigFactory.parseString(featureGenConfigStr)
    val withParamsOverrideConfig = paramsOverride
      .map(configStr => {
        // override user specified parameters
        val paramOverrideConfigStr = "operational: {" + configStr.stripPrefix("[").stripSuffix("]") + "}"
        val paramOverrideConfig = ConfigFactory.parseString(paramOverrideConfigStr)
        // typeSafe config does not support path expression to access array elements directly
        // see https://github.com/lightbend/config/issues/30, so we need to special handle path expression for output array
        val withOutputOverrideStr = fullConfig
          .getConfigList("operational.output")
          .asScala
          .zipWithIndex
          .map {
            case (output, idx) =>
              val key = "operational.output(" + idx + ")"
              val withOverride = if (paramOverrideConfig.hasPath(key)) {
                paramOverrideConfig.getConfig(key).withFallback(output)
              } else output
              withOverride.root().render(ConfigRenderOptions.concise())
          }
          .mkString(",")
        val withOutputOverride = ConfigFactory.parseString("operational.output:[" + withOutputOverrideStr + "]")
        // override the config with paramOverrideConfig
        paramOverrideConfig.withFallback(withOutputOverride).withFallback(fullConfig)
      })
      .getOrElse(fullConfig)
    withParamsOverrideConfig.root().render()
  }

  private[feathr] def setupSparkRedis(sparkConf: SparkConf, featureGenContext: Option[FeatureGenJobContext] = None) = {
    val host = FeatureStoreConfigUtil.getRedisAuthStr(REDIS_HOST, featureGenContext)
    val port = FeatureStoreConfigUtil.getRedisAuthStr(REDIS_PORT, featureGenContext)
    val sslEnabled = FeatureStoreConfigUtil.getRedisAuthStr(REDIS_SSL_ENABLED, featureGenContext)
    val auth = FeatureStoreConfigUtil.getRedisAuthStr(REDIS_PASSWORD, featureGenContext)
    sparkConf.set("spark.redis.host", host)
    sparkConf.set("spark.redis.port", port)
    sparkConf.set("spark.redis.ssl", sslEnabled)
    sparkConf.set("spark.redis.auth", auth)
  }

  private[feathr] def setupS3Params(ss: SparkSession, featureGenContext: Option[FeatureGenJobContext] = None) = {
    val s3Endpoint = FeatureStoreConfigUtil.getS3AuthStr(S3_ENDPOINT, featureGenContext)
    val s3AccessKey = FeatureStoreConfigUtil.getS3AuthStr(S3_ACCESS_KEY, featureGenContext)
    val s3SecretKey = FeatureStoreConfigUtil.getS3AuthStr(S3_SECRET_KEY, featureGenContext)

    ss.sparkContext
      .hadoopConfiguration.set("fs.s3a.endpoint", s3Endpoint)
    ss.sparkContext
      .hadoopConfiguration.set("fs.s3a.access.key", s3AccessKey)
    ss.sparkContext
      .hadoopConfiguration.set("fs.s3a.secret.key", s3SecretKey)
  }

  private[feathr] def process(params: Array[String]): Map[TaggedFeatureName, SparkFeaturizedDataset] = {
    val (applicationConfigPath, featureDefs, jobContext) = parseInputArguments(params)
    val sparkConf = new SparkConf().registerKryoClasses(Array(classOf[GenericRecord]))
    setupSparkRedis(sparkConf, Some(jobContext))
    val sparkSessionBuilder = SparkSession
      .builder()
      .config(sparkConf)
      .appName(getClass.getName)
      .enableHiveSupport()

    val ss = sparkSessionBuilder.getOrCreate()
    setupS3Params(ss, Some(jobContext))
    run(ss, applicationConfigPath, featureDefs, jobContext)
  }

  def main(args: Array[String]) {
    process(args)
  }
}
