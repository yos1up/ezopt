import itertools
import optuna
from ezopt.models import ChoiceType
from ezopt.output_evaluator import OutputEvaluator

from ezopt.source_executor import SourceExecutor
from ezopt.source_parameterizer import SourceParameterizer
from ezopt.utils import compute_product


class BayesianOptimizationStudyConductor:
    def __init__(
        self,
        parameterizer: SourceParameterizer,
        executor: SourceExecutor,
        evaluator: OutputEvaluator
    ):
        self.parameterizer = parameterizer
        self.executor = executor
        self.evaluator = evaluator
    
    def run(self, n_trials: int, direction: str) -> optuna.study.Study:
        study = optuna.create_study(direction=direction)
        study.optimize(
            lambda trial: self.__class__.objective(
                trial,
                self.parameterizer,
                self.executor,
                self.evaluator
            ),
            n_trials=n_trials
        )
        return study
    
    @staticmethod
    def objective(
        trial: optuna.Trial,
        parameterizer: SourceParameterizer,
        executor: SourceExecutor,
        evaluator: OutputEvaluator        
    ) -> float:
        values = [parameterizer.hps[i].choices[trial.suggest_int(f"hp_{i}", 0, len(parameterizer.hps[i].choices) - 1)] for i in range(len(parameterizer.hps))]
        mod_source = parameterizer.apply_hp_values(values)
        result = executor.execute(mod_source)
        score = evaluator.evaluate(result)
        if score is None:
            raise RuntimeError(f"Score extraction failed. \n----\n{evaluator=}\n----\n{result=}")
        return score

class GridSearchSourceIterator:
    def __init__(self, parameterizer: SourceParameterizer):
        self.parameterizer = parameterizer
        hps = self.parameterizer.hps
        self.product = itertools.product(*[hp.choices for hp in hps])
        self.length = compute_product([len(hp.choices) for hp in hps])
    
    def __len__(self) -> int:
        return self.length
    
    def __iter__(self):
        return self
    
    def __next__(self) -> tuple[tuple[ChoiceType], str]:
        values = next(self.product)
        return values, self.parameterizer.apply_hp_values(values)


class GridSearchStudyConductor:
    def __init__(
        self,
        parameterizer: SourceParameterizer,
        executor: SourceExecutor,
        evaluator: OutputEvaluator
    ):
        self.parameterizer = parameterizer
        self.executor = executor
        self.evaluator = evaluator
    
    def run(self) -> None:
        iterator = GridSearchSourceIterator(self.parameterizer)
        for i, (param, mod_source) in enumerate(iterator, start=1):
            print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] START =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")
            self.executor.execute(mod_source)
            print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] END =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")
