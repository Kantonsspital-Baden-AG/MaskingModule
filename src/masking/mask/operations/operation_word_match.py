from masking.base_operations.operation_word_match import WordMatchOperationBase
from masking.mask.operations.operation import PandasOperation


class WordMatchOperation(PandasOperation, WordMatchOperationBase):
    """Word matching operation."""
