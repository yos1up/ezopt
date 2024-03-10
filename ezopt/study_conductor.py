import itertools
import optuna
from pydantic import BaseModel
from ezopt.models import ChoiceType
from ezopt.output_evaluator import OutputEvaluator

from ezopt.source_executor import SourceExecutor
from ezopt.source_parameterizer import SourceParameterizer
from ezopt.utils import compute_product


class StudyResult(BaseModel):
    trial_results: list[tuple[tuple[ChoiceType, ...], float | None]]
    study: optuna.study.Study | None
    best_hp_values: tuple[ChoiceType, ...] | None

    class Config:
        arbitrary_types_allowed = True

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
    
    def run(self, n_trials: int, direction: str) -> StudyResult:
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
        return StudyResult(
            trial_results=[(t.params, t.value) for t in study.trials],
            study=study,
            best_hp_values=study.best_params
        )
    
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
    
    def __next__(self) -> tuple[tuple[ChoiceType, ...], str]:
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
    
    def run(self) -> StudyResult:
        trial_results: list[tuple[tuple[ChoiceType, ...], float]]  = []
        iterator = GridSearchSourceIterator(self.parameterizer)
        for i, (param, mod_source) in enumerate(iterator, start=1):
            # print(f"=:=:=:=:=:=:=:=:=  {param=} [{i} / {len(iterator)}] START  =:=:=:=:=:=:=:=:=")
            print(f"[{i} / {len(iterator)}] {param=}")
            result = self.executor.execute(mod_source)
            score = self.evaluator.evaluate(result)
            trial_results.append((param, score))
            # print(f"=:=:=:=:=:=:=:=:=  {param=} [{i} / {len(iterator)}] END (Score: {score})  =:=:=:=:=:=:=:=:=")
            print(f"    Score: {score}")
        
        trial_results_with_score = [(param, score) for param, score in trial_results if score is not None]
        return StudyResult(
            trial_results=trial_results,
            study=None,
            best_hp_values=max(trial_results_with_score, key=lambda x: x[1])[0] if len(trial_results_with_score) > 0 else None
        )
