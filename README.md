# skit

Syllabus Kit

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

Development — installs runtime + dev tools by default:

```sh
uv sync
```

Run tests, lint, type check:

```sh
uv run pytest        # tests
uv run ruff check    # lint
uv run ruff format   # format
uv run pyright       # type check
```

Release / deploy — runtime deps only, no dev:

```sh
uv sync --no-dev
```

Build a distributable (dev/docs groups never included):

```sh
uv build             # -> dist/*.whl, *.tar.gz
```

Docs:

```sh
uv run --group docs mkdocs build -f docs/mkdocs.yml
```
