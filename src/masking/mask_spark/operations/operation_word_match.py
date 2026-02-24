from masking.mask.operations.operation_word_match import (
    WordMatchOperation as WordMatchPandas,
)
from masking.mask_spark.operations.operation import SparkOperation


class WordMatchOperation(SparkOperation, WordMatchPandas):
    """Masks a column using a fake date generator."""
