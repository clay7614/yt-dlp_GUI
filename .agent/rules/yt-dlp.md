---
trigger: always_on
glob: "**/*.py"
description: yt-dlp_GUIリポジトリの構造と技術スタックに関する知識
---

# yt-dlp_GUI プロジェクト概要

このリポジトリは、`yt-dlp` を Python と `customtkinter` を使用してGUI化したアプリケーションです。

## プロジェクト構造と主要ファイル

*   [main.py](file:///c:/Users/Tangeken/Documents/GitHub/yt-dlp_GUI/main.py): エントリーポイント。`App` クラスがGUIの構築、設定管理、および `yt-dlp` の呼び出しを制御します。
*   [color.py](file:///c:/Users/Tangeken/Documents/GitHub/yt-dlp_GUI/color.py): テーマエディター機能。`EditTheme` クラスにより、ユーザーが動的に配色を変更し `theme.json` を生成できます。
*   [scraping.py](file:///c:/Users/Tangeken/Documents/GitHub/yt-dlp_GUI/scraping.py) / [scraping_2.py](file:///c:/Users/Tangeken/Documents/GitHub/yt-dlp_GUI/scraping_2.py): GitHub Releases からの更新情報取得用ユーティリティ。
*   [locale/](file:///c:/Users/Tangeken/Documents/GitHub/yt-dlp_GUI/locale): `gettext` を使用した多言語対応（日・英・韓）のための翻訳ファイル。

## 主要な機能

*   **GUIベース of ダウンロード**: `yt-dlp` の各種オプションをGUIから設定し実行。
*   **カスタムテーマ**: `customtkinter` の外観モード（ライト/ダーク）と、ユーザー定義の配色テーマに対応。
*   **自動更新確認**: 起動時にGitHubの最新リリースをチェック。
*   **多言語対応**: UI表示言語の切り替え機能。

## 技術スタック

*   **GUIライブラリ**: `customtkinter`
*   **コアエンジン**: `yt-dlp` (subprocessモジュール経由)
*   **ネットワーク**: `requests` (更新チェック用)
*   **解析**: `BeautifulSoup4` (スクレイピング用)
*   **国際化**: `gettext`
*   **その他**: `darkdetect`, `Pillow`, `configparser`

## 開発上の注意点

*   設定は `color.ini` 等のINIファイルや、`theme.json` で管理されています。
*   日本語コメントが推奨される環境です（`.agent/user_global` 参照）。
*   コミット時には適切なプレフィックス（add, update, fix等）を付与してください。
