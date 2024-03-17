import itertools
import sys
from typing import Any
import optuna
from pydantic import BaseModel
from ezopt.models import ChoiceType, HyperParameterWithChoices, HyperParameterWithRange
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
        # self.hps = [hp for hp in self.parameterizer.hps if isinstance(hp, HyperParameterWithChoices)]
        # assert len(self.hps) == len(self.parameterizer.hps), "BayesianOptimization is only supported for HyperParameterWithChoices"
        self.hps = self.parameterizer.hps
        self.executor = executor
        self.evaluator = evaluator
    
    def run(self, n_trials: int, direction: str) -> StudyResult:
        study = optuna.create_study(direction=direction)

        try:
            study.optimize(
                lambda trial: self._objective(
                    trial,
                ),
                n_trials=n_trials
            )
        except KeyboardInterrupt:
            pass

        return StudyResult(
            trial_results=[(self._decode_params(t.params), t.value) for t in study.trials],
            study=study,
            best_params=self._decode_params(study.best_params) if study.best_params is not None else None,
            best_value=study.best_value
        )

    def _decode_params(self, params: dict[str, Any]) -> tuple[ChoiceType, ...]:
        """
        optuna params を実際のハイパーパラメータ値に変換する
        """
        raw_params: list[ChoiceType] = []
        for hp in self.hps:
            if isinstance(hp, HyperParameterWithChoices):
                # raw_params.append(hp.choices[params[hp.name]])
                raw_params.append(params[hp.name])
            elif isinstance(hp, HyperParameterWithRange):
                raw_params.append(params[hp.name])
            else:
                raise RuntimeError(f"Unsupported hyperparameter type: {hp}")

        return tuple(raw_params)
    
    def _objective(
        self,
        trial: optuna.Trial,
    ) -> float:
        params = self._suggest_params(trial)
        # print(f"[suggestion] {params=}")
        mod_source = self.parameterizer.apply_params(params)
        result = self.executor.execute(mod_source)
        value = self.evaluator.evaluate(result)
        # print(f"    {value=}")
        if value is None:
            raise RuntimeError(f"Value extraction failed. \n----\n{self.evaluator=}\n----\n{result=}")
        return value
    
    def _suggest_params(self, trial: optuna.Trial) -> tuple[ChoiceType, ...]:
        """
        HyperParameter たちから optuna の suggestion を行う
        """
        raw_params: list[ChoiceType] = []
        for i in range(len(self.hps)):
            hp = self.hps[i]
            if isinstance(hp, HyperParameterWithChoices):
                # TODO: float のみや int のみのケースは suggest_(int|float) + GridSampler で対応したほうが better と思われる
                # raw_params.append(hp.choices[trial.suggest_int(f"hp_{i}", 0, len(hp.choices) - 1)])
                raw_params.append(trial.suggest_categorical(hp.name, hp.choices))
            elif isinstance(hp, HyperParameterWithRange):
                raw_params.append(trial.suggest_float(hp.name, hp.low, hp.high, log=hp.log))
            else:
                raise RuntimeError(f"Unsupported hyperparameter type: {hp}")
            
        return tuple(raw_params)


class GridSearchSourceIterator:
    def __init__(self, parameterizer: SourceParameterizer):
        self.parameterizer = parameterizer
        hps = [hp for hp in self.parameterizer.hps if isinstance(hp, HyperParameterWithChoices)]
        assert len(hps) == len(self.parameterizer.hps), "GridSearch is only supported for HyperParameterWithChoices"
        self.product: itertools.product[tuple[ChoiceType, ...]] = itertools.product(*[hp.choices for hp in hps])
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
        trial_results: list[tuple[tuple[ChoiceType, ...], float | None]]  = []
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
