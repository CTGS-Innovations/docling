# Python Usage in CLI Folder

## Important Note

The `/home/corey/projects/docling/cli/` folder is an **exception** to the main project's Docker-only rule.

### Rules for this folder:
- ✅ **Python is allowed** to be used directly in this CLI folder
- ✅ **Virtual environment** (`.venv`) can be used for dependencies
- ✅ **Direct docling execution** is permitted from `.venv/bin/docling`

### User Responsibility:
- 🔑 **The user runs all Python commands** - not Claude
- 🔑 **Claude can reference Python paths** in code but user executes them
- 🔑 **Virtual environment setup** is managed by the user

### Contrast with Main Project:
- ❌ Main `/home/corey/projects/docling/` requires Docker for all Python tasks
- ❌ Main project: "NEVER run Python directly"
- ✅ CLI folder: Python usage is explicitly permitted

This exception exists because the CLI folder is a separate workspace for development and testing of docling functionality.