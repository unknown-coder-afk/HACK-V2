from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PrivacyAction(str, Enum):
    NONE = "none"
    MASK = "mask"
    HASH = "hash"
    NOISE = "noise"

class PrivacyRule(BaseModel):
    column: str
    action: PrivacyAction

class GenerationConfig(BaseModel):
    row_count: int = Field(default=100, ge=1, le=100000)
    seed: int = 42
    null_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    outlier_rate: float = Field(default=0.02, ge=0.0, le=0.2)
    privacy_rules: List[PrivacyRule] = []
    locale: str = "en_US"
    include_ai: bool = True

class GenerationResponse(BaseModel):
    preview: List[Dict[str, Any]]
    validation: Dict[str, Any]
    metadata: Dict[str, Any]
    columns: Optional[List[str]] = None
    total_rows: Optional[int] = None

class TextPoolRequest(BaseModel):
    column_type: str
    context: str = "e-commerce"
    count: int = 100
    locale: str = "en_US"

class EdgeCasesRequest(BaseModel):
    schema_info: Optional[Dict[str, Any]] = None