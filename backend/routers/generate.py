from fastapi import APIRouter
from backend.models.schemas import GenerationConfig
from backend.engine.tabular import generate_table
from backend.engine.relational import generate_relational

router = APIRouter(prefix="/api/generate", tags=["Generate"])

@router.post("/tabular")
async def generate_tabular(config: GenerationConfig):
    schema = [
        {"name": "id", "is_primary_key": True},
        {"name": "name"},
        {"name": "email"},
        {"name": "signup"},
        {"name": "balance"}
    ]
    distributions = {
        "id": {"type": "integer", "min": 10000, "max": 99999},
        "name": {"type": "categorical", "categories": ["Maria Chen", "Ahmed Raza", "Sofia Ivanova"]},
        "email": {"type": "categorical", "categories": ["m.chen@example.com", "a.raza@example.com", "s.ivanova@example.com"]},
        "signup": {"type": "datetime", "start": "2025-01-01", "end": "2025-04-01"},
        "balance": {"type": "float", "min": 100.0, "max": 1000.0}
    }
    df = generate_table(schema, distributions, config.row_count, config.seed, config)
    # df.replace({pd.NaT: None}) could be needed, but we can just use to_dict
    import numpy as np
    import pandas as pd
    df = df.replace({np.nan: None, pd.NaT: None})
    return {"preview": df.to_dict(orient="records")}

@router.post("/relational")
async def generate_rel():
    return {"preview": "Relational data generation coming soon"}

@router.post("/document")
async def generate_doc():
    return {"preview": "Document data generation coming soon"}
