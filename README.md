# twitter_json2html

Twitter API の JSON ファイルを読み込み、日別・月別の HTML ページを生成するツール。

## 機能

- Twitter API v1.1 / v2 形式の自動判別・正規化
- 拡張ツイートモード (`full_text`) 対応
- エンティティ (URL, ハッシュタグ, メンション) のリンク化
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

1. `data/` ディレクトリに Twitter API の JSON ファイルを配置する (1ファイル1ツイート)
2. スクリプトを実行する

```bash
uv run python -m twitter_json2html.main
```

3. `output/` ディレクトリに HTML が生成される

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

## JSON ファイルの形式

以下の形式に対応しています:

| 形式 | 判別条件 |
|------|----------|
| v1.1 単体ツイート | トップレベルに `user` オブジェクトが存在 |
| v1.1 拡張モード | `full_text` フィールドが存在 |
| v2 API レスポンス | トップレベルに `data` キーが存在 |
| v2 単体ツイート | `author_id` フィールドが存在し `user` が不在 |

## プロジェクト構成

```
twitter_json2html/
├── pyproject.toml          # プロジェクト設定
├── data/                   # JSON ファイル配置先 (gitignore)
├── output/                 # 生成先 (gitignore)
├── templates/              # Jinja2 テンプレート
│   ├── base.html           # ベーステンプレート (CSS 埋め込み)
│   ├── macros.html         # ツイートカード描画マクロ
│   ├── index.html          # 一覧ページ
│   ├── daily.html          # 日別ページ
│   └── monthly.html        # 月別ページ
└── twitter_json2html/      # Python パッケージ
    ├── main.py             # エントリポイント
    ├── loader.py           # JSON 読み込み・日付グルーピング
    ├── normalizer.py       # v1.1/v2 正規化
    ├── tweet.py            # テキスト処理 (エンティティ→HTML)
    └── renderer.py         # テンプレート描画・ファイル出力
```
