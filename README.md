# skit

Syllabus Kit

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

For use — runtime deps only:

```sh
uv sync
```

For development — adds tests, lint, type check:

```sh
uv sync --group dev
```

For docs:

```sh
uv sync --group docs
uv run mkdocs build -f docs/mkdocs.yml
```
