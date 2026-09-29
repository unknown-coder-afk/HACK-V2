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


class ColumnSchema(BaseModel):
    name: str
    type: str = "string"  # integer, float, categorical, boolean, datetime, string, email, uuid
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None  # "table.column"
    categories: Optional[List[Any]] = None
    probabilities: Optional[List[float]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    start: Optional[str] = None
    end: Optional[str] = None


class TableConfig(BaseModel):
    name: str
    schema_cols: List[ColumnSchema] = Field(default_factory=list, alias="schema")
    row_count: int = Field(default=100, ge=1, le=50000)

    class Config:
        populate_by_name = True


class GenerationConfig(BaseModel):
    row_count: int = Field(default=100, ge=1, le=100000)
    seed: int = 42
    null_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    outlier_rate: float = Field(default=0.02, ge=0.0, le=0.2)
    privacy_rules: List[PrivacyRule] = []
    locale: str = "en_US"
    include_ai: bool = False


class TabularRequest(BaseModel):
    table_name: str = "dataset"
    columns: List[ColumnSchema]
    config: GenerationConfig = GenerationConfig()


class RelationalRequest(BaseModel):
    tables: List[TableConfig]
    config: GenerationConfig = GenerationConfig()


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


class ExportRequest(BaseModel):
    data: List[Dict[str, Any]]
    format: str = "csv"  # csv, json, parquet
    filename: str = "synthetic_data"


class DocumentConfig(BaseModel):
    doc_type: str = "invoice"   # invoice, bank_statement, receipt
    count: int = Field(default=5, ge=1, le=100)
    seed: int = 42