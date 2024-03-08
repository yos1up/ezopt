import argparse
import json
from pathlib import Path
import subprocess
import itertools
import re

from pydantic import BaseModel

from ezopt.utils import compute_product, get_random_hex, read_text_file, write_text_file


def extract_cpp_file(cmd: str) -> str:
    cpp_files = re.findall(r"[\w\./]+\.cpp", cmd)
    if len(cpp_files) == 0:
        raise ValueError("No C++ source file is found")
    elif len(cpp_files) > 1:
        raise ValueError("Multiple C++ source files are found")
    return cpp_files[0]


ChoiceType = bool | float | int | str
# NOTE: pydantic の仕様上，例えば int | float | bool | str の順番だと，float が int にキャストされてしまう


class HyperParameter(BaseModel):
    original: str
    hash: str
    name: str
    choices: list[ChoiceType]


class SourceIterator:
    def __init__(self, source: str):
        self.hps, self.source = self.__class__.collect_hyper_parameters(source)
        self.product = itertools.product(*[hp.choices for hp in self.hps])
        self.length = compute_product([len(hp.choices) for hp in self.hps])
    
    def apply_hp_values(self, values: list[ChoiceType]) -> str:
        assert len(values) == len(self.hps)
        source = self.source
        for hp, value in zip(self.hps, values):
            source = source.replace(hp.hash, self.__class__._to_cpp_repr(value))
        return source
    
    def __len__(self) -> int:
        return self.length
    
    def __iter__(self):
        return self
    
    def __next__(self) -> tuple[tuple[ChoiceType], str]:
        values = next(self.product)
        return values, self.apply_hp_values(values)
    
    @staticmethod
    def _to_cpp_repr(x: ChoiceType) -> str:
        if isinstance(x, bool):
            return "true" if x else "false"
        elif isinstance(x, (int, float)):
            return str(x)
        elif isinstance(x, str):
            return f'"{x}"'
        else:
            raise ValueError(f"Unsupported choice type: {type(x)}")


    @staticmethod
    def collect_hyper_parameters(source: str) -> tuple[list[HyperParameter], str]:
        # 全てのプレースホルダをランダムなハッシュに置き換える
        hash_to_original: dict[str, str] = {}
        
        hp_pattern = r"\(([^)]+)\)/\*(HP.*):(.+)\*/"

        def _fn_replacer(m):
            hash = get_random_hex(24)
            hash_to_original[hash] = m.group(1)
            return f"({hash})/*{m.group(2)}:{m.group(3)}*/"

        source = re.sub(
            hp_pattern,
            _fn_replacer,
            source
        )

        # HyperParameer のリストを取得する
        matches = re.findall(hp_pattern, source)
        hps: list[HyperParameter] = []
        for m in matches:
            choices = json.loads(m[2], strict=False)
            assert isinstance(choices, list)
            hps.append(HyperParameter(
                original=hash_to_original[m[0]],
                hash=m[0],
                name=m[1],
                choices=choices
            ))
        return hps, source



def main():  # NOTE: パッケージのエントリーポイントとして使われる
    parser = argparse.ArgumentParser(description="EZOPT: Easy Optimization")
    parser.add_argument("CMD", type=str, help="Command to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()

    CMD: str = args.CMD
    VERBOSE: bool = args.verbose
    # CMD == "g++ main.cpp; ./a.out < in.txt"

    # cmd の中から，対象のC++ソースファイルを認識する
    cpp_file = extract_cpp_file(CMD)

    iterator = SourceIterator(read_text_file(cpp_file))

    # HP の確認
    print("HyperParameters:")
    for hp in iterator.hps:
        print(f"    [{hp.name}] {hp.original} <-- {hp.choices}")
    if input("Continue? [y/n] ") != "y":
        exit()

    this_dir = Path(__file__).parent
    tmp_file_path = this_dir / ".." / "tmp" / "_tmp.cpp"
    for i, (param, mod_source) in enumerate(iterator, start=1):
        print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] START =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")
        # source を一時ディレクトリ内の一時ファイルに書き出す
        write_text_file(tmp_file_path, mod_source)
        # cmd の cppfile 部分を一時ファイルのパスに差し替える
        mod_cmd = CMD.replace(cpp_file, str(tmp_file_path))
        if VERBOSE:
            print(f"{mod_cmd=}")
        # 実行する
        subprocess.run(mod_cmd, shell=True)
        print(f"=:=:=:=:=:=:=:=:=:=:=:=:=:=:= {param=} [{i} / {len(iterator)}] END =:=:=:=:=:=:=:=:=:=:=:=:=:=:=")


if __name__ == "__main__":
    main()