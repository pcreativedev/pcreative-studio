# Pcreative Studio plugins — examples

User plugins extend Pcreative Studio with custom stacks, template types and
AI agents **without forking the repo**. Each plugin is a `.py` file
placed under:

```
~/.config/themeforge/plugins/
```

Pcreative Studio auto-loads every `*.py` from that directory at startup
(files starting with `_` are ignored — convention for "disabled").

This folder ships **example plugins** you can copy to your local
plugins directory.

## How to use

```bash
mkdir -p ~/.config/themeforge/plugins
cp examples/plugins/my-custom-vite.py ~/.config/themeforge/plugins/
# Edit the copy with your own stack details, then restart Pcreative Studio.
```

## Public API

Your plugin can import from `themeforge_plugins`:

```python
from themeforge_plugins import (
    register_stack,            # add a new stack to the picker
    register_template_type,    # add an entry to the "Tipo" dropdown
    register_agent,            # add a new AI provider option
)
```

### `register_stack(key, **fields)`

Required fields: `name`, `category`, `language`, `min_version`, `scaffold`.
Optional: `skills` (list, default `[]`), `notes` (str, default `""`).

`scaffold` is a list of bash commands run in order at project creation.
Supports placeholders that Pcreative Studio substitutes: `__SLUG__`,
`__PROJECT__`, `__PASCAL__`, `__ORG_ID__`.

If `key` matches an existing stack from the repo, the plugin's
version **overrides** it. Pcreative Studio logs the override to stderr.

### `register_template_type(name)`

Appends `name` to the **Tipo** dropdown in the project form. Idempotent
(no duplicates).

### `register_agent(key, **fields)`

Required fields: `name`, `command`, `context_file`. Optional:
`autoskills_flag` (default `None`).

## Tips

- Disable a plugin without deleting it: rename `foo.py` → `_foo.py`.
- Errors in one plugin don't break the rest — Pcreative Studio prints the
  exception to stderr and keeps loading the others.
- Your plugin file IS Python: you can `import` anything you need,
  read JSON / YAML configs, etc. Pcreative Studio doesn't sandbox plugins.
- Stacks registered via plugins behave identically to repo stacks —
  same scaffold substitution, same autoskills flow, same UI picker
  category.
