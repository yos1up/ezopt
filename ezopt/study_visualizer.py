

import json
import os
from pathlib import Path
import pickle

import optuna


class StudyVisualizer:
    @classmethod
    def visualize(
        cls,
        study: optuna.study.Study,
        output_dir: Path
    ) -> None:
        """
        optuna の study を受け取って，その結果を可視化してディレクトリに書き出す
        """
        os.makedirs(output_dir, exist_ok=True)
        with open(output_dir / "stats.json", "w") as f:
            json.dump({
                "n_trials": len(study.trials),
                "best_value": study.best_value,
                "best_params": study.best_params,
                "direction": study.direction,
                "trials": [
                    {
                        "params": t.params,
                        "value": t.value,
                    }
                    for t in study.trials
                ]
            }, f, indent=2, ensure_ascii=False)
        optuna.visualization.plot_optimization_history(study).write_html(output_dir / "optimization_history.html")
        optuna.visualization.plot_parallel_coordinate(study).write_html(output_dir / "parallel_coordinate.html")
        optuna.visualization.plot_param_importances(study).write_html(output_dir / "param_importances.html")
        importances: dict[str, float] = optuna.importance.get_param_importances(study)
        # TODO: plot と get の結果が微妙にずれる？
        print(f"{importances=}")
        important_params = sorted(importances, key=lambda k: -importances[k])[:3]
        optuna.visualization.plot_contour(study, params=important_params).write_html(output_dir / "contour.html")
        # NOTE: contour は非常に重たいので，重要度が高いと思われる 3 パラメータに絞って描画する
        with open(output_dir / "study.pkl", "wb") as f:
            pickle.dump(study, f)
