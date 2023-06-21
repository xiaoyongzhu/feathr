import json
import os
import datetime
import time
from uuid import UUID
from feathr.definition.anchor import FeatureAnchor
from feathr.definition.dtype import BOOLEAN, FLOAT, INT32, BooleanFeatureType, ValueType
from feathr.definition.feature import Feature
from feathr.definition.feature_derivations import DerivedFeature
from feathr.definition.source import INPUT_CONTEXT, HdfsSource, InputContext
from feathr.definition.transformation import ExpressionTransformation, WindowAggTransformation
from feathr.definition.typed_key import TypedKey
from feathr import FeathrClient



def test_filter_features_by_WindowAggregation(client : FeathrClient):
    # client = FeathrClient()
    actual = ['f_account_movies_watched_sec_7d', 'test_1']
    result = list(client.get_filtered_features(project_name="DEBUG_ZERO_FEATURES", agg_func='sum', agg_window='7d').keys())

    assert sorted(actual) == sorted(result), "Actual != result"


def test_filter_feature_by_tags(client : FeathrClient):
    # client = FeathrClient()
    actual = ['f_account_console_watched_sec_7d',
              'f_account_unknown_watched_sec_7d',
              'f_account_evening_watched_sec_7d',
              'f_account_family_watched_sec_7d',
              'f_account_older365d_watched_sec_7d',
              'f_account_tv_watched_sec_7d',
              'f_account_prime_watched_sec_7d',
              'f_account_mobile_watched_sec_7d',
              'f_account_afternoon_watched_sec_7d',
              'f_account_total_watched_secs_7d',
              'f_account_drama_watched_sec_7d',
              'f_account_desktop_watched_sec_7d',
              'f_account_latenight_watched_sec_7d',
              'f_account_reality_watched_sec_7d',
              'f_account_older30d_watched_sec_7d',
              'f_account_movies_watched_sec_7d',
              'f_account_older7d_watched_sec_7d',
              'f_account_morning_watched_sec_7d',
              'f_account_weekend_watched_sec_7d',
              'f_account_weekday_watched_sec_7d',
              'f_account_series_watched_sec_7d',
              'f_account_fantasy_watched_sec_7d',
              'f_account_comedy_watched_sec_7d']

    result = list(client.get_filtered_features(project_name="short_term_ltv_v5", agg_window='7d',
                                               tags={'entity_key': 'HBO_UUID'}).keys())

    assert sorted(actual) == sorted(result), "Actual != result "


def test_filter_feature_by_transExpr(client : FeathrClient):
    # client = FeathrClient()
    actual = ['DAILY_COMCAST_X1_PERCENT_ADJ']
    result = list(client.get_filtered_features(project_name="MAX_TEST_1", transform_expr="DAILY_COMCAST_X1_PERCENT_ADJ").keys())

    assert sorted(actual) == sorted(result), " Actual != result"


