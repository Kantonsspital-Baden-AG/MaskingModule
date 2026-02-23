from masking.base_operations.operation_token_match import TokenMatchOperationBase
from masking.mask.operations.operation import PandasOperation


class TokenMatchOperation(PandasOperation, TokenMatchOperationBase):
    """Token matching operation."""
