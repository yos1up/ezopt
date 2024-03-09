from pydantic import BaseModel


ChoiceType = bool | float | int | str
# NOTE: pydantic の仕様上，例えば int | float | bool | str の順番だと，float が int にキャストされてしまう


class HyperParameter(BaseModel):
    original: str
    hash: str
    name: str
    choices: list[ChoiceType]


class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    return_code: int
