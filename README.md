# twitter_json2html

Twitter API の JSON / XML ファイルを読み込み、日別・月別の HTML ページを生成するツール。

## 機能

### ツイート変換
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

### DM (ダイレクトメッセージ) 変換
- DM JSON (v1.1 形式) および XML 形式に対応
- 会話相手ごとにページを自動グルーピング
- オーナー (自分) を最頻出ユーザから自動検出
- 自分宛メッセージ (`_self`) の対応
- チャットバブル UI (送信: 右/青、受信: 左/白)
- 日付区切り表示
- エンティティのリンク化 (XML はテキストから自動検出)

## セットアップ

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
git clone https://github.com/msakai/twitter_json2html.git
cd twitter_json2html
uv sync
```

## 使い方

### ツイート変換

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

### DM 変換

1. `data_dm/` ディレクトリに DM の JSON または XML ファイルを配置する
2. スクリプトを実行する

```bash
uv run python -m twitter_json2html.dm_main [data_dir] [-o output_dir]
```

- `data_dir`: DM JSON/XML ファイルが格納されたディレクトリ (デフォルト: `./data_dm`)
- `-o`, `--output`: 出力ディレクトリ (デフォルト: `./output_dm`)

3. 出力ディレクトリに HTML が生成される

```
output_dm/
├── index.html                # 会話相手一覧
└── conversations/
    ├── screen_name.html      # 相手ごとの会話ページ
    └── _self.html            # 自分宛メッセージ
```

4. ブラウザで確認する

```bash
open output_dm/index.html
```

## 対応ファイル形式

### ツイート

| 形式 | 拡張子 | 判別条件 |
|------|--------|----------|
| v1.0 XML | `.xml` | `<status>` ルート要素 |
| v1.1 JSON | `.json` | トップレベルに `user` オブジェクトが存在 |
| v1.1 拡張モード JSON | `.json` | `full_text` フィールドが存在 |
| v2 API レスポンス JSON | `.json` | トップレベルに `data` キーが存在 |
| v2 単体ツイート JSON | `.json` | `author_id` フィールドが存在し `user` が不在 |

同一ツイート ID の JSON と XML が両方存在する場合、JSON が優先されます。

### DM

| 形式 | 拡張子 | 判別条件 |
|------|--------|----------|
| DM XML | `.xml` | `<direct-messages>` または `<direct_message>` ルート要素 |
| DM JSON | `.json` | `sender` / `recipient` オブジェクトを含む v1.1 形式 |

同一 DM ID の JSON と XML が両方存在する場合、JSON が優先されます。

## プロジェクト構成

```
twitter_json2html/
├── pyproject.toml              # プロジェクト設定
├── data/                       # ツイート JSON/XML 配置先 (gitignore)
├── output/                     # ツイート出力先 (gitignore)
├── data_dm/                    # DM JSON/XML 配置先 (gitignore)
├── output_dm/                  # DM 出力先 (gitignore)
├── templates/                  # Jinja2 テンプレート
│   ├── base.html               # ベーステンプレート (CSS 埋め込み)
│   ├── macros.html             # ツイートカード描画マクロ
│   ├── index.html              # ツイート一覧ページ
│   ├── daily.html              # 日別ページ
│   ├── monthly.html            # 月別ページ
│   ├── dm_base.html            # DM ベーステンプレート (base.html 継承)
│   ├── dm_index.html           # DM 会話一覧ページ
│   └── dm_conversation.html    # DM 会話ページ
└── twitter_json2html/          # Python パッケージ
    ├── main.py                 # ツイート変換エントリポイント
    ├── loader.py               # ツイート読み込み・グルーピング
    ├── normalizer.py           # ツイート正規化 (v1.0 XML / v1.1 / v2)
    ├── tweet.py                # テキスト処理 (エンティティ→HTML)
    ├── renderer.py             # ツイートテンプレート描画
    ├── dm_main.py              # DM 変換エントリポイント
    ├── dm_loader.py            # DM 読み込み・会話グルーピング
    ├── dm_normalizer.py        # DM 正規化 (JSON / XML)
    └── dm_renderer.py          # DM テンプレート描画
```
