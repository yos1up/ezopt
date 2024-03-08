

from pathlib import Path
import re
import subprocess

from ezopt.utils import write_text_file


class SourceEvaluator:
    """
    具体値代入後のソースを受け取って，それを実行する（さらにオプションによってはその評価値を返す）クラス
    """
    def __init__(self, original_cmd: str):
        self.tmp_file_path = self.__class__.get_tmp_file_path()

        self.cpp_file = self.__class__.extract_cpp_file(original_cmd)
        self.mod_cmd = original_cmd.replace(self.cpp_file, str(self.tmp_file_path))

    def evaluate(self, mod_source: str) -> float | None:
        # source を一時ファイルに書き出す
        write_text_file(self.tmp_file_path, mod_source)
        # cmd の cppfile 部分を一時ファイルのパスに差し替えた mod_cmd を実行する
        subprocess.run(self.mod_cmd, shell=True)

    @staticmethod
    def extract_cpp_file(cmd: str) -> str:
        cpp_files = re.findall(r"[\w\./]+\.cpp", cmd)
        if len(cpp_files) == 0:
            raise ValueError("No C++ source file is found")
        elif len(cpp_files) > 1:
            raise ValueError("Multiple C++ source files are found")
        return cpp_files[0]

    @staticmethod
    def get_tmp_file_path() -> Path:
        this_dir = Path(__file__).parent
        return this_dir / ".." / "tmp" / "_tmp.cpp"
