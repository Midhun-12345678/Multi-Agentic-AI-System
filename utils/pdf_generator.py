from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
from reportlab.platypus import Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

def create_resume_pdf(content: str, output_path="optimized_resume.pdf"):

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36
    )

    story = []

    for line in content.split("\n"):
        story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 6))

    doc.build(story)

    return output_path
