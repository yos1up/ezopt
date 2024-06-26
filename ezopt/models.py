from pydantic import BaseModel, StrictBool, StrictFloat, StrictInt, StrictStr


ChoiceType = StrictBool | StrictFloat | StrictInt | StrictStr | None


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
