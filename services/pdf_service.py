import base64
from weasyprint import HTML

def html_to_pdf_base64(html_content: str) -> str:
    """
    Converts HTML → PDF → Base64
    """

    # DEBUG (optional but useful)
    if not html_content.strip():
        raise ValueError("HTML content is empty")

    pdf_bytes = HTML(string=html_content).write_pdf()

    return base64.b64encode(pdf_bytes).decode("utf-8")
