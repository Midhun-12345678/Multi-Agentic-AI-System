import re

def resume_to_json(text):
    name = text.split("\n")[0]

    skills = re.findall(r"- (.+)", text)

    return {
        "name": name.strip(),
        "skills": skills[:10],
        "summary": text[:500],
        "raw": text
    }
