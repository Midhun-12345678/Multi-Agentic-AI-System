import io
import pdfplumber
from fastapi import UploadFile
from typing import Tuple


def read_resume(upload: UploadFile) -> Tuple[str, int]:
    """
    Safely extracts text from uploaded PDF resume.
    Works with FastAPI UploadFile.
    
    Returns:
        Tuple[str, int]: (resume_text, page_count)
    """

    if not upload.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF resumes are supported")

    # Read bytes from UploadFile
    file_bytes = upload.file.read()

    text_chunks = []
    page_count = 0

    # Wrap bytes in BytesIO (pdfplumber-safe)
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks), page_count
