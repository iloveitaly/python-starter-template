import glob
import hashlib
import os
import subprocess


def dump_direnv_diff():
    # Execute command and capture output
    result = subprocess.run(
        "CI=true direnv exec ~ direnv export json",
        shell=True,
        capture_output=True,
        text=True,
    ).stdout

    # Glob all .env* files and hash their modified times
    env_files = glob.glob(".env*")
    mtimes = "".join(str(os.path.getmtime(f)) for f in env_files)
    sha = hashlib.sha256(mtimes.encode()).hexdigest()

    # Ensure tmp/ exists and write to file
    os.makedirs("tmp", exist_ok=True)
    with open(f"tmp/{sha}.json", "w") as f:
        f.write(result)
