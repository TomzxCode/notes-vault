# Installation

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Install Notes Vault

```bash
uv tool install https://github.com/tomzxcode/notes-vault.git
```

## Verify Installation

```bash
nv --help
```

## Entry Points

Notes Vault installs several command aliases:

| Command | Description |
|---------|-------------|
| `nv` | Full CLI (admin + user commands) |
| `notes-vault` | Alias for `nv` |
| `nva` | Alias for `nv` |
| `notes-vault-admin` | Alias for `nv` |
| `nvu` | User-only CLI (`list`, `get`, `query` only) |
| `notes-vault-user` | Alias for `nvu` |

The user-only variants (`nvu`, `notes-vault-user`) expose only the read commands, suitable for restricted environments.
