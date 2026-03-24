# municipal-service-catalog

自治体の行政サービス情報を収集・整理し、カテゴリ別に分類された構造化データとして公開するデータパイプライン＆Webアプリケーションです。

現在、東京都国分寺市のサービスデータをサンプルとして収録しています。

## 概要

- フラットなJSON形式のサービス一覧（`service_catalog.json`）を、カテゴリ別に階層化された構造に変換します
- 変換後のデータをGitHub Pages上のWebアプリケーションで閲覧できます
- サービスの検索、カテゴリごとの展開・折りたたみ、JSONダウンロードなどの機能を提供します
- GitHub Actionsによるビルド・デプロイの自動化に対応しています

## プロジェクト構成

```
municipal-service-catalog/
├── .github/workflows/
│   └── deploy.yml                 # GitHub Actions CI/CDパイプライン
├── scripts/
│   ├── convert_catalog.py         # ステージ1: フラット→階層構造への変換
│   └── build_data.py              # ステージ2: Web公開用データの生成
├── data_source/
│   └── kokubunji-city.json        # 変換済み自治体データ（階層構造）
├── docs/                          # 静的Webサイト＆生成データ
│   ├── index.html                 # メインSPAフロントエンド
│   ├── municipality.html          # 自治体詳細ページ（テンプレート）
│   ├── css/
│   │   └── style.css              # フォールバック用スタイル
│   └── data/
│       ├── municipalities.json    # 自治体一覧
│       └── {municipality-id}/     # 自治体別データディレクトリ
│           ├── all.json           # 全カテゴリ統合データ
│           └── {category}.json    # カテゴリ別データ
├── service_catalog.json           # 入力データ（フラットなサービス一覧）
└── README.md
```

## 処理内容

データは2段階のパイプラインで処理されます。

### ステージ1: データ変換（`convert_catalog.py`）

`service_catalog.json`（フラットなサービス配列）を読み込み、以下の処理を行います。

- 和暦（例: 令和7年5月28日）をISO 8601形式（2025-05-28）に変換
- URLからサービスIDを抽出（取得できない場合は連番IDを生成）
- サービスラベルの先頭要素をもとにカテゴリ別にグループ化
- 21種類の日本語カテゴリ名を英語IDにマッピング（例: 子育て・教育 → `childcare-education`）
- サービス数の多い順にカテゴリをソート
- 最新の公開日から `last_updated` を算出

出力される階層構造:

```json
{
  "municipality": { "id": "...", "name": "...", "homepage": "...", "last_updated": "..." },
  "categories": [
    {
      "id": "childcare-education",
      "name": "子育て・教育",
      "services": [
        { "id": "...", "name": "...", "url": "...", "description": "...", "tags": [...], "eligibility": "...", "howToApply": "..." }
      ]
    }
  ]
}
```

### ステージ2: Web公開用データ生成（`build_data.py`）

`data_source/` 配下の全JSONファイルを読み込み、以下のファイルを `docs/data/` に生成します。

- `municipalities.json` — 参加自治体の一覧
- `{municipality-id}/all.json` — 自治体の全カテゴリ統合データ
- `{municipality-id}/{category-id}.json` — カテゴリ別データ

## 使い方

### 前提条件

- Python 3.10以上
- 外部パッケージのインストールは不要です（標準ライブラリのみ使用）

### ローカルでの実行

1. **サービスカタログの変換**

```bash
python scripts/convert_catalog.py service_catalog.json \
  --municipality-id "kokubunji-city" \
  --municipality-name "国分寺市" \
  --homepage "https://www.city.kokubunji.tokyo.jp" \
  --output-dir "data_source"
```

引数を省略した場合は国分寺市のデフォルト値が使用されます。

2. **Web公開用データのビルド**

```bash
python scripts/build_data.py
```

`data_source/` 配下のデータを読み込み、`docs/data/` にWebアプリ用のJSONファイルを生成します。

3. **Webアプリの確認**

`docs/index.html` をブラウザで開くか、ローカルサーバーを起動して確認します。

```bash
python -m http.server 8000 -d docs
```

ブラウザで `http://localhost:8000` にアクセスすると、自治体一覧が表示されます。

### GitHub Actionsによる自動デプロイ

`main` または `master` ブランチへのプッシュ時、GitHub Actionsが以下を自動実行します。

1. `service_catalog.json` が存在する場合、`convert_catalog.py` を実行
2. `build_data.py` を実行してWeb公開用データを生成
3. `docs/` ディレクトリをGitHub Pagesにデプロイ

手動実行（workflow_dispatch）にも対応しています。
