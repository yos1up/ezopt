import argparse
import re

from ezopt.output_evaluator import OutputEvaluator, TrivialOutputEvaluator
from ezopt.source_executor import SourceExecutor
from ezopt.source_parameterizer import SourceParameterizer
from ezopt.study_conductor import BayesianOptimizationStudyConductor, GridSearchStudyConductor

from ezopt.utils import read_text_file


def extract_cpp_file(cmd: str) -> str:
    cpp_files = re.findall(r"[\w\./]+\.cpp", cmd)
    if len(cpp_files) == 0:
        raise ValueError("No C++ source file is found")
    elif len(cpp_files) > 1:
        raise ValueError("Multiple C++ source files are found")
    return cpp_files[0]


def main():  # NOTE: パッケージのエントリーポイントとして使われる
    parser = argparse.ArgumentParser(description="EZOPT: Easy Optimization")
    parser.add_argument("CMD", type=str, help="Command to run")
    parser.add_argument("--value-pattern", type=str, default="Score: (.+)", help="Pattern to extract value")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()

    CMD: str = args.CMD  # CMD == "g++ main.cpp; ./a.out < in.txt"
    VALUE_PATTERN: str = args.value_pattern


    # 編集後ソースを評価するクラス
    executor = SourceExecutor(CMD)

    # 編集前ソースをパラメータ化するクラス
    parameterizer = SourceParameterizer(read_text_file(executor.cpp_file))
    # HP の確認
    print("HyperParameters:")
    for hp in parameterizer.hps:
        print(f"    [{hp.name}] {hp.original} <-- {hp.choices}")
    if input("Continue? [y/n] ") != "y":
        exit()

    evaluator = OutputEvaluator(VALUE_PATTERN)
    if False:
        study_conductor = GridSearchStudyConductor(parameterizer, executor, evaluator)
        study_result = study_conductor.run()
        print(f"{study_result=}")
    else:
        study_conductor = BayesianOptimizationStudyConductor(parameterizer, executor, evaluator)
        study_result = study_conductor.run(n_trials=12, direction="maximize")
        print(f"{study_result=}")


if __name__ == "__main__":
    main()