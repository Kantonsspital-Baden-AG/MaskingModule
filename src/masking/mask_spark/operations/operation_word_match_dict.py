from masking.mask.operations.operation_word_match_dict import (
    WordMatchDictOperation as WordMatchDictPandas,
)
from masking.mask_spark.operations.operation import SparkOperation


class WordMatchDictOperation(SparkOperation, WordMatchDictPandas):
    """Word matching operation."""
