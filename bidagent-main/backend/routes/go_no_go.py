from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from services.pdf_parser import run_go_no_go_pipeline
from services.auth import get_current_user

go_no_go_router = APIRouter()


@go_no_go_router.post("/go-no-go")
async def go_no_go(file: UploadFile = File(...), _user=Depends(get_current_user)):
    """Process a proposal PDF and return go/no-go decision with reasoning."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large for prototype")

    try:
        result = run_go_no_go_pipeline(pdf_bytes)
    except ValueError as e:
        if str(e) == "SCANNED_PDF":
            raise HTTPException(
                status_code=400,
                detail="Scanned PDF detected. Please provide a PDF with selectable text.",
            )
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal error processing PDF: {str(e)}"
        )

    return result
