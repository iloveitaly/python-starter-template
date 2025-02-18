#!/usr/bin/env bash

# Description: this syncs the project with the upstream python-starter-template repo.
#
#   - Skips all javascript updates
#   - You'll need to manually review conflicts of which there will be many

uv tool run --with jinja2_shell_extension \
  copier update --trust --skip-tasks --skip-answered \
  --exclude web
