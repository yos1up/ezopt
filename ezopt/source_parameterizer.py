


import json
import re
from ezopt.models import ChoiceType, HyperParameter, HyperParameterWithChoices, HyperParameterWithRange
from ezopt.utils import get_random_hex


class SourceParameterizer:
    """
    ソースを受け取り，以下をする
    - ソース内の HP を把握する
    - HP の具体値を受け取ると，それらをソースに埋め込んだものを返す
    """
    def __init__(self, source: str):
        self.hps, self.source = self.__class__.collect_hyper_parameters(source)
    
    def apply_params(self, values: tuple[ChoiceType, ...]) -> str:
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

    @classmethod
    def collect_hyper_parameters(cls, source: str) -> tuple[list[HyperParameter], str]:
        # 全てのプレースホルダをランダムなハッシュに置き換える
        hash_to_original: dict[str, str] = {}
        
        hp_pattern = r"\(([^)]+)\)\s*/\*\s*(HP.*)\s*:\s*(.+)\s*\*/"

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
        annotation_matches = re.findall(hp_pattern, source)
        hps: list[HyperParameter] = []
        for hash, name, search_space_spec in annotation_matches:
            # search_space_spec をパースし，その結果ごとに異なる種類の HP を生成する
            if (choices := cls.try_to_parse_search_space_spec_as_choices(search_space_spec)) is not None:
                hps.append(HyperParameterWithChoices(
                    original=hash_to_original[hash],
                    hash=hash,
                    name=name,
                    choices=choices           
                ))
            elif (spec := cls.try_to_parse_search_space_spec_as_range(search_space_spec)) is not None:
                low, high, log = spec
                hps.append(HyperParameterWithRange(
                    original=hash_to_original[hash],
                    hash=hash,
                    name=name,
                    low=low,
                    high=high,
                    log=log
                ))
            else:
                raise ValueError(f"Invalid search space spec: {search_space_spec=}")
        return hps, source
    
    @staticmethod
    def try_to_parse_search_space_spec_as_choices(search_space_spec: str) -> list[ChoiceType] | None:
        try:
            return json.loads(search_space_spec, strict=False)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def try_to_parse_search_space_spec_as_range(search_space_spec: str) -> tuple[float, float, bool] | None:
        m = re.match(r"(-?\d+(?:\.\d+)?)\s* -- \s*(-?\d+(?:\.\d+)?)", search_space_spec)
        if m:
            return float(m.group(1)), float(m.group(2)), False
        m_log = re.match(r"(-?\d+(?:\.\d+)?)\s* --- \s*(-?\d+(?:\.\d+)?)", search_space_spec)
        if m_log:
            return float(m_log.group(1)), float(m_log.group(2)), True
        return None
