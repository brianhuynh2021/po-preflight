# MANDATORY RULE: GIT DISCIPLINE & LOCAL TESTING PROCESS

> **UNCHANGING PRINCIPLE (CRITICAL RULE):**
> 1. **ABSOLUTELY DO NOT commit and push directly to the `dev` or `main` branch.**
> 2. Every source code change, feature, or bug fix MUST be made on a **dedicated branch (feature branch / bugfix branch)**: `feat/<feature-name>` or `fix/<bug-name>`.
> 3. **LOCAL TESTING MUST SUCCEED 100%:**
>    - Run unit tests (`PYTHONPATH=src python3 -m unittest discover -s tests`).
>    - Run the frontend build (`npm run build` or check the linter) if the UI has changed.
>    - Only when all local tests pass may you commit on the feature branch and create a PR.
