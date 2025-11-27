from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_processor import FileProcessor

router = APIRouter()


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and extract text content
    """
    # Check file type
    content_type = None

    if file.filename.endswith('.pdf'):
        content_type = "pdf"
    elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        content_type = "image"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or image files."
        )

    try:
        # Save file
        file_path = await FileProcessor.save_upload_file(file)

        # Process and extract text
        extracted_text = await FileProcessor.process_content("", content_type, file_path)

        return {
            "filename": file.filename,
            "content_type": content_type,
            "extracted_text": extracted_text[:500],  # Preview
            "text_length": len(extracted_text)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url")
async def process_url(url: str):
    """
    Extract text from a URL
    """
    try:
        extracted_text = await FileProcessor.process_url(url)

        return {
            "url": url,
            "extracted_text": extracted_text[:500],  # Preview
            "text_length": len(extracted_text)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
