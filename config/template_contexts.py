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
            "style": "Concise bullets (1-2 lines), formal language, achievement-focused"
        },
        "formatting_rules": [
            "Use ### for section headers (Education, Experience, Leadership & Activities, Skills & Interests)",
            "Bold **company names** and **project titles** using markdown",
            "Keep bullet points concise - max 2 lines per achievement",
            "Use strong action verbs and quantify results",
            "Professional, formal tone - no casual language",
            "Education section comes FIRST after header",
            "Projects labeled as 'Leadership & Activities'"
        ],
        "example_output": """### Education
Bachelor of Science in Computer Science
Massachusetts Institute of Technology, Cambridge, MA
Graduated: May 2020 | GPA: 3.8/4.0

### Experience

**Tech Corporation**
Senior Software Engineer
June 2020 – Present, Boston, MA
- Architected microservices platform serving 2M+ users with 99.9% uptime using AWS and Docker
- Reduced API latency by 45% through Redis caching and database query optimization
- Led team of 5 engineers in migration from monolithic to event-driven architecture

**Startup Inc**
Software Engineer
January 2019 – May 2020, San Francisco, CA
- Developed full-stack features for SaaS product using React and Node.js
- Improved test coverage from 40% to 90% using Jest and Cypress

### Leadership & Activities

**Open Source Contributor**
- Contributed to 10+ open source projects including React and TensorFlow
- Maintained Python library with 5K+ downloads and 200+ GitHub stars

### Skills & Interests
Technical: Python, JavaScript, AWS, Docker, Kubernetes, PostgreSQL, React, CI/CD
Interests: Machine learning, cloud architecture, technical mentorship""",
        "json_structure_example": {
            "_NOTE": "This example shows FORMATTING STYLE only. Your output must contain ALL entries from the original resume (not limited to the number of items shown here). If original has 5 projects, output 5 projects; if original has 3 jobs, output 3 jobs.",
            "name": "JOHN SMITH",
            "email": "john.smith@email.com",
            "phone": "+1-555-123-4567",
            "linkedin": "linkedin.com/in/johnsmith",
            "github": "github.com/johnsmith",
            "education": "Bachelor of Science in Computer Science\nMassachusetts Institute of Technology, Cambridge, MA\nGraduated: May 2020 | GPA: 3.8/4.0",
            "experience": [
                {
                    "company": "Tech Corporation",
                    "role": "Senior Software Engineer",
                    "description": "- Architected **microservices platform** serving **2M+ users** with **99.9% uptime** using **AWS** and **Docker**\n- Reduced API latency by **45%** through **Redis caching** and database query optimization\n- Led team of **5 engineers** in migration from monolithic to **event-driven architecture**"
                },
                {
                    "company": "Startup Inc",
                    "role": "Software Engineer",
                    "description": "- Developed full-stack features for **SaaS product** using **React** and **Node.js**\n- Improved test coverage from **40% to 90%** using **Jest** and **Cypress**"
                }
            ],
            "projects": [
                {
                    "title": "Open Source Contributor",
                    "details": "- Contributed to **10+ open source projects** including **React** and **TensorFlow**\n- Maintained **Python library** with **5K+ downloads** and **200+ GitHub stars**"
                }
            ],
            "skills": [
                "Programming Languages: **Python**, **JavaScript**, **TypeScript**, **SQL**",
                "Cloud & DevOps: **AWS**, **Docker**, **Kubernetes**, **Terraform**",
                "Frameworks: **React**, **Node.js**, **Django**, **FastAPI**",
                "Databases & Tools: **PostgreSQL**, **MongoDB**, **Git**, **CI/CD**"
            ],
            "summary": ""
        },
        "style_notes": "Conservative and achievement-focused. Emphasize education credentials, leadership, and measurable impact. Use formal business language."
    },
    
    "professional": {
        "name": "Modern Professional",
        "description": "Left-aligned layout, sans-serif font, bold section headers with underlines, technical depth",
        "structure": {
            "header": "Left-aligned name (large), contact info below",
            "section_order": ["Professional Summary", "Technical Skills", "Professional Experience", "Projects", "Education"],
            "experience_format": "Job Title | Employment Type as main heading",
            "style": "Detailed bullets (2-3 lines), technical specifics, modern language"
        },
        "formatting_rules": [
            "Use ### for section headers",
            "Bold **job titles with employment type** (e.g., **Senior Engineer | Full-time**)",
            "Include technical stack details in bullets",
            "Use 2-3 line bullets with specific technologies",
            "Professional but modern tone",
            "Summary section at top highlighting expertise",
            "Categorize technical skills (Languages, Cloud, Frameworks, etc.)"
        ],
        "example_output": """### Professional Summary
Senior Software Engineer with 5+ years building scalable cloud-native applications. Specialized in microservices architecture, DevOps automation, and full-stack development. Proven track record delivering high-impact features for products serving millions of users.

### Technical Skills
- Languages: Python, JavaScript, TypeScript, Go, SQL
- Cloud & DevOps: AWS (EC2, Lambda, RDS, S3), Docker, Kubernetes, Terraform, Jenkins
- Backend: Node.js, FastAPI, Django, PostgreSQL, MongoDB, Redis
- Frontend: React, Next.js, TypeScript, Tailwind CSS
- Tools: Git, CI/CD (GitHub Actions, CircleCI), Datadog, Sentry

### Professional Experience

**Lead Software Engineer | Full-time**
TechCorp Inc, San Francisco, CA
March 2021 – Present
- Architected and deployed microservices infrastructure serving 2M+ daily active users using Kubernetes, Docker, and AWS ECS with auto-scaling and load balancing
- Implemented comprehensive CI/CD pipeline with GitHub Actions, reducing deployment time from 4 hours to 15 minutes and enabling 20+ daily deployments
- Led migration from monolithic Django application to event-driven microservices using Kafka, resulting in 60% improvement in system scalability
- Mentored team of 6 engineers on cloud-native best practices, code reviews, and agile methodologies

**Software Engineer | Full-time**
StartupXYZ, Remote
June 2019 – February 2021
- Developed responsive web application using React, Node.js, and PostgreSQL handling 500K+ requests per day with sub-200ms response times
- Designed and implemented RESTful APIs with comprehensive OpenAPI documentation and integrated third-party services (Stripe, Twilio, SendGrid)
- Built real-time notification system using WebSockets and Redis pub/sub serving 100K+ concurrent connections

### Projects

**Distributed Task Queue System**
- Built scalable task processing system using Python, Redis, and Celery handling 1M+ tasks daily
- Implemented monitoring dashboard with real-time metrics using Grafana and Prometheus
- Open-sourced on GitHub with 500+ stars and active community contributions

### Education
Bachelor of Science in Computer Science
Stanford University, Palo Alto, CA
Graduated: 2019""",
        "json_structure_example": {
            "name": "JANE DOE",
            "email": "jane.doe@email.com",
            "phone": "+1-555-987-6543",
            "linkedin": "linkedin.com/in/janedoe",
            "github": "github.com/janedoe",
            "summary": "Senior Software Engineer with 5+ years building scalable cloud-native applications. Specialized in microservices architecture, DevOps automation, and full-stack development.",
            "skills": [
                "Languages: Python, JavaScript, TypeScript, Go, SQL",
                "Cloud & DevOps: AWS (EC2, Lambda, RDS, S3), Docker, Kubernetes, Terraform, Jenkins",
                "Backend: Node.js, FastAPI, Django, PostgreSQL, MongoDB, Redis",
                "Frontend: React, Next.js, TypeScript, Tailwind CSS"
            ],
            "experience": [
                {
                    "company": "TechCorp Inc, San Francisco, CA",
                    "role": "Lead Software Engineer | Full-time",
                    "description": "- Architected and deployed microservices infrastructure serving 2M+ daily active users using Kubernetes, Docker, and AWS ECS\n- Implemented comprehensive CI/CD pipeline with GitHub Actions, reducing deployment time from 4 hours to 15 minutes\n- Led migration from monolithic Django application to event-driven microservices using Kafka"
                }
            ],
            "projects": [
                {
                    "title": "Distributed Task Queue System",
                    "details": "- Built scalable task processing system using Python, Redis, and Celery handling 1M+ tasks daily\n- Implemented monitoring dashboard with real-time metrics using Grafana and Prometheus"
                }
            ],
            "education": "Bachelor of Science in Computer Science\nStanford University, Palo Alto, CA\nGraduated: 2019"
        },
        "style_notes": "Technical depth and specificity. Include exact technologies, frameworks, and quantified metrics. Modern professional language with detailed accomplishments."
    },
    
    "classic": {
        "name": "Classic Professional",
        "description": "Traditional format with serif font, minimal styling, understated design, emphasis on career progression",
        "structure": {
            "header": "Name at top, contact below",
            "section_order": ["Professional Summary", "Professional Experience", "Technical Skills", "Education"],
            "experience_format": "Job title as main heading, company below",
            "style": "Clean minimal formatting, traditional business language, focus on progression"
        },
        "formatting_rules": [
            "Use ### for section headers",
            "Bold **job titles** prominently",
            "Keep formatting minimal and clean",
            "Traditional professional language",
            "Emphasize career growth and stability",
            "Summary at top showcasing overall expertise",
            "Skills section brief and categorized"
        ],
        "example_output": """### Professional Summary
Experienced software engineer with 6+ years in enterprise application development. Proven expertise in full-stack development, team leadership, and delivering mission-critical systems. Strong background in financial services and healthcare technology sectors.

### Professional Experience

**Senior Software Engineer**
Global Financial Services Corp, New York, NY
2021 – Present
- Lead development team of 8 engineers for core banking platform serving 500K+ customers
- Implemented security enhancements achieving SOC 2 Type II compliance
- Delivered 15+ major features on schedule with zero production incidents
- Collaborate with product and design teams to define technical requirements

**Software Engineer**
HealthTech Solutions, Boston, MA
2018 – 2021
- Developed patient management system used by 200+ healthcare facilities
- Maintained legacy systems while modernizing to cloud infrastructure
- Participated in on-call rotation and resolved critical production issues
- Documented technical specifications and conducted code reviews

**Junior Developer**
Software Consultancy LLC, Boston, MA
2017 – 2018
- Contributed to client projects across various industries
- Gained experience in Java, Python, and web development
- Worked closely with senior developers to improve technical skills

### Technical Skills
Languages: Java, Python, JavaScript, SQL
Frameworks: Spring Boot, React, Node.js
Databases: PostgreSQL, MySQL, MongoDB
Tools: Git, Jenkins, Docker, AWS

### Education
Bachelor of Science in Computer Science
Boston University, Boston, MA
Graduated: 2017""",
        "json_structure_example": {
            "name": "ROBERT JOHNSON",
            "email": "robert.j@email.com",
            "phone": "+1-555-456-7890",
            "linkedin": "linkedin.com/in/robertjohnson",
            "github": "",
            "summary": "Experienced software engineer with 6+ years in enterprise application development. Proven expertise in full-stack development, team leadership, and delivering mission-critical systems.",
            "experience": [
                {
                    "company": "Global Financial Services Corp, New York, NY",
                    "role": "Senior Software Engineer",
                    "description": "- Lead development team of 8 engineers for core banking platform serving 500K+ customers\n- Implemented security enhancements achieving SOC 2 Type II compliance\n- Delivered 15+ major features on schedule with zero production incidents"
                }
            ],
            "skills": [
                "Languages: Java, Python, JavaScript, SQL",
                "Frameworks: Spring Boot, React, Node.js",
                "Databases: PostgreSQL, MySQL, MongoDB",
                "Tools: Git, Jenkins, Docker, AWS"
            ],
            "projects": [],
            "education": "Bachelor of Science in Computer Science\nBoston University, Boston, MA\nGraduated: 2017"
        },
        "style_notes": "Traditional and conservative. Emphasize stability, career progression, and professional growth. Use formal business language and focus on responsibilities alongside achievements."
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
  • experience: Array of objects with company, role, description
    - description: Use \\n for line breaks between bullet points
    - Start each bullet with "- " 
  • projects: Array of objects with title, details
    - details: Use \\n for line breaks
  • skills: Array of strings (categorized skills like "Languages: Python, JS")

⚠️  CRITICAL RULES:
  1. Output ONLY the JSON object - no additional text, commentary, or markdown
  2. Use \\n (not actual line breaks) for multi-line fields
  3. Ensure all strings are properly escaped
  4. All arrays must be valid JSON arrays with proper syntax
  5. Do NOT wrap JSON in markdown code blocks
  6. Do NOT add any text before or after the JSON

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