import io
import pdfplumber
from fastapi import UploadFile

def read_resume(upload: UploadFile) -> str:
    """
    Safely extracts text from uploaded PDF resume.
    Works with FastAPI UploadFile.
    """

    if not upload.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF resumes are supported")

    # ✅ Read bytes from UploadFile
    file_bytes = upload.file.read()

    text_chunks = []

    # ✅ Wrap bytes in BytesIO (pdfplumber-safe)
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks)
