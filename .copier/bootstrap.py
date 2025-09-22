"""
This script is executed by Copier after the project is generated.

The 'right' way to do this is jinja syntax, but I want this project to actually function on it's own, which is why we do
this hacky string substitution here.
"""
import json
import os
import re
import shutil
from pathlib import Path
import uuid

# Change to parent directory of the script
script_dir = Path(__file__).parent
os.chdir(str(script_dir.parent))

# Copy README.md from .copier to project root
shutil.copy2(".copier/README.md", "README.md")

# Load copier answers
copier_answers = json.loads(Path(".copier-answers.yml").read_text())


def replace_lines_in_files(replacements: dict[str, list[tuple[str, str]]]):
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

        for pattern, replacement in patterns:
            content = re.sub(
                pattern,
                replacement,
                content,
                flags=re.MULTILINE,
            )

        path.write_text(content)


replacements = {
    "pyproject.toml": [
        (r'^name = ".*$', f'name = "{copier_answers["project_slug"]}"'),
        (r'^python-starter-template = "app.cli:app".*$', f'{copier_answers["project_slug"]} = "app.cli:app"')
    ],
    "env/not_production.sh": [
        (
            r"^export EMAIL_FROM_ADDRESS=.*$",
            f"export EMAIL_FROM_ADDRESS={copier_answers['from_email']}",
        ),
        (
            r"^export OP_ACCOUNT=.*$",
            f"export OP_ACCOUNT={copier_answers['one_password_account']}",
        ),
        (
            r"^export OP_VAULT_UID=.*$",
            f"export OP_VAULT_UID={copier_answers['one_password_vault']}",
        ),
        (
            r"^SESSION_SECRET_KEY=.*$",
            f"SESSION_SECRET_KEY={uuid.uuid4()}"
        ),
        (
            r"web\.localhost",
            f"{copier_answers['project_slug']}.localhost"
        )
    ],
    "Justfile": [
        (r"^PROJECT_NAME :=.*$", f'PROJECT_NAME := "{copier_answers["project_slug"]}"'),
    ],
    "just/build.just": [
        (
            r"^PYTHON_PRODUCTION_IMAGE_NAME :=.*$",
            f'PYTHON_PRODUCTION_IMAGE_NAME := "{copier_answers["production_image_name"]}"',
        ),
    ],
    ".localias.yaml": [
        (
            r"web\.localhost",
            f'{copier_answers["project_slug"]}.localhost',
        ),
    ]

}

replace_lines_in_files(replacements)
