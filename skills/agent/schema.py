"""
JSON Schema Generator for LLM Tools
====================================
Converts Pydantic models and function signatures into OpenAI-compatible
function schemas.
"""

from __future__ import annotations

import enum
import inspect
from decimal import Decimal
from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel, create_model


class SkillSchemaGenerator:
    """Generates JSON Schema from Python callables and Pydantic types."""

    @classmethod
    def from_callable(cls, func: Callable, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate OpenAI function schema from a callable.
        """
        sig = inspect.signature(func)
        hints = get_type_hints(func)
        func_name = name or func.__name__
        description = inspect.getdoc(func) or f"Execute {func_name}"

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = hints.get(param_name, str)
            json_type = cls._python_type_to_json(param_type)
            properties[param_name] = json_type
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": func_name,
                "description": description.split("\n")[0].strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    @classmethod
    def from_pydantic_model(cls, model: Type[BaseModel], name: Optional[str] = None) -> Dict[str, Any]:
        """Generate schema from a Pydantic model class."""
        schema = model.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": name or model.__name__,
                "description": model.__doc__ or "",
                "parameters": schema,
            },
        }

    @classmethod
    def _python_type_to_json(cls, py_type: Any) -> Dict[str, Any]:
        """
        Map Python types to JSON Schema types.

        Handles:
          * primitives (int/float/bool/str/None)
          * containers (list, dict, with element types when known)
          * ``Optional[T]`` and ``Union[A, B, ...]``
          * ``Literal[a, b, c]`` (rendered as ``enum``)
          * ``Enum`` subclasses (rendered as ``enum`` of values)
          * ``Decimal`` (rendered as ``number``)
          * Pydantic ``BaseModel`` subclasses (inlined ``$ref``-style schema)
        """
        if py_type is None or py_type is type(None):
            return {"type": "null"}
        if py_type is int:
            return {"type": "integer"}
        if py_type is float:
            return {"type": "number"}
        if py_type is bool:
            return {"type": "boolean"}
        if py_type is str:
            return {"type": "string"}
        if py_type is Decimal:
            return {"type": "number"}
        if py_type is Any:
            return {}

        origin = get_origin(py_type)
        args = get_args(py_type)

        if origin is Literal:
            values = list(args)
            json_type = cls._infer_enum_type(values)
            schema: Dict[str, Any] = {"enum": values}
            if json_type is not None:
                schema["type"] = json_type
            return schema

        if origin is Union:
            # Optional[T] = Union[T, None]
            non_none = [a for a in args if a is not type(None)]
            has_none = len(non_none) != len(args)
            if len(non_none) == 1:
                inner = cls._python_type_to_json(non_none[0])
                if has_none:
                    inner["nullable"] = True
                return inner
            return {"anyOf": [cls._python_type_to_json(a) for a in non_none] +
                             ([{"type": "null"}] if has_none else [])}

        if origin is list or py_type is list:
            item_type = args[0] if args else str
            return {"type": "array", "items": cls._python_type_to_json(item_type)}
        if origin is dict or py_type is dict:
            return {"type": "object"}
        if origin is tuple or py_type is tuple:
            if args:
                return {"type": "array", "items": [cls._python_type_to_json(a) for a in args]}
            return {"type": "array"}

        if isinstance(py_type, type):
            if issubclass(py_type, enum.Enum):
                values = [m.value for m in py_type]
                json_type = cls._infer_enum_type(values)
                schema = {"enum": values}
                if json_type is not None:
                    schema["type"] = json_type
                return schema
            if issubclass(py_type, BaseModel):
                return py_type.model_json_schema()

        return {"type": "string"}

    @staticmethod
    def _infer_enum_type(values: List[Any]) -> Optional[str]:
        """Infer a uniform JSON Schema 'type' for an enum/Literal value list."""
        if all(isinstance(v, bool) for v in values):
            return "boolean"
        if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
            return "integer"
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            return "number"
        if all(isinstance(v, str) for v in values):
            return "string"
        return None
