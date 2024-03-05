import argparse
import json
from pathlib import Path
import random
import subprocess
import itertools
import re

from pydantic import BaseModel


def compute_product(xs: list[int]) -> int:
    ans = 1
    for x in xs:
        ans *= x
    return ans


def get_random_hex(n: int) -> str:
    # 16進数の乱数を生成する n 桁の
    return "".join(random.choices("0123456789abcdef", k=n))


def read_text_file(path: str | Path) -> str:
    with open(path, "r") as f:
        return f.read()


def write_text_file(path: str | Path, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


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
    
    def __len__(self) -> int:
        return self.length
    
    def __iter__(self):
        return self
    
    def __next__(self) -> tuple[tuple[ChoiceType], str]:
        # product から一つ取り出して，source のプレースホルダを置き換える
        choices = next(self.product)
        source = self.source
        for hp, choice in zip(self.hps, choices):
            source = source.replace(hp.hash, self.__class__._to_cpp_repr(choice))
        return choices, source
    
    @staticmethod
    def _to_cpp_repr(x: ChoiceType) -> str:
        if isinstance(x, (int, float)):
            return str(x)
        elif isinstance(x, str):
            return f'"{x}"'
        elif isinstance(x, bool):
            return "true" if x else "false"
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



if __name__ == "__main__":
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
