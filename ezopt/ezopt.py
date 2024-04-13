import argparse
import datetime
from pathlib import Path
import re

from ezopt.output_evaluator import OutputEvaluator
from ezopt.source_executor import SourceExecutor
from ezopt.source_parameterizer import SourceParameterizer
from ezopt.study_conductor import BayesianOptimizationStudyConductor, GridSearchStudyConductor
from ezopt.study_visualizer import StudyVisualizer
from ezopt.utils import read_text_file, write_text_file


def extract_cpp_file(cmd: str) -> str:
    cpp_files = re.findall(r"[\w\./]+\.cpp", cmd)
    if len(cpp_files) == 0:
        raise ValueError("No C++ source file is found")
    elif len(cpp_files) > 1:
        raise ValueError("Multiple C++ source files are found")
    return cpp_files[0]


def main() -> None:  # NOTE: パッケージのエントリーポイントとして使われる
    parser = argparse.ArgumentParser(description="EZOPT: Easy Optimization")
    parser.add_argument("CMD", type=str, help="Command to run. Example: 'g++ main.cpp && ./a.out < in.txt'")
    parser.add_argument("-p", "--value-pattern", type=str, default="Score: (.+)", help="Pattern to extract value")
    parser.add_argument("-M", "--maximize", action="store_true", help="Maximize the value")
    parser.add_argument("-m", "--minimize", action="store_true", help="Minimize the value")
    parser.add_argument("-n", "--trials", type=int, default=100, help="Number of trials")
    parser.add_argument("-g", "--grid", action="store_true", help="Grid search mode")
    parser.add_argument("-o", "--output-dir", type=str, help="Output directory")
    # parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()

    CMD: str = args.CMD
    VALUE_PATTERN: str = args.value_pattern
    if args.maximize and args.minimize:
        raise ValueError("Cannot specify both --maximize and --minimize")
    OPTIMIZE: bool = args.maximize or args.minimize
    DIRECTION: str = "maximize" if args.maximize else "minimize" if args.minimize else "none"
    N_TRIALS: int = args.trials
    GRID: bool = args.grid
    OUTPUT_DIR: Path = Path(args.output_dir) if args.output_dir is not None else Path(f"./ezopt-results/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}/")

    # 編集後ソースを実行するクラス
    executor = SourceExecutor(CMD)

    # 編集前ソースをパラメータ化するクラス
    parameterizer = SourceParameterizer(read_text_file(executor.cpp_file))

    if len(parameterizer.hps) == 0:
        raise ValueError("No hyperparameters are found")

    # 各種情報の確認
    print("HyperParameters:")
    for hp in parameterizer.hps:
        print(f"    - {hp}")
    print("Optimization Direction:", DIRECTION)
    print("Output Directory (will be created if not exists):", OUTPUT_DIR)
    if input("Continue? [y/n] ") != "y":
        exit()

    evaluator = OutputEvaluator(VALUE_PATTERN)
    if OPTIMIZE:
        # 最適化を目的としている場合
        study_conductor = BayesianOptimizationStudyConductor(parameterizer, executor, evaluator)
        study_result = study_conductor.run(n_trials=N_TRIALS, direction=DIRECTION, sampling="grid" if GRID else "tpe")
        print("Summary:")
        print(f"    - Best params: {study_result.best_params}")
        print(f"    - Best value: {study_result.best_value}")
        if study_result.study is not None:
            # 可視化の保存
            StudyVisualizer.visualize(study_result.study, OUTPUT_DIR)
            # 最適ソースの保存
            if study_result.best_params is not None:
                best_source = parameterizer.apply_params(study_result.best_params)
                write_text_file(OUTPUT_DIR / "best_source.cpp", best_source)
            print(f"Results are saved in the directory {OUTPUT_DIR}")
            # TODO: visualize は定期的に保存されるようにする
    else:
        # 最適化を特に目的としていない場合（単に全ての条件で実行したい場合）
        # NOTE: スコア形式を指定するのが面倒だが，とりあえず全通り走らせて欲しい，生出力を眺めたい，というニーズに対してはこれで対応
        # TODO: こちらのモードはいずれ消したい（上に統合したい）
        grid_search_study_conductor = GridSearchStudyConductor(parameterizer, executor, evaluator)
        study_result = grid_search_study_conductor.run()
        print(f"{study_result=}")
        

if __name__ == "__main__":
    main()