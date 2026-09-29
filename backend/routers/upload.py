from fastapi import APIRouter

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("/")
async def upload_schema():
    return {"message": "Schema uploaded successfully"}
