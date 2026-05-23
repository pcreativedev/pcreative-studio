# Contributing to ThemeForge

Thanks for considering a contribution. This guide describes how to
report issues, propose changes, and submit pull requests.

ThemeForge is a Python/PyQt6 desktop GUI plus a small embedded
Node terminal server. The codebase is intentionally small and
unopinionated about frameworks — each stack scaffold and skill list
lives in `stacks.py`.

## Code of conduct

By participating you agree to follow the [Code of
Conduct](CODE_OF_CONDUCT.md). In short: be respectful, assume good
intent, focus on the technical problem.

## Reporting an issue

1. Reproduce on the latest `main` commit if possible.
2. Open an issue with:
   - Distro + kernel (`uname -a`)
   - Python version (`python3 --version`)
   - PyQt6 version (`pip show pyqt6`)
   - Node version (`node -v`)
   - The mode (scratch / recreate / adopt / existing) and the stack.
   - Steps to reproduce, expected, actual.
   - Relevant log output. ThemeForge prints to stderr; run it from
     a terminal: `python3 themeforge.py` so you capture tracebacks.

Sensitive data — API keys, license tokens — should NEVER be pasted
into an issue. ThemeForge's stderr redactor strips known key patterns
from the embedded log panel, but if you copy from a terminal session
double-check before sharing.

## Pull requests

### Setup

```bash
git clone https://github.com/pcreativedev/themeforge.git
cd themeforge
# Optional: virtual env. PyQt6 from distro packages tends to be
# easier than via pip due to the bundled Qt libraries.
sudo pacman -S python python-pyqt6 python-pyqt6-webengine    # Arch / CachyOS
# or
sudo apt install python3 python3-pyqt6 python3-pyqt6.qtwebengine

cd terminal && npm install && cd ..
./launch.sh
```

### Branch naming

Use short, descriptive branches:

- `feat/<short-name>` — new feature.
- `fix/<short-name>` — bug fix.
- `docs/<short-name>` — documentation only.
- `refactor/<short-name>` — code change without behaviour change.

Avoid branch names that imply a specific author or AI agent — keep
them about the change.

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) in
English:

```
feat: add multi-tab preview to ProjectWindow
fix: autoskills guard for nested mono-repo stacks
docs: clarify reference-analysis multi-turn flow
chore: bump terminal/node-pty to 1.1.0
refactor: extract context discovery into a helper
```

Keep the first line under 72 chars. Body (optional) explains *why*,
not *what*.

### Code style

- Python: PEP 8 with reasonable line length (~100). Type hints where
  they help readability. Avoid premature abstractions.
- JavaScript (in `terminal/`): no formatter enforced; match the
  existing style.
- Comments: prefer English when they document for other contributors;
  Spanish is fine for tooltips/UI strings if the surrounding code
  already uses Spanish (this is a Spanish-led project, but contributing
  English is welcome).

### What's in scope

- Bug fixes in any layer.
- New stacks in `stacks.py` (follow the existing dict shape:
  `name`, `category`, `language`, `min_version`, `scaffold`, `skills`,
  `notes`).
- Improvements to the embedded preview, terminal, GitHub flow,
  reference-analysis dialog.
- Documentation, examples, screenshots, GIFs.
- Additional AI providers in `ai_providers.py` (each provider
  invocation is a `subprocess` boundary — no SDK lock-in).

### What's out of scope (without prior discussion)

- Rewriting the GUI framework (PyQt6 → PySide6 / Qt6 native /
  Electron, etc.). Open an issue first.
- Renaming or deprecating supported stacks.
- Adding stack-specific business logic that doesn't belong in a
  scaffolder. Stack-specific behaviour goes in templates the agent
  reads, not in ThemeForge core.
- Direct integration with cloud licensing providers (Lemon Squeezy,
  Polar, Paddle…). The licensing scaffold ships a schema, not adapters.

### Tests

ThemeForge has minimal automated tests right now (smoke tests on
setup-script generation only). For each PR, please:

1. Run `python3 -m py_compile *.py` to catch syntax errors.
2. Manually exercise the affected path in the GUI on at least one
   stack + mode combination.
3. If you touched the licensing scaffold, generate a sample project
   with the checkbox on and verify the templates render with the
   expected placeholders.

## License

By contributing, you agree your contributions are licensed under
GPL v3 (the same license as the project). See `LICENSE`.
