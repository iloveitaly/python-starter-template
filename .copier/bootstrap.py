import json
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

# Change to parent directory of the script
script_dir = Path(__file__).parent
os.chdir(str(script_dir.parent))

# Copy README.md from .copier to project root
Path("README.md").unlink()
shutil.copy2(".copier/README.md", "README.md")

# Load copier answers
copier_answers = json.loads(Path(".copier/.copier-answers.yml").read_text())


def replace_lines_in_files(replacements: Dict[str, List[Tuple[str, str]]]):
    """
    replacements = {
        'file.txt': [
            (r'regex_pattern', 'replacement_line'),
            (r'another_pattern', 'another_replacement'),
        ]
    }
    """
    for filepath, patterns in replacements.items():
        path = Path(filepath)
        content = path.read_text()

        def full_line_match(existing_regex):
            return f"{'.' if not pattern.startswith('^') else ''}{pattern}.*$"

        for pattern, replacement in patterns:
            content = re.sub(
                full_line_match(pattern),
                replacement,
                content,
                flags=re.MULTILINE,
            )

        path.write_text(content)


replacements = {
    "pyproject.toml": [(r"^name = \"", f"name = \"{copier_answers['project-slug']}\"")],
    ".env.shared": [
        (
            r"export EMAIL_FROM_ADDRESS=",
            f"export EMAIL_FROM_ADDRESS={copier_answers['from_email']}",
        )
    ],
    "Justfile": [
        (r"^PROJECT_NAME :=", f"PROJECT_NAME := \"{copier_answers['project_slug']}\""),
        (
            r"^PYTHON_PRODUCTION_IMAGE_NAME :=",
            f"PYTHON_PRODUCTION_IMAGE_NAME := \"{copier_answers['production_image_name']}\"",
        ),
    ],
}

replace_lines_in_files(replacements)
