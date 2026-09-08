# R2 File Manager

> [!IMPORTANT]
> このStandaloneアプリの主要機能は `dommyttdev2/comfyui-batch-studio` の **モデル配置 / R2ファイル管理** へ統合されました。新規のComfyUI Batch Studio運用では、R2管理の正本はBatch Studio側です。このrepositoryはStandalone版・移行元・既存利用者向けとして維持します。

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Cloudflare R2](https://img.shields.io/badge/Cloudflare-R2-F38020?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/r2/)

Cloudflare R2 をブラウザから操作する、Windows 向けのローカルファイルマネージャーです。バケットやオブジェクトの管理、大容量ファイルのマルチパートアップロード、ダウンロード URL の一括生成を、Cloudflare Dashboard を行き来せずに実行できます。

アップロード時はブラウザでファイルを分割し、ローカルサーバー経由で R2 へ順次転送します。ファイル全体の一時コピーを作らないため、数 GB のファイルもローカルディスク容量を圧迫せずに扱えます。

> [!IMPORTANT]
> このアプリはローカル利用を前提としています。サーバーは `127.0.0.1` のみにバインドされ、LAN やインターネットへ公開する機能はありません。

## 主な機能

- R2 接続情報のテストと安全な保存
- バケットの一覧・作成・空バケットの削除
- フォルダー形式のオブジェクト一覧と、バケット全体のファイル名検索
- ドラッグ＆ドロップ対応の並列マルチパートアップロード
- アップロードの一時停止・再試行・キャンセル・アプリ再起動後の再開
- オブジェクトのダウンロード・移動・名前変更・複数選択削除
- 公開 URL または有効期限付き署名 URL の生成
- URL、`curl`、`wget`、`aria2c` コマンドの一括生成
- 一括ダウンロード対象を名前付きテンプレートとして保存・再利用
- アカウント全体のストレージ使用量とオブジェクト数の表示（任意）
- CLI からのバケット・オブジェクト一覧取得

## 必要なもの

- Windows
- Python 3.11 以上
- Cloudflare R2 を有効化したアカウント
- R2 の Access Key ID と Secret Access Key

R2 の認証情報は、Cloudflare Dashboard の **R2 Object Storage → Overview → API Tokens** から作成できます。バケットの一覧・作成・削除を含むすべての機能を使う場合は `Admin Read & Write` が必要です。詳細は [Cloudflare R2 の認証ドキュメント](https://developers.cloudflare.com/r2/api/tokens/) を参照してください。

Secret Access Key は作成直後にしか表示されないため、安全な場所へ控えてください。

## クイックスタート

PowerShell で次のコマンドを実行します。

```powershell
git clone https://github.com/toshiki-takedomi/r2-file-manager.git
cd r2-file-manager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m r2_file_manager
```

ブラウザで `http://127.0.0.1:8877` が自動的に開きます。8877 番ポートが使用中の場合は、次の空きポートを自動選択します。

初回起動後、右上の設定ボタンから次の値を入力してください。

1. Cloudflare Account ID
2. R2 Access Key ID
3. R2 Secret Access Key
4. Public URL（公開バケットまたはカスタムドメインを使う場合のみ）
5. Cloudflare API Token（ストレージ使用量を表示する場合のみ）

接続テストが成功したら設定を保存します。

## GUI の起動方法

セットアップが完了した環境では、PowerShell を開いてプロジェクトのディレクトリへ移動し、次のコマンドを実行します。

```powershell
.\.venv\Scripts\Activate.ps1
r2-file-manager
```

または、仮想環境を有効化せずに直接起動できます。

```powershell
.\.venv\Scripts\r2-file-manager.exe
```

起動すると既定のブラウザで GUI が自動的に開きます。自動的に開かない場合は、PowerShell に表示された `http://127.0.0.1:<ポート番号>` をブラウザで開いてください。

アプリの使用中は PowerShell のウィンドウを閉じないでください。終了するには、PowerShell で `Ctrl+C` を押します。

## CLI

インストール後は `r2-file-manager` コマンドも利用できます。サブコマンドを省略すると Web 画面を起動します。

```powershell
# ヘルプ
r2-file-manager --help

# Web画面を起動
r2-file-manager serve

# バケット一覧
r2-file-manager list-buckets
r2-file-manager list-buckets --json

# バケット直下または指定プレフィックスの一覧
r2-file-manager list-objects my-bucket
r2-file-manager list-objects my-bucket --prefix images/

# サブフォルダーを含む全オブジェクトをJSONで取得
r2-file-manager list-objects my-bucket --recursive --json
```

各コマンドの詳細は `r2-file-manager <サブコマンド> --help` で確認できます。

## 環境変数

接続情報は Web 画面から保存する代わりに、環境変数から読み込むこともできます。

| 変数 | 必須 | 用途 |
| --- | --- | --- |
| `R2_ACCOUNT_ID` | 接続時 | 32 文字の Cloudflare Account ID |
| `R2_ACCESS_KEY` | 接続時 | R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | 接続時 | R2 Secret Access Key |
| `R2_PUBLIC_URL` | 任意 | 公開バケットまたはカスタムドメインのベース URL |
| `CLOUDFLARE_API_TOKEN` | 任意 | ストレージ使用量表示用の Cloudflare API Token |
| `R2_FILE_MANAGER_PORT` | 任意 | Web 画面のポートを固定（1～65535） |
| `R2_FILE_MANAGER_DATA_DIR` | 任意 | 設定・アップロード状態の保存先を変更 |

PowerShell で現在のセッションに設定する例です。

```powershell
$env:R2_ACCOUNT_ID = "your-account-id"
$env:R2_ACCESS_KEY = "your-access-key-id"
$env:R2_SECRET_ACCESS_KEY = "your-secret-access-key"
r2-file-manager
```

CLI は保存済みの接続設定を優先し、保存済み設定がない場合に環境変数を使用します。Web 画面では接続設定ダイアログの「環境変数から再読込」操作で値を反映できます。

## 認証情報とローカルデータ

- Secret Access Key と Cloudflare API Token は Windows 資格情報マネージャーへ保存します。
- Secret は設定 JSON やログへ書き込みません。
- 資格情報マネージャーを利用できない場合も、平文ファイルへフォールバック保存しません。
- 通常設定は `%LOCALAPPDATA%\R2 File Manager\config.json` に保存します。
- 未完了アップロードは `uploads.json`、一括ダウンロードテンプレートは `batch_download_templates.json` として同じディレクトリに保存します。
- Web API は読み取り・変更の両方で、起動ごとに生成するリクエストトークンを要求します。

ストレージ使用量は Cloudflare REST API から取得します。有効にする場合は、Account の R2 読み取り権限を持つ Cloudflare API Token を別途指定してください。S3 用の Secret Access Key と Cloudflare API Token は別の認証情報です。

## 制限事項

- 現在の R2 エンドポイントは標準 jurisdiction（`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`）固定です。EU、FedRAMP、US jurisdiction 固有のバケットには対応していません。
- 接続確認と初期画面でバケット一覧を取得するため、バケット単位の `Object Read & Write` 認証情報だけでは利用できません。
- アップロード再開時は、ブラウザの制約により同じローカルファイルを再選択する必要があります。
- バケット削除は空のバケットに限ります。
- 一括ダウンロードは一度に最大 500 オブジェクトです。
- Public URL を設定していない場合、生成する署名 URL の有効期限は 1 時間です。

## 開発

開発用依存関係をインストールして Python テストを実行します。

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Node.js がある場合は、ダウンロードコマンド生成処理のテストも実行できます。

```powershell
node --test tests/test_download_utils.js
```

不具合報告や改善提案は [Issues](https://github.com/toshiki-takedomi/r2-file-manager/issues) へお願いします。Pull Request も歓迎します。

## セキュリティ上の注意

- このアプリで必要な操作だけを許可した、専用の R2 認証情報を使用してください。
- Public URL を設定すると、対象 URL は署名なしで共有されます。バケットの公開範囲を確認してください。
- 署名 URL や生成したダウンロードコマンドには、一時的なアクセス権が含まれます。公開場所へ貼り付けないでください。
- 共有 PC では、利用後に Windows 資格情報マネージャーから認証情報を削除してください。

このプロジェクトは Cloudflare の公式製品ではありません。

## ライセンス

このプロジェクトは [MIT License](https://opensource.org/license/mit) の下で公開されています。
