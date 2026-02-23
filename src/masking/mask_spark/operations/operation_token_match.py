from masking.mask.operations.operation_token_match import (
    TokenMatchOperation as TokenMatchPandas,
)
from masking.mask_spark.operations.operation import SparkOperation


class TokenMatchOperation(SparkOperation, TokenMatchPandas):
    """Masks a column using a fake date generator."""
