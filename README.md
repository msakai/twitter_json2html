# twitter_json2html

Twitter API の JSON / XML ファイルを読み込み、日別・月別の HTML ページを生成するツール。

## 機能

- Twitter API v1.1 / v2 JSON および v1.0 XML 形式に対応
- 拡張ツイートモード (`full_text`) 対応
- エンティティ (URL, ハッシュタグ, メンション) のリンク化
- エンティティ情報がない古いツイートではテキストから自動検出
- JSON/XML 間のツイート ID 重複排除 (JSON 優先)
- 引用ツイートのネスト表示
- 画像・動画メディアの埋め込み
- `display_text_range` によるテキスト表示範囲の制御
- Twitter ライクなカードレイアウト (レスポンシブ対応)
- CSS 埋め込み (外部ファイル不要)

## セットアップ

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
git clone https://github.com/msakai/twitter_json2html.git
cd twitter_json2html
uv sync
```

## 使い方

1. `data/` ディレクトリに Twitter API の JSON または XML ファイルを配置する (1ファイル1ツイート)
2. スクリプトを実行する

```bash
uv run python -m twitter_json2html.main [data_dir] [-o output_dir]
```

- `data_dir`: JSON/XML ファイルが格納されたディレクトリ (デフォルト: `./data`)
- `-o`, `--output`: 出力ディレクトリ (デフォルト: `./output`)

例:

```bash
# デフォルト (./data → ./output)
uv run python -m twitter_json2html.main

# ディレクトリを指定
uv run python -m twitter_json2html.main /path/to/json -o /path/to/html
```

3. 出力ディレクトリに HTML が生成される

```
output/
├── index.html          # 一覧ページ (日別・月別リンク)
├── daily/
│   └── YYYY-MM-DD.html # 日別ページ
└── monthly/
    └── YYYY-MM.html    # 月別ページ
```

4. ブラウザで確認する

```bash
open output/index.html
```

## 対応ファイル形式

| 形式 | 拡張子 | 判別条件 |
|------|--------|----------|
| v1.0 XML | `.xml` | `<status>` ルート要素 |
| v1.1 JSON | `.json` | トップレベルに `user` オブジェクトが存在 |
| v1.1 拡張モード JSON | `.json` | `full_text` フィールドが存在 |
| v2 API レスポンス JSON | `.json` | トップレベルに `data` キーが存在 |
| v2 単体ツイート JSON | `.json` | `author_id` フィールドが存在し `user` が不在 |

同一ツイート ID の JSON と XML が両方存在する場合、JSON が優先されます。

## プロジェクト構成

```
twitter_json2html/
├── pyproject.toml          # プロジェクト設定
├── data/                   # JSON/XML ファイル配置先 (gitignore)
├── output/                 # 生成先 (gitignore)
├── templates/              # Jinja2 テンプレート
│   ├── base.html           # ベーステンプレート (CSS 埋め込み)
│   ├── macros.html         # ツイートカード描画マクロ
│   ├── index.html          # 一覧ページ
│   ├── daily.html          # 日別ページ
│   └── monthly.html        # 月別ページ
└── twitter_json2html/      # Python パッケージ
    ├── main.py             # エントリポイント
    ├── loader.py           # JSON/XML 読み込み・重複排除・日付グルーピング
    ├── normalizer.py       # v1.0 XML / v1.1 / v2 JSON 正規化
    ├── tweet.py            # テキスト処理 (エンティティ→HTML)
    └── renderer.py         # テンプレート描画・ファイル出力
```
