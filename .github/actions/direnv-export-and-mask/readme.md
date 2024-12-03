# Export Direnv to GitHub Action's Environment & Mask Secrets

This action loads environment variables from direnv and automatically masks sensitive values in GitHub Actions logs. The environment is loaded into `$GITHUB_ENV` so it's available in future action steps.

## Features

- Automatically loads `.envrc` files using direnv
- Masks common secret formats including:
  - API keys (sk-*, api-*, key-*)
  - Tokens (phc_*, sntrys_*)
  - Base64 encoded strings
  - UUIDs
  - High entropy strings
  - Values with common secret suffixes (_KEY, _TOKEN, _SECRET, etc)
  - Environment variables starting with OP_ or DIRENV_
- Option to mask all environment variables

## Usage


```yml
steps:
  - uses: actions/checkout@v3

  - name: Load environment and mask secrets
    uses: iloveitaly/direnv-export-and-mask@master
    with:
      mask_all: 'true' # Optional, defaults to true
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `mask_all` | Mask all environment variables by default | false | true |

## Requirements

The action will automatically install:

- direnv if not already present
- Python 3.x if not already present

This assumes you have a `.envrc` file in your repository root.

## How it works

1. Checks for and installs required dependencies (direnv and Python)
2. Loads environment variables from direnv
3. Exports variables to GitHub Actions environment
4. Automatically detects and masks sensitive values in logs using pattern matching
