from jinja2 import Environment, FileSystemLoader
from config.paths import TEMPLATES_DIR
from config.templates import AVAILABLE_TEMPLATES
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML.
    Converts **bold** to <strong>bold</strong> and \\n to <br>
    """
    if not text:
        return ""
    # Convert **bold** to <strong>bold</strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Convert \\n to <br>
    text = text.replace('\\n', '<br>')
    # Also handle actual newlines
    text = text.replace('\n', '<br>')
    return text


def render_html(resume_data, template_name: str) -> str:
    if template_name not in AVAILABLE_TEMPLATES:
        raise ValueError(f"Template '{template_name}' not supported")

    template_cfg = AVAILABLE_TEMPLATES[template_name]

    # Log structured data for debugging
    logger.info("=" * 60)
    logger.info("RESUME DATA BEING RENDERED:")
    logger.info(f"Name: {resume_data.name}")
    logger.info(f"Email: {resume_data.email}")
    logger.info(f"Phone: {resume_data.phone}")
    logger.info(f"LinkedIn: {resume_data.linkedin}")
    logger.info(f"GitHub: {resume_data.github}")
    logger.info(f"Summary: {resume_data.summary[:100] if resume_data.summary else 'EMPTY'}...")
    logger.info(f"Skills count: {len(resume_data.skills)}")
    logger.info(f"Skills: {resume_data.skills}")
    logger.info(f"Experience count: {len(resume_data.experience)}")
    for i, exp in enumerate(resume_data.experience):
        logger.info(f"  Experience {i+1}: {exp.role} at {exp.company}")
    logger.info(f"Projects count: {len(resume_data.projects)}")
    for i, proj in enumerate(resume_data.projects):
        logger.info(f"  Project {i+1}: {proj.title}")
    logger.info(f"Education: {resume_data.education[:100] if resume_data.education else 'EMPTY'}...")
    logger.info("=" * 60)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True
    )
    
    # Register custom filter for markdown to HTML conversion
    env.filters['md2html'] = markdown_to_html

    template = env.get_template(template_cfg["html"])

    # IMPORTANT: keep data namespaced
    return template.render(
        name=resume_data.name,
        email=resume_data.email,
        phone=resume_data.phone,
        linkedin=resume_data.linkedin,
        github=resume_data.github,
        summary=resume_data.summary,
        skills=resume_data.skills,
        experience=resume_data.experience,
        projects=resume_data.projects,
        education=resume_data.education
    )
