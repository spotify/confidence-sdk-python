import dataclasses


@dataclasses.dataclass
class FlagName(object):
    flag: str

    @classmethod
    def parse(cls, resource_name: str) -> "FlagName":
        components = resource_name.split("/", 2)
        if components[0] != "flags":
            raise ValueError("name error")
        return cls(components[1])

    def __str__(self) -> str:
        return f"flags/{self.flag}"


@dataclasses.dataclass
class VariantName(object):
    flag: str
    variant: str

    @classmethod
    def parse(cls, resource_name: str) -> "VariantName":
        components = resource_name.split("/")
        if components[0] != "flags" or components[2] != "variants":
            raise ValueError("name error")
        return cls(components[1], components[3])
