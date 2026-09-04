# R2 File Manager

English | [日本語](README.ja.md)

> [!IMPORTANT]
> このStandaloneアプリの主要機能は `dommyttdev2/comfyui-batch-studio` の **モデル配置 / R2ファイル管理** へ統合されました。新規のComfyUI Batch Studio運用では、R2管理の正本はBatch Studio側です。このrepositoryはStandalone版・移行元・既存利用者向けとして維持します。

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Cloudflare R2](https://img.shields.io/badge/Cloudflare-R2-F38020?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/r2/)

R2 File Manager is a local, Windows-focused browser interface for Cloudflare R2. It lets you manage buckets and objects, upload large files with multipart uploads, and generate batch download URLs without repeatedly switching to the Cloudflare Dashboard.

During an upload, the browser splits the file into parts and transfers them to R2 through the local server. Because the application never creates a temporary copy of the entire file, it can handle multi-gigabyte files without consuming the same amount of extra disk space.

> [!IMPORTANT]
> This application is intended for local use. The server binds only to `127.0.0.1` and does not provide a way to expose itself to your LAN or the internet.

## Features

- Test and securely save R2 connection settings
- List, create, and delete empty buckets
- Browse objects as folders and search in real time using a local index
- Upload files with drag-and-drop and parallel multipart transfers
- Pause, retry, cancel, and resume uploads after restarting the application
- Download, move, rename, and bulk-delete objects
- Generate public URLs or time-limited presigned URLs
- Generate URL lists and `curl`, `wget`, or `aria2c` commands in batches
- Save and reuse named batch-download templates
- Display account-wide storage usage and object counts (optional)
- List buckets and objects from the CLI

## Requirements

- Windows
- Python 3.11 or later
- A Cloudflare account with R2 enabled
- An R2 Access Key ID and Secret Access Key

Create R2 credentials in the Cloudflare Dashboard under **R2 Object Storage → Overview → API Tokens**. The full feature set, including listing, creating, and deleting buckets, requires `Admin Read & Write`. See the [Cloudflare R2 authentication documentation](https://developers.cloudflare.com/r2/api/tokens/) for details.

The Secret Access Key is displayed only immediately after creation. Store it somewhere secure.

## Quick start

Run the following commands in PowerShell:

```powershell
git clone https://github.com/toshiki-takedomi/r2-file-manager.git
cd r2-file-manager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m r2_file_manager
```

The application automatically opens `http://127.0.0.1:8877` in your browser. If port 8877 is already in use, it selects the next available port.

On the first launch, open the settings dialog from the button in the upper-right corner and enter:

1. Cloudflare Account ID
2. R2 Access Key ID
3. R2 Secret Access Key
4. Public URL (only for a public bucket or custom domain)
5. Cloudflare API Token (only for displaying storage usage)

Test the connection, then save the settings.

## Launching the GUI

After setup, open PowerShell in the project directory and run:

```powershell
.\.venv\Scripts\Activate.ps1
r2-file-manager
```

You can also launch it directly without activating the virtual environment:

```powershell
.\.venv\Scripts\r2-file-manager.exe
```

The GUI opens automatically in your default browser. If it does not open, visit the `http://127.0.0.1:<port>` address displayed in PowerShell.

Keep the PowerShell window open while using the application. Press `Ctrl+C` in PowerShell to stop it.

## CLI

The `r2-file-manager` command is available after installation. Running it without a subcommand starts the web interface.

```powershell
# Show help
r2-file-manager --help

# Start the web interface
r2-file-manager serve

# List buckets
r2-file-manager list-buckets
r2-file-manager list-buckets --json

# List the bucket root or a specific prefix
r2-file-manager list-objects my-bucket
r2-file-manager list-objects my-bucket --prefix images/

# Recursively list all objects as JSON
r2-file-manager list-objects my-bucket --recursive --json
```

Run `r2-file-manager <subcommand> --help` for details about each command.

## Environment variables

You can load connection settings from environment variables instead of saving them through the web interface.

| Variable | Required | Purpose |
| --- | --- | --- |
| `R2_ACCOUNT_ID` | For connection | 32-character Cloudflare Account ID |
| `R2_ACCESS_KEY` | For connection | R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | For connection | R2 Secret Access Key |
| `R2_PUBLIC_URL` | Optional | Base URL for a public bucket or custom domain |
| `CLOUDFLARE_API_TOKEN` | Optional | Cloudflare API Token used to display storage usage |
| `R2_FILE_MANAGER_PORT` | Optional | Fixed web-interface port (1–65535) |
| `R2_FILE_MANAGER_DATA_DIR` | Optional | Custom location for settings and upload state |

Example for the current PowerShell session:

```powershell
$env:R2_ACCOUNT_ID = "your-account-id"
$env:R2_ACCESS_KEY = "your-access-key-id"
$env:R2_SECRET_ACCESS_KEY = "your-secret-access-key"
r2-file-manager
```

The CLI prefers saved connection settings and uses environment variables only when no saved settings exist. In the web interface, select **Reload from environment variables** in the connection settings dialog to populate the form.

## Credentials and local data

- The Secret Access Key and Cloudflare API Token are stored in Windows Credential Manager.
- Secrets are never written to the configuration JSON or application logs.
- If Credential Manager is unavailable, the application does not fall back to storing secrets in plaintext.
- Regular settings are stored in `%LOCALAPPDATA%\R2 File Manager\config.json`.
- Incomplete uploads are stored in `uploads.json`, and batch-download templates are stored in `batch_download_templates.json` in the same directory.
- Searchable object metadata is stored in `objects.sqlite3`. It is synchronized with every R2 bucket when the server starts and updated after in-app upload completion, moves, and deletions.
- Both read and write Web API requests require a per-launch request token.

Storage usage is retrieved through the Cloudflare REST API. To enable it, provide a separate Cloudflare API Token with account-level R2 read access. The S3 Secret Access Key and the Cloudflare API Token are different credentials.

## Limitations

- The R2 endpoint is fixed to the default jurisdiction (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`). Buckets in the EU, FedRAMP, and US jurisdictions are not supported.
- The application lists buckets during connection testing and on the initial screen, so bucket-scoped `Object Read & Write` credentials alone are not sufficient.
- Resuming an upload requires selecting the same local file again because browsers do not retain file access across sessions.
- Only empty buckets can be deleted.
- A batch download can contain up to 500 objects.
- When no Public URL is configured, generated presigned URLs expire after one hour.

## Development

Install the development dependencies and run the Python tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

If Node.js is available, run the download-command generation tests as well:

```powershell
node --test tests/test_download_utils.js
```

Use [Issues](https://github.com/toshiki-takedomi/r2-file-manager/issues) for bug reports and feature requests. Pull requests are welcome.

## Security notes

- Use dedicated R2 credentials that grant only the operations required by this application.
- When a Public URL is configured, the resulting URLs are shared without signatures. Verify the bucket's public-access settings.
- Presigned URLs and generated download commands contain temporary access credentials. Do not post them publicly.
- On a shared PC, remove the stored credentials from Windows Credential Manager after use.

This project is not an official Cloudflare product.

## License

This project is released under the [MIT License](https://opensource.org/license/mit).
