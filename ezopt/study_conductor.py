import optuna

from ezopt.source_evaluator import SourceEvaluator
from ezopt.source_parameterizer import SourceParameterizer


class StudyConductor:
    def __init__(self, parameterizer: SourceParameterizer, evaluator: SourceEvaluator):
        self.parameterizer = parameterizer
        self.evaluator = evaluator
    
    def run(self, n_trials: int, direction: str) -> optuna.study.Study:
        study = optuna.create_study(direction=direction)
        study.optimize(
            lambda trial: self.__class__.objective(trial, self.parameterizer),
            n_trials=n_trials
        )
        return study
    
    @staticmethod
    def objective(trial: optuna.Trial, parameterizer: SourceParameterizer) -> float:
        values = [parameterizer.hps[i].choices[trial.suggest_int(f"hp_{i}", 0, len(parameterizer.hps[i].choices) - 1)] for i in range(len(parameterizer.hps))]
        source = parameterizer.apply_hp_values(values)
        return 0.0  # NOTE: ここに実際の評価関数を書く
