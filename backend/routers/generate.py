import time
from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    TabularRequest,
    RelationalRequest,
    DocumentConfig,
    GenerationResponse,
)
from backend.engine.tabular import generate_table, df_to_serializable
from backend.engine.relational import generate_relational
from backend.engine.documents import generate_documents
from backend.engine.validation import validate_dataframe

router = APIRouter(prefix="/api/generate", tags=["Generate"])


# ── Preset schemas ─────────────────────────────────────────────────────────────

_ECOMMERCE_PRESET = {
    "tables": [
        {
            "name": "customers",
            "row_count": 50,
            "schema": [
                {"name": "id",         "type": "integer", "is_primary_key": True, "min": 1000, "max": 9999},
                {"name": "full_name",  "type": "name"},
                {"name": "email",      "type": "email"},
                {"name": "phone",      "type": "phone"},
                {"name": "city",       "type": "categorical", "categories": ["New York", "LA", "Chicago", "Houston", "Phoenix"]},
                {"name": "status",     "type": "categorical", "categories": ["active","inactive","pending"], "probabilities": [0.7, 0.2, 0.1]},
                {"name": "created_at", "type": "datetime", "start": "2023-01-01", "end": "2025-12-31"},
            ],
        },
        {
            "name": "orders",
            "row_count": 150,
            "schema": [
                {"name": "id",          "type": "integer", "is_primary_key": True, "min": 10000, "max": 99999},
                {"name": "customer_id", "type": "integer", "is_foreign_key": True, "references": "customers.id"},
                {"name": "order_date",  "type": "datetime", "start": "2024-01-01", "end": "2025-12-31"},
                {"name": "status",      "type": "categorical", "categories": ["pending","processing","shipped","delivered","cancelled"]},
                {"name": "total_amount","type": "float", "min": 10.0, "max": 2000.0},
                {"name": "payment_method", "type": "categorical", "categories": ["credit_card","paypal","bank_transfer"]},
            ],
        },
    ]
}


@router.post("/tabular", response_model=GenerationResponse)
async def generate_tabular(req: TabularRequest):
    t0 = time.perf_counter()
    try:
        df = generate_table(
            schema=req.columns,
            n_rows=req.config.row_count,
            seed=req.config.seed,
            config=req.config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    preview = df_to_serializable(df)
    elapsed = round(time.perf_counter() - t0, 3)
    validation = validate_dataframe(df, req.columns)

    return GenerationResponse(
        preview=preview,
        validation=validation,
        metadata={
            "table_name": req.table_name,
            "rows_generated": len(df),
            "columns": len(df.columns),
            "seed": req.config.seed,
            "null_rate": req.config.null_rate,
            "outlier_rate": req.config.outlier_rate,
            "generation_time_s": elapsed,
        },
        columns=list(df.columns),
        total_rows=len(df),
    )


@router.post("/relational")
async def generate_relational_endpoint(req: RelationalRequest):
    t0 = time.perf_counter()
    try:
        tables = generate_relational(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    elapsed = round(time.perf_counter() - t0, 3)
    return {
        "tables": tables,
        "metadata": {
            "table_count": len(tables),
            "row_counts": {name: len(rows) for name, rows in tables.items()},
            "generation_time_s": elapsed,
        },
    }


@router.post("/relational/preset/ecommerce")
async def generate_ecommerce_preset():
    """One-click e-commerce dataset (customers + orders)."""
    from backend.models.schemas import GenerationConfig, TableConfig, ColumnSchema

    tables = []
    for tbl in _ECOMMERCE_PRESET["tables"]:
        cols = [ColumnSchema(**c) for c in tbl["schema"]]
        tables.append(TableConfig(name=tbl["name"], schema=cols, row_count=tbl["row_count"]))

    req = RelationalRequest(tables=tables, config=GenerationConfig(seed=42, null_rate=0.03))
    return await generate_relational_endpoint(req)


@router.post("/document")
async def generate_document(cfg: DocumentConfig):
    t0 = time.perf_counter()
    try:
        docs = generate_documents(cfg.doc_type, cfg.count, cfg.seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    elapsed = round(time.perf_counter() - t0, 3)
    return {
        "documents": docs,
        "metadata": {
            "doc_type": cfg.doc_type,
            "count": len(docs),
            "generation_time_s": elapsed,
        },
    }
