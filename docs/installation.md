# Installation

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) - required for the `query` command

## Install Notes Vault

```bash
uv tool install https://github.com/tomzxcode/notes-vault.git
```

## Install ripgrep

The `nv query` command requires `ripgrep` to be installed on your system.

=== "Ubuntu / Debian"

    ```bash
    sudo apt install ripgrep
    ```

=== "macOS"

    ```bash
    brew install ripgrep
    ```

=== "Windows"

    ```bash
    winget install BurntSushi.ripgrep.MSVC
    ```

=== "Other"

    See the [ripgrep installation guide](https://github.com/BurntSushi/ripgrep#installation) for other platforms.

## Verify Installation

```bash
nv --help
rg --version
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
