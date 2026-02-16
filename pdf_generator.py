import pdfkit

def generate_pdf(html_path):
    pdfkit.from_file(html_path, "final_resume.pdf")
