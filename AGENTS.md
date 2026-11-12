# Repository instructions

## Project scope

- Work in this repository's current checkout.
- Stack: HTML/CSS/JavaScript + Python/FastAPI. Deployment target: Render.
- Preserve the team's supplied Notion mockup design unless the user requests a redesign.
- First scenario: 이윤제. Keep the other two candidate slots empty.
- Dialogue supports a server-side LLM and an explicit mock mode. State which mode was actually tested; do not claim a persistent database is connected.
- Preserve the team's confirmed timer, clue and ending rules in services/story.py and services/endings.py. Do not invent additional finalized world rules or classification criteria.

## Commits and collaboration

- Use Conventional Commit style for every commit: `type: summary`, optionally `type(scope): summary`.
- Use `feat`, `fix`, `docs`, `refactor`, `test`, `style`, `chore`, or `ci` according to the change. Use `docs` for explanation/comment-only changes.
- Keep commits focused. Do not mix unrelated changes.
- After the initial baseline, prefer a feature branch and Pull Request into `main` for shared work.
- Never commit API keys, credentials, signed download URLs, `.env` values, virtual environments, or personal tool configuration.
- Do not force push or rewrite shared history without explicit user instruction.

## Validation

- Run `python -m unittest discover -s tests -v` with the project environment for relevant Python changes.
- For JavaScript changes, check syntax with `node --check public/assets/js/app.js` when Node is available.
- For UI changes, inspect the local app at mobile and desktop sizes. `scripts/verify_ui.py` is available when Playwright and local Edge are installed.
- Report what was tested and any remaining limitations. See `CONTRIBUTING.md` for the team's workflow.
