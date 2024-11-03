from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class DescriptionMixin:
    """Base mixin for all models providing description and serialization"""
    _description: str = field(default="", init=False)

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation"""
        result = {}
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            if isinstance(v, dict):
                result[k] = v.copy()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if hasattr(item, 'to_dict')
                             else item for item in v]
            elif hasattr(v, 'to_dict'):
                result[k] = v.to_dict()
            else:
                result[k] = v
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DescriptionMixin':
        """Create model instance from dictionary"""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })
