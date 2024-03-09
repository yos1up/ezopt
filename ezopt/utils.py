import random
from pathlib import Path


def safe_float(x: str) -> float | None:
    try:
        return float(x)
    except ValueError:
        return None

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