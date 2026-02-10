"""Utilidades de serialización JSON para ChosicAlpha."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any


class DataclassEncoder(json.JSONEncoder):
    """Encoder JSON personalizado que maneja automáticamente dataclasses."""
    
    def default(self, obj: Any) -> Any:
        """Convierte dataclasses a dict automáticamente."""
        if is_dataclass(obj):
            return asdict(obj) # type: ignore
        return super().default(obj)

def dump_json(obj: Any, filepath: str, **kwargs) -> None:
    """Guarda un objeto (con dataclasses) a JSON.
    
    Args:
        obj: Objeto a guardar (puede contener dataclasses)
        filepath: Ruta del archivo de salida
        **kwargs: Argumentos adicionales para json.dump (indent, ensure_ascii, etc.)
    """
    default_kwargs = {
        'ensure_ascii': False,
        'indent': 2,
        'cls': DataclassEncoder
    }
    default_kwargs.update(kwargs)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(obj, f, **default_kwargs)

def dumps_json(obj: Any, **kwargs) -> str:
    """Retorna un objeto (con dataclasses) como string JSON.
    
    Args:
        obj: Objeto a serializar
        **kwargs: Argumentos adicionales para json.dumps
    """
    default_kwargs = {
        'ensure_ascii': False,
        'indent': 2,
        'cls': DataclassEncoder
    }
    default_kwargs.update(kwargs)
    
    return json.dumps(obj, **default_kwargs)
