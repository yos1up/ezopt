

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
        
        fig = optuna.visualization.plot_param_importances(study)
        fig.write_html(output_dir / "param_importances.html")
        params_sorted_by_importance = list(fig.data[0].y[::-1])
        # NOTE: get_param_importances で再計算するのは重たい（また seed を合わせないと結果が再現しない）ため，
        # visualization fig から重要パラメータを抽出するようにしている
        
        if len(params_sorted_by_importance) > 1:
            optuna.visualization.plot_contour(study, params=params_sorted_by_importance[:3]).write_html(output_dir / "contour.html")
            # NOTE: contour を全変数について出力すると html ファイルサイズが膨大となるので，重要度が高いと思われる 3 パラメータに絞って描画している
        
        optuna.visualization.plot_slice(study, params=params_sorted_by_importance[:3]).write_html(output_dir / "slice.html")

        with open(output_dir / "study.pkl", "wb") as f:
            pickle.dump(study, f)
