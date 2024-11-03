from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Optional, List
from datetime import datetime
from dataclasses import is_dataclass, fields
from typing import Any, Dict, Protocol, TypeVar, Type
from typing import ClassVar


T = TypeVar('T')


class Validatable(ABC):
    """Interface for models that can validate themselves"""
    @abstractmethod
    def validate(self) -> None:
        pass


class ValidationResultInterface(ABC):
    """Interface for validation results"""
    @property
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if validation passed"""
        pass

    @property
    @abstractmethod
    def warnings(self) -> List[str]:
        """Get validation warnings"""
        pass

    @property
    @abstractmethod
    def error_rate(self) -> float:
        """Get error rate from validation"""
        pass

    @abstractmethod
    def validate_transformation(self, result: 'TransformationResultBase') -> None:
        """Validate transformation results"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        pass


class TransformationOperation(ABC, Generic[T]):
    """Base interface for all transformation operations"""
    @abstractmethod
    def execute(self) -> T:
        pass

    @abstractmethod
    def validate(self) -> None:
        pass


class TransformationResultBase(ABC):
    """Base interface for transformation results"""
    @property
    @abstractmethod
    def original(self) -> str:
        pass

    @property
    @abstractmethod
    def transformed(self) -> str:
        pass

    @property
    @abstractmethod
    def metrics(self) -> Any:
        pass

    @property
    @abstractmethod
    def validation(self) -> Any:
        pass

    @property
    @abstractmethod
    def context(self) -> Any:
        pass

    @property
    @abstractmethod
    def sections(self) -> Optional[List[Any]]:
        pass


class DataclassProtocol(Protocol):
    """Protocol for dataclass instances"""
    __dataclass_fields__: ClassVar[Dict]
    def to_dict(self) -> Dict[str, Any]: ...


def _serialize_datetime(dt: datetime) -> str:
    """Convert datetime to ISO format string"""
    return dt.isoformat()


def _convert(obj: Any) -> Any:
    """Convert objects to serializable format"""
    if isinstance(obj, datetime):
        return _serialize_datetime(obj)
    elif is_dataclass(obj):
        if isinstance(obj, Serializable):
            return obj.to_dict()
        return {f.name: _convert(getattr(obj, f.name)) for f in fields(obj)}
    elif isinstance(obj, list):
        return [_convert(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _convert(value) for key, value in obj.items()}
    return obj


class Serializable:
    """Mixin class to add serialization capabilities to dataclasses"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass instance to dictionary"""
        if not is_dataclass(self):
            raise TypeError("Serializable can only be used with dataclasses")

        result = {}
        for field in fields(self):
            value = getattr(self, field.name)
            result[field.name] = _convert(value)
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create dataclass instance from dictionary"""
        if not is_dataclass(cls):
            raise TypeError("from_dict can only be used with dataclasses")

        field_types = {field.name: field.type for field in fields(cls)}
        processed_data = {}

        for key, value in data.items():
            if key not in field_types:
                continue

            field_type = field_types[key]

            # Handle nested dataclasses
            if is_dataclass(field_type) and isinstance(value, dict):
                processed_data[key] = field_type.from_dict(value)
            # Handle lists of dataclasses
            elif (getattr(field_type, "__origin__", None) is list and
                  len(getattr(field_type, "__args__", [])) == 1 and
                  is_dataclass(field_type.__args__[0]) and
                  isinstance(value, list)):
                item_type = field_type.__args__[0]
                processed_data[key] = [
                    item_type.from_dict(item) if isinstance(
                        item, dict) else item
                    for item in value
                ]
            else:
                processed_data[key] = value

        return cls(**processed_data)
