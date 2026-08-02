[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.9"

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.9"]

[tool.setuptools.packages.find]
where = ["src"]
