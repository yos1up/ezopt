import itertools
from typing import Any
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
    best_params: tuple[ChoiceType, ...] | None
    best_value: float | None

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
            trial_results=[(self._decode_params(t.params), t.value) for t in study.trials],
            study=study,
            best_params=self._decode_params(study.best_params) if study.best_params is not None else None,
            best_value=study.best_value
        )

    def _decode_params(self, params: dict[str, Any]) -> tuple[ChoiceType, ...]:
        return tuple([self.parameterizer.hps[i].choices[params[f"hp_{i}"]] for i in range(len(self.parameterizer.hps))])
    
    @staticmethod
    def objective(
        trial: optuna.Trial,
        parameterizer: SourceParameterizer,
        executor: SourceExecutor,
        evaluator: OutputEvaluator        
    ) -> float:
        params = [parameterizer.hps[i].choices[trial.suggest_int(f"hp_{i}", 0, len(parameterizer.hps[i].choices) - 1)] for i in range(len(parameterizer.hps))]
        mod_source = parameterizer.apply_params(params)
        print(f"[suggestion] {params=}")
        result = executor.execute(mod_source)
        value = evaluator.evaluate(result)
        print(f"    {value=}")
        if value is None:
            raise RuntimeError(f"Value extraction failed. \n----\n{evaluator=}\n----\n{result=}")
        return value


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
        return values, self.parameterizer.apply_params(values)


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
            print(f"[{i} / {len(iterator)}] {param=}")
            result = self.executor.execute(mod_source)
            value = self.evaluator.evaluate(result)
            trial_results.append((param, value))
            print(f"    {value=}")
        
        trial_results_with_value = [(param, value) for param, value in trial_results if value is not None]
        best_trial = max(trial_results_with_value, key=lambda x: x[1]) if len(trial_results_with_value) > 0 else None
        return StudyResult(
            trial_results=trial_results,
            study=None,
            best_params=best_trial[0] if best_trial is not None else None,
            best_value=best_trial[1] if best_trial is not None else None
        )
