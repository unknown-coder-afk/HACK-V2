import io
import json
import csv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.schemas import ExportRequest

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.post("/csv")
async def export_csv(req: ExportRequest):
    if not req.data:
        raise HTTPException(status_code=400, detail="No data provided")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=req.data[0].keys())
    writer.writeheader()
    writer.writerows(req.data)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}.csv"'},
    )


@router.post("/json")
async def export_json(req: ExportRequest):
    if not req.data:
        raise HTTPException(status_code=400, detail="No data provided")

    content = json.dumps(req.data, indent=2, default=str)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{req.filename}.json"'},
    )
