

import math
import re
from ezopt.models import ExecutionResult
from ezopt.utils import safe_float


class OutputEvaluator:
    """
    実行結果 (ExecutionResult) を受け取り，その出力を評価して評価値(value)を返すクラス
    """
    def __init__(
        self,
        value_pattern: str,
        value_aggregation: str = "sum",
    ):
        self.value_pattern = value_pattern
        self.value_aggregation = value_aggregation

    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        values_from_stdout = self.extract_values(execution_result.stdout)
        values_from_stderr = self.extract_values(execution_result.stderr)
        if len(values_from_stdout) > 0 and len(values_from_stderr) > 0:
            raise RuntimeError("Both stdout and stderr contain values. This is ambiguous.")
        
        values = values_from_stdout if len(values_from_stdout) > 0 else values_from_stderr

        if len(values) == 0:
            return None
        
        if self.value_aggregation == "sum":
            value = sum(values)
        elif self.value_aggregation == "sumlog":
            value = sum(math.log(v) for v in values if v > 0)
        else:
            raise ValueError(f"Unsupported value_aggregation: {self.value_aggregation}")
        
        return value
    
    def extract_values(self, output: str) -> list[float]:
        """
        output から value として解釈可能な値を全て抽出して返す
        """
        values = [
            value for m in re.finditer(self.value_pattern, output, re.MULTILINE)
            if (value := safe_float(m.group(1))) is not None
        ]
        return values
    
    def __repr__(self):
        return f"OutputEvaluator(value_pattern={self.value_pattern}, value_aggregation={self.value_aggregation})"

# TODO: 複数のスコアを受け取って，それらの和や対数和で評価するようなEvaluatorを作る？

class TrivialOutputEvaluator:
    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        return None
