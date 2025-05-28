from dataclasses import dataclass


@dataclass
class ScriptInputTagData:
    timestamp: int
    value: float
    status_code: int
    tagname: str = None

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptInputTagData":
        return cls(**data)

    def update(self, timestamp: int, value: float, status_code: int) -> None:
        self.timestamp = timestamp
        self.value = value
        self.status_code = status_code
