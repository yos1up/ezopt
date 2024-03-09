

import re
from ezopt.models import ExecutionResult
from ezopt.utils import safe_float


class OutputEvaluator:
    """
    実行結果 (ExecutionResult) を受け取り，その出力を評価してスコアを返すクラス
    """
    def __init__(self, score_pattern: str):
        self.score_pattern = score_pattern

    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        score = self.extract_score(execution_result.stdout)
        if score is None:
            score = self.extract_score(execution_result.stderr)
        
        return score
    
    def extract_score(self, output: str) -> float | None:
        score = safe_float(res.group(1)) if (res := re.search(self.score_pattern, output)) is not None else None
        return score
    
    def __repr__(self):
        return f"OutputEvaluator(score_pattern={self.score_pattern})"


class TrivialOutputEvaluator:
    def evaluate(self, execution_result: ExecutionResult) -> float | None:
        return None
