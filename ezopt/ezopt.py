import argparse
from pathlib import Path
import subprocess
import itertools
import re

from ezopt.models import ChoiceType
from ezopt.source_evaluator import SourceEvaluator
from ezopt.source_parameterizer import SourceParameterizer

from ezopt.utils import compute_product, read_text_file, write_text_file


def extract_cpp_file(cmd: str) -> str:
    cpp_files = re.findall(r"[\w\./]+\.cpp", cmd)
    if len(cpp_files) == 0:
        raise ValueError("No C++ source file is found")
    elif len(cpp_files) > 1:
        raise ValueError("Multiple C++ source files are found")
    return cpp_files[0]


class SourceIterator:
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


def main():  # NOTE: パッケージのエントリーポイントとして使われる
    parser = argparse.ArgumentParser(description="EZOPT: Easy Optimization")
    parser.add_argument("CMD", type=str, help="Command to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()

    CMD: str = args.CMD  # CMD == "g++ main.cpp; ./a.out < in.txt"

    # 編集後ソースを評価するクラス
    evaluator = SourceEvaluator(CMD)

    # 編集前ソースをパラメータ化するクラス
    parameterizer = SourceParameterizer(read_text_file(evaluator.cpp_file))

    # HP の確認
    print("HyperParameters:")
    for hp in parameterizer.hps:
        print(f"    [{hp.name}] {hp.original} <-- {hp.choices}")
    if input("Continue? [y/n] ") != "y":
        print("Cancelled")
        exit()

    # グリッドサーチのためのイテレータ
    iterator = SourceIterator(parameterizer)

    for i, (param, mod_source) in enumerate(iterator, start=1):
        print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] START =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")
        evaluator.evaluate(mod_source)
        print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] END =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")


if __name__ == "__main__":
    main()