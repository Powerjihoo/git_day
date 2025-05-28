from dataclasses import dataclass


@dataclass
class _TagDataFromKafka:
    timestamp: int
    value: float
    status_code: int
    tagname: str = None

    @classmethod
    def from_dict(cls, data: dict) -> "_TagDataFromKafka":
        return cls(**data)


@dataclass
class ScriptDataFromKafka:
    script_key: str
    data: list[_TagDataFromKafka]

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptDataFromKafka":
        return cls(
            script_key=data["script_key"],
            data=[_TagDataFromKafka.from_dict(tag_data) for tag_data in data["data"]],
        )
