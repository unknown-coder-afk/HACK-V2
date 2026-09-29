from fastapi import APIRouter

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/infer")
async def infer_schema():
    return {"message": "Schema inferred successfully"}
