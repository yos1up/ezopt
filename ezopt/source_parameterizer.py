


import json
import re
from ezopt.models import ChoiceType, HyperParameter
from ezopt.utils import get_random_hex


class SourceParameterizer:
    """
    ソースを受け取り，以下をする
    - ソース内の HP を把握する
    - HP の具体値を受け取ると，それらをソースに埋め込んだものを返す
    """
    def __init__(self, source: str):
        self.hps, self.source = self.__class__.collect_hyper_parameters(source)
    
    def apply_params(self, values: list[ChoiceType]) -> str:
        assert len(values) == len(self.hps)
        source = self.source
        for hp, value in zip(self.hps, values):
            source = source.replace(hp.hash, self.__class__._to_cpp_repr(value))
        return source
    
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
