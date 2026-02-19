"""
Template-specific context for agent optimization.
Provides formatting rules, structure, and examples for each template.
"""

TEMPLATE_CONTEXTS = {
    "harvard": {
        "name": "Harvard Business School Style",
        "description": "Center-aligned header with maroon accent border, traditional serif font, conservative professional tone",
        "structure": {
            "header": "Center-aligned name and contact (email • phone • linkedin • github)",
            "section_order": ["Professional Summary (at top for ATS)", "Education", "Experience", "Leadership & Activities (Projects)", "Skills & Interests"],
            "experience_format": "Company name as title, role as subtitle",
            "style": "Concise bullets (1 line each), formal language, achievement-focused"
        },
        "formatting_rules": [
            "Use ### for section headers (Education, Experience, Leadership & Activities, Skills & Interests)",
            "Bold **company names** and **project titles** using markdown",
            "Each bullet point = ONE LINE only (50-80 characters ideal)",
            "Use strong action verbs and quantify results",
            "Professional, formal tone - no casual language",
            "PRESERVE same number of bullets as original resume",
            "Projects labeled as 'Leadership & Activities'"
        ],
        "example_output": """### Education
B.S. Computer Science, MIT, Cambridge, MA | May 2020 | GPA: 3.8

### Experience

**Tech Corporation** | Senior Software Engineer | Jun 2020 – Present | Boston, MA
- Built microservices platform serving 2M+ users (AWS, Docker)
- Reduced API latency 45% via Redis caching
- Led 5-engineer team in monolith-to-microservices migration

**Startup Inc** | Software Engineer | Jan 2019 – May 2020 | San Francisco, CA
- Developed SaaS features using React and Node.js
- Increased test coverage from 40% to 90%

### Leadership & Activities

**Open Source Contributor** | Python, TensorFlow, React
- Contributed to 10+ projects including React, TensorFlow
- Maintained Python library with 5K+ downloads

### Skills & Interests
Languages: Python, JavaScript, TypeScript, SQL
Cloud: AWS, Docker, Kubernetes, Terraform
Frameworks: React, Node.js, Django, FastAPI""",
        "json_structure_example": {
            "_CRITICAL": "OUTPUT MUST HAVE SAME NUMBER OF ITEMS AS ORIGINAL RESUME. If original has 4 bullets per job, output 4 bullets. If original has 6 projects, output 6 projects. This example shows FORMAT only.",
            "name": "JOHN SMITH",
            "email": "john.smith@email.com",
            "phone": "+1-555-123-4567",
            "linkedin": "linkedin.com/in/johnsmith",
            "github": "github.com/johnsmith",
            "education": "B.S. Computer Science, MIT, Cambridge, MA | May 2020 | GPA: 3.8",
            "experience": [
                {
                    "company": "Tech Corporation",
                    "role": "Senior Software Engineer",
                    "start_date": "Jun 2020",
                    "end_date": "Present",
                    "location": "Boston, MA",
                    "description": "- Built microservices platform serving 2M+ users (AWS, Docker)\\n- Reduced API latency 45% via Redis caching\\n- Led 5-engineer team in architecture migration"
                },
                {
                    "company": "Startup Inc",
                    "role": "Software Engineer",
                    "start_date": "Jan 2019",
                    "end_date": "May 2020",
                    "location": "San Francisco, CA",
                    "description": "- Developed SaaS features using React and Node.js\\n- Increased test coverage from 40% to 90%"
                }
            ],
            "projects": [
                {
                    "title": "Open Source Contributor",
                    "tech_stack": "Python, TensorFlow, React",
                    "details": "- Contributed to 10+ projects (React, TensorFlow)\\n- Maintained Python lib with 5K+ downloads"
                }
            ],
            "skills": [
                "Languages: Python, JavaScript, TypeScript, SQL",
                "Cloud: AWS, Docker, Kubernetes, Terraform",
                "Frameworks: React, Node.js, Django, FastAPI",
                "Databases: PostgreSQL, MongoDB, Redis"
            ],
            "certifications": [
                "AWS Solutions Architect – Associate",
                "Google Cloud Professional Data Engineer"
            ],
            "awards": [],
            "languages": [],
            "summary": ""
        },
        "style_notes": "Conservative and achievement-focused. Keep each bullet to ONE LINE. Preserve ALL bullets from original - just make them concise."
    },
    
    "professional": {
        "name": "Modern Professional",
        "description": "Left-aligned layout, sans-serif font, bold section headers with underlines, technical depth",
        "structure": {
            "header": "Left-aligned name (large), contact info below",
            "section_order": ["Professional Summary", "Technical Skills", "Professional Experience", "Projects", "Education"],
            "experience_format": "Job Title | Employment Type as main heading",
            "style": "Concise bullets (1 line each), technical specifics, modern language"
        },
        "formatting_rules": [
            "Use ### for section headers",
            "Bold **job titles with employment type** (e.g., **Senior Engineer | Full-time**)",
            "Each bullet point = ONE LINE only (include key tech)",
            "PRESERVE same number of bullets as original resume",
            "Professional but modern tone",
            "Summary section at top (2-3 sentences max)",
            "Categorize technical skills (Languages, Cloud, Frameworks, etc.)"
        ],
        "example_output": """### Professional Summary
Senior Software Engineer with 5+ years in cloud-native apps. Expert in microservices, DevOps, and full-stack development.

### Technical Skills
Languages: Python, JavaScript, TypeScript, Go, SQL
Cloud: AWS, Docker, Kubernetes, Terraform, Jenkins
Backend: Node.js, FastAPI, Django, PostgreSQL, Redis
Frontend: React, Next.js, Tailwind CSS

### Professional Experience

**Lead Software Engineer | Full-time** | TechCorp Inc | Mar 2021 – Present | San Francisco, CA
- Deployed microservices for 2M+ DAUs using K8s, Docker, AWS ECS
- Built CI/CD pipeline (GitHub Actions), reduced deploy time 4hrs→15min
- Migrated monolith to event-driven microservices (Kafka), 60% scalability gain
- Mentored 6 engineers on cloud-native practices

**Software Engineer | Full-time** | StartupXYZ | Jun 2019 – Feb 2021 | Remote
- Built web app (React, Node.js, PostgreSQL) handling 500K req/day
- Designed RESTful APIs with OpenAPI docs, integrated Stripe/Twilio
- Created real-time notifications (WebSockets, Redis) for 100K connections

### Projects

**Distributed Task Queue** | Python, Redis, Celery
- Built task system processing 1M+ daily tasks
- Created Grafana/Prometheus monitoring dashboard

### Education
B.S. Computer Science, Stanford University | 2019""",
        "json_structure_example": {
            "_CRITICAL": "If original has 4 bullets per job, output MUST have 4 bullets per job. Same number of items!",
            "name": "JANE DOE",
            "email": "jane.doe@email.com",
            "phone": "+1-555-987-6543",
            "linkedin": "linkedin.com/in/janedoe",
            "github": "github.com/janedoe",
            "summary": "5+ years cloud-native apps. Expert in microservices, DevOps, full-stack.",
            "skills": [
                "Languages: Python, JavaScript, TypeScript, Go, SQL",
                "Cloud: AWS, Docker, Kubernetes, Terraform",
                "Backend: Node.js, FastAPI, Django, PostgreSQL",
                "Frontend: React, Next.js, Tailwind CSS"
            ],
            "experience": [
                {
                    "company": "TechCorp Inc",
                    "role": "Lead Software Engineer | Full-time",
                    "start_date": "Mar 2021",
                    "end_date": "Present",
                    "location": "San Francisco, CA",
                    "description": "- Deployed microservices for 2M+ DAUs (K8s, Docker, AWS ECS)\\n- Built CI/CD (GitHub Actions), 4hrs→15min deploy\\n- Migrated to event-driven microservices (Kafka), 60% scale gain\\n- Mentored 6 engineers on cloud-native practices"
                }
            ],
            "projects": [
                {
                    "title": "Distributed Task Queue",
                    "tech_stack": "Python, Redis, Celery",
                    "details": "- Task system: 1M+ daily tasks\\n- Grafana/Prometheus monitoring"
                }
            ],
            "education": "B.S. Computer Science, Stanford University | 2019",
            "certifications": [],
            "awards": [],
            "languages": []
        },
        "style_notes": "Concise with tech specifics. Each bullet ONE LINE. PRESERVE all bullets from original - just make them shorter."
    },
    
    "classic": {
        "name": "Classic Professional",
        "description": "Traditional format with serif font, minimal styling, understated design, emphasis on career progression",
        "structure": {
            "header": "Name at top, contact below",
            "section_order": ["Professional Summary", "Professional Experience", "Technical Skills", "Education"],
            "experience_format": "Job title as main heading, company below",
            "style": "Concise bullets (1 line each), traditional business language"
        },
        "formatting_rules": [
            "Use ### for section headers",
            "Bold **job titles** prominently",
            "Each bullet = ONE LINE only",
            "PRESERVE same number of bullets as original resume",
            "Traditional professional language",
            "Summary at top (2-3 sentences max)",
            "Skills section brief and categorized"
        ],
        "example_output": """### Professional Summary
6+ years enterprise app development. Expert in full-stack, team leadership, mission-critical systems.

### Professional Experience

**Senior Software Engineer**
Global Financial Services Corp, New York, NY | 2021 – Present
- Lead team of 8 engineers for banking platform (500K+ customers)
- Implemented SOC 2 Type II security compliance
- Delivered 15+ features on schedule, zero production incidents
- Collaborated with product/design on technical requirements

**Software Engineer**
HealthTech Solutions, Boston, MA | 2018 – 2021
- Developed patient management system (200+ healthcare facilities)
- Modernized legacy systems to cloud infrastructure
- On-call rotation, resolved critical production issues
- Documented specs, conducted code reviews

### Technical Skills
Languages: Java, Python, JavaScript, SQL
Frameworks: Spring Boot, React, Node.js
Databases: PostgreSQL, MySQL, MongoDB
Tools: Git, Jenkins, Docker, AWS

### Education
B.S. Computer Science, Boston University | 2017""",
        "json_structure_example": {
            "_CRITICAL": "If original has 4 bullets per job, output MUST have 4 bullets per job. Same number of items!",
            "name": "ROBERT JOHNSON",
            "email": "robert.j@email.com",
            "phone": "+1-555-456-7890",
            "linkedin": "linkedin.com/in/robertjohnson",
            "github": "",
            "summary": "6+ years enterprise apps. Expert in full-stack, team leadership, mission-critical systems.",
            "experience": [
                {
                    "company": "Global Financial Services Corp",
                    "role": "Senior Software Engineer",
                    "start_date": "2021",
                    "end_date": "Present",
                    "location": "New York, NY",
                    "description": "- Lead 8-engineer team for banking platform (500K+ customers)\\n- Implemented SOC 2 Type II security compliance\\n- Delivered 15+ features on schedule, zero incidents\\n- Collaborated with product/design teams"
                }
            ],
            "skills": [
                "Languages: Java, Python, JavaScript, SQL",
                "Frameworks: Spring Boot, React, Node.js",
                "Databases: PostgreSQL, MySQL, MongoDB"
            ],
            "projects": [],
            "education": "B.S. Computer Science, Boston University | 2017",
            "certifications": [],
            "awards": [],
            "languages": []
        },
        "style_notes": "Traditional, conservative. Each bullet ONE LINE. PRESERVE all bullets from original - just make them concise."
    }
}


def get_template_context(template_name: str) -> dict:
    """
    Get formatting context for specified template.
    Returns Harvard context as default if template not found.
    """
    return TEMPLATE_CONTEXTS.get(template_name.lower(), TEMPLATE_CONTEXTS["harvard"])


def get_template_prompt_context(template_name: str) -> str:
    """
    Generate formatted prompt context string for agents.
    Includes structure, rules, examples, and style guidance.
    """
    ctx = get_template_context(template_name)
    
    # Format structure details
    structure_text = "\n".join([f"  • {key}: {value}" for key, value in ctx["structure"].items()])
    
    # Format rules as numbered list
    rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(ctx["formatting_rules"])])
    
    prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ TARGET TEMPLATE: {ctx['name']}
║ {ctx['description']}
╚══════════════════════════════════════════════════════════════════════════════╝

📋 TEMPLATE STRUCTURE:
{structure_text}

✅ FORMATTING REQUIREMENTS:
{rules_text}

📐 SECTION ORDER: {' → '.join(ctx['structure']['section_order'])}

🎨 STYLE GUIDANCE: {ctx['style_notes']}

📝 EXAMPLE OUTPUT FORMAT:
{ctx['example_output']}

⚠️  CRITICAL: Follow the EXACT format shown in the example above. Match the structure, 
    section order, and formatting precisely to ensure proper template rendering.
"""
    return prompt

def get_json_structure_prompt(template_name: str) -> str:
    """
    Generate prompt for structured JSON output matching template requirements.
    This ensures direct data structure that maps to template without parsing.
    """
    ctx = get_template_context(template_name)
    json_example = ctx.get("json_structure_example", {})
    
    import json
    json_str = json.dumps(json_example, indent=2)
    
    prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ OUTPUT FORMAT: STRUCTURED JSON (Required)
║ Template: {ctx['name']}
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 CRITICAL: Output ONLY valid JSON in this EXACT structure:

{json_str}

📋 FIELD REQUIREMENTS:
  • name: Full name in UPPERCASE or Title Case
  • email, phone, linkedin, github: Contact information (strings)
  • summary: Professional summary paragraph (string, can be empty "")
  • education: Education details with newlines (\\n) between lines (string)
  • experience: Array of objects with:
    - company: Company name (string)
    - role: Job title (string)
    - start_date: Start date like "Jan 2023" or "2023" (string)
    - end_date: End date like "Dec 2024" or "Present" (string)
    - location: City, State (string, can be empty)
    - description: Bullet points with \\n between them
  • projects: Array of objects with:
    - title: Project name (string)
    - tech_stack: Technologies used (string, can be empty)
    - details: Description with \\n for line breaks
  • skills: Array of strings (categorized skills like "Languages: Python, JS")
  • certifications: Array of certification strings (empty array if none)
  • awards: Array of award strings (empty array if none)
  • languages: Array of language strings (empty array if none)

⚠️  CRITICAL RULES:
  1. Output ONLY the JSON object - no additional text, commentary, or markdown
  2. Use \\n (not actual line breaks) for multi-line fields
  3. Ensure all strings are properly escaped
  4. All arrays must be valid JSON arrays with proper syntax
  5. Do NOT wrap JSON in markdown code blocks
  6. Do NOT add any text before or after the JSON
  7. ALWAYS include start_date and end_date for each experience
  8. ALWAYS include certifications array (even if empty [])

✅ VALID OUTPUT:
{{
  "name": "JOHN SMITH",
  "email": "john@email.com",
  ...
}}

❌ INVALID:
```json
{{
  "name": "JOHN SMITH"
}}
```

❌ INVALID:
Here is the optimized resume:
{{
  "name": "JOHN SMITH"
}}
"""
    return prompt