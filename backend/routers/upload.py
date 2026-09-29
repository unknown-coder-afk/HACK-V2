import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ai.client import ai_client

router = APIRouter(prefix="/api/upload", tags=["Upload"])


@router.post("/schema")
async def upload_schema(file: UploadFile = File(...)):
    """Accept a JSON schema file and return it parsed."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json schema files are supported")

    content = await file.read()
    try:
        schema = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")

    return {"filename": file.filename, "schema": schema}


@router.post("/infer")
async def infer_schema_from_csv(file: UploadFile = File(...)):
    """Infer a column schema from an uploaded CSV sample."""
    import io
    import csv

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace")))
    headers = reader.fieldnames or []
    rows = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        rows.append(dict(row))

    # Simple type inference
    inferred = []
    for col in headers:
        sample_vals = [r[col] for r in rows if r.get(col)]
        col_type = "string"
        try:
            [int(v) for v in sample_vals]
            col_type = "integer"
        except (ValueError, TypeError):
            try:
                [float(v) for v in sample_vals]
                col_type = "float"
            except (ValueError, TypeError):
                pass
        inferred.append({"name": col, "type": col_type})

    return {"columns": inferred, "sample_rows": rows}
