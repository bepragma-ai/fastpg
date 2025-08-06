# Installation

FastPG supports Python 3.9 and newer.

## Using pip

```bash
pip install git+https://github.com/bepragma-ai/fastpg.git
```

## Environment variables

Set the following optional variables to configure FastPG:

- `FASTPG_TZ` – timezone for auto-generated timestamps (default: `UTC`)
- `POSTGRES_READ_USER`, `POSTGRES_READ_PASSWORD`, `POSTGRES_READ_DB`,
  `POSTGRES_READ_HOST`, `POSTGRES_READ_PORT`
- `POSTGRES_WRITE_USER`, `POSTGRES_WRITE_PASSWORD`, `POSTGRES_WRITE_DB`,
  `POSTGRES_WRITE_HOST`, `POSTGRES_WRITE_PORT`

## Verify installation

```bash
python -c "import fastpg; print(fastpg.__version__)"
```

