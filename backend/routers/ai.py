from fastapi import APIRouter
from backend.models.schemas import TextPoolRequest
from backend.ai.text_pools import generate_text_pool

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/text-pool")
async def get_text_pool(req: TextPoolRequest):
    """Generate a pool of realistic text values using AI or fallback."""
    pool, source = generate_text_pool(
        column_type=req.column_type,
        context=req.context,
        count=req.count,
        locale=req.locale,
    )
    return {"pool": pool, "count": len(pool), "source": source}


@router.get("/column-types")
async def list_column_types():
    """List all supported column types."""
    return {
        "types": [
            {"value": "string",   "label": "String (Generic)",  "icon": "T"},
            {"value": "integer",  "label": "Integer",            "icon": "#"},
            {"value": "float",    "label": "Float / Decimal",    "icon": ".1"},
            {"value": "boolean",  "label": "Boolean",            "icon": "⊤"},
            {"value": "datetime", "label": "Date / DateTime",    "icon": "📅"},
            {"value": "uuid",     "label": "UUID",               "icon": "🔑"},
            {"value": "name",     "label": "Full Name",          "icon": "👤"},
            {"value": "email",    "label": "Email",              "icon": "✉"},
            {"value": "phone",    "label": "Phone Number",       "icon": "📞"},
            {"value": "address",  "label": "Address",            "icon": "📍"},
            {"value": "company",  "label": "Company Name",       "icon": "🏢"},
            {"value": "product",  "label": "Product Name",       "icon": "📦"},
            {"value": "status",   "label": "Status",             "icon": "🔴"},
            {"value": "categorical", "label": "Categorical",     "icon": "≡"},
        ]
    }
