

import re
from ezopt.models import ExecutionResult
from ezopt.utils import safe_float


class OutputEvaluator:
    """
    実行結果 (ExecutionResult) を受け取り，その出力を評価してスコアを返すクラス
    """
    def __init__(self, value_pattern: str):
        self.value_pattern = value_pattern

    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        value = self.extract_value(execution_result.stdout)
        if value is None:
            value = self.extract_value(execution_result.stderr)
        
        return value
    
    def extract_value(self, output: str) -> float | None:
        value = safe_float(res.group(1)) if (res := re.search(self.value_pattern, output)) is not None else None
        return value
    
    def __repr__(self):
        return f"OutputEvaluator(value_pattern={self.value_pattern})"


class TrivialOutputEvaluator:
    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        return None
