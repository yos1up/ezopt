from pydantic import BaseModel


ChoiceType = bool | float | int | str
# NOTE: pydantic の仕様上，例えば int | float | bool | str の順番だと，float が int にキャストされてしまう


class HyperParameter(BaseModel):
    original: str
    hash: str
    name: str

    def __str__(self):
        return f"{self.__class__.__name__}"


class HyperParameterWithChoices(HyperParameter):
    choices: list[ChoiceType]

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, choices={self.choices})"


class HyperParameterWithRange(HyperParameter):
    low: float
    high: float
    log: bool

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, low={self.low}, high={self.high}, log={self.log})"


class ExecutionResult(BaseModel):
    stdout: str
    stderr: str
    return_code: int
