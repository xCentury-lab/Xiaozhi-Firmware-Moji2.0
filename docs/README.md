# 📚 ドキュメントインデックス

> **Xiaozhi-Firmware-update プロジェクトの全ドキュメントの目次**
> 最終更新: 2026-04-18

プロジェクト全体のドキュメントはこの `docs/` 配下に集約しています。各文書は役割別にカテゴリ分けされています。

---

## 🚀 はじめての方へ

初めて環境構築する方は以下の順で読んでください:

1. **[../README.md](../README.md)** — プロジェクト概要（4軸カスタマイズ・STEP1/STEP2 方針）
2. **[setup/linux.md](setup/linux.md)** または **[setup/windows.md](setup/windows.md)** — OS 別の環境構築手順
3. **[build-plan.md](build-plan.md)** — 詳細な計画書（Phase 0-A 〜 2-G）
4. **[operations/flash-guide.md](operations/flash-guide.md)** — ビルド済 firmware の書込手順

---

## 📁 カテゴリ別ドキュメント

### 🏗 セットアップ（[setup/](setup/)）

初回環境構築の詳細手順。OS ごとに分かれています。

| ドキュメント | 内容 |
|---|---|
| **[setup/linux.md](setup/linux.md)** | Ubuntu 22.04/24.04 でのビルド環境構築。ESP-IDF v5.5.4、dialout 権限、brltty 対策、環境変数まで |
| **[setup/windows.md](setup/windows.md)** | Windows 11 + ESP-IDF インストーラでのビルド環境構築 |

### 📐 設計・計画（直下）

プロジェクトの設計・計画・仕様書。

| ドキュメント | 内容 |
|---|---|
| **[build-plan.md](build-plan.md)** | **メイン計画書**（972行）— 2段階構成（STEP1 英語版 → STEP2 日本語版）、Phase 0-A 〜 2-G の詳細、マイルストーン、出荷フロー |
| **[asset-spec.md](asset-spec.md)** | 画像（ロゴ）・音声（起動音）の仕様書。Phase 0-A 完了後に仕様確定予定 |
| **[translation-source.md](translation-source.md)** | 翻訳対象ファイル一覧（STEP2 日本語化で使用）。本家翻訳を採用する場合は簡略化可能 |

### ⚙️ 運用・書込（[operations/](operations/)）

ビルド済 firmware の書込・配布運用手順。

| ドキュメント | 内容 |
|---|---|
| **[operations/flash-guide.md](operations/flash-guide.md)** | **ファームウェア書込手順書**（量産ライン作業者向け・10 ステップ）— esptool で 1 行書込、トラブルシューティング、SHA256 検証、作業記録テンプレート |
| **[operations/wake-word-selection.md](operations/wake-word-selection.md)** | **ウェイクワード選定ガイド** — 用途別推奨組合せ、実機検証結果（Jarvis 失敗の原因分析）、プリビルド済ウェイクワード全リスト、切替手順 |
| **[operations/audio-assets.md](operations/audio-assets.md)** | **音声アセット リファレンス** — 音声ファイルの所在（common/ と locales/{lang}/）、用途、埋込方式（EMBED_FILES）、Kconfig 制御、カスタム音声差替手順 |
| **[operations/esp32s3-download-mode.md](operations/esp32s3-download-mode.md)** | **ESP32-S3 ダウンロードモード投入** — `device reports readiness to read but returned no data` 等のハング対処。BOOT+RST シーケンス、`--before/--after no_reset` フラグ、進行確認テクニック、3 個体のデバイス指紋表 |
| **[operations/ota-url-inplace-rewrite.md](operations/ota-url-inplace-rewrite.md)** | **OTA URL の in-place 書き換え** — 既存 `.bin` の OTA サーバ URL を再ビルドなしで変更。NUL パディングでサイズ不変、SHA-256 整合性のリスクと運用原則、再ビルドとの使い分け |
| **[operations/esp-vocat-build-procedure.md](operations/esp-vocat-build-procedure.md)** | **ESP-VoCat OEM カスタムビルド完全手順** — v2.2.6 ESP-VoCat (旧 EchoEar) の Alexa + 你好喵伴 デュアル wake word ビルド。`movemodel.py` で `srmodels.bin` 差し替え、worktree 分離、既知バグ回避、Flash レイアウト図 |
| **[operations/esp-vocat-partition-layout.md](operations/esp-vocat-partition-layout.md)** | **ESP-VoCat パーティション・アセット仕様** — `0x800000` partition に `expression_assets.bin` (ESP-VoCat) vs `generated_assets.bin` (他 SKU) の使い分け、Kconfig 切替、ビルド/書込/OTA 各フェーズの影響、既知の落とし穴 4 件、検証コマンド集 |
| **[operations/wsl-usb-device-setup.md](operations/wsl-usb-device-setup.md)** | **WSL から ESP32 デバイスへの USB アクセス手順** — WSL2 が USB device を直接見れない根本理由 (First Principles)、案 A `usbipd-win` (推奨、永続化) と 案 B Windows PowerShell 直接実行 (即時)、量産ライン向けクイックリファレンス、トラブルシューティング 5 件 |

### 🔍 レビュー・調査（[Review/](Review/)）

Phase 0 の事前調査・レビュー結果。過去の意思決定のエビデンス。

| ドキュメント | 内容 |
|---|---|
| **[Review/project-review.md](Review/project-review.md)** | プロジェクト全体レビュー（2026-04-18 時点のスケルトン評価、STEP1/STEP2 設計の妥当性） |
| **[Review/code-quality-report.md](Review/code-quality-report.md)** | `tools/` / `build/` 配下のコード品質評価（バグ・重複・リファクタ候補） |
| **[Review/linux-build-compatibility.md](Review/linux-build-compatibility.md)** | Ubuntu でのビルド互換性調査（ESP-IDF 要件・差分対応）※冒頭の更新警告に従い v5.5.x 前提で読むこと |
| **[Review/linux-environment-setup-log.md](Review/linux-environment-setup-log.md)** | **実機セットアップ実測ログ**（2026-04-18 Ubuntu 22.04.5 での構築結果・発見事項 6 件） |
| **[Review/phase-gate-0A-language-assets.md](Review/phase-gate-0A-language-assets.md)** | Phase 0-A のゲート判定（en-US/ja-JP アセット存在確認） |
| **[Review/action-items.md](Review/action-items.md)** | アクションアイテム一覧（A-/B-/C-/D- で優先度別管理、D-系は実機検証後の追加項目） |

---

## 📂 ディレクトリ構造と主要ドキュメント

```
Xiaozhi-Firmware-update/
├── README.md                  ★ プロジェクト入口（GitHub トップ表示）
├── docs/                      ★ ドキュメント集約
│   ├── README.md              （本ファイル・マスターインデックス）
│   ├── build-plan.md          （メイン計画書）
│   ├── asset-spec.md
│   ├── translation-source.md
│   ├── setup/
│   │   ├── linux.md
│   │   └── windows.md
│   ├── operations/
│   │   └── flash-guide.md     （量産書込手順）
│   └── Review/
│       ├── project-review.md
│       ├── code-quality-report.md
│       ├── linux-build-compatibility.md
│       ├── linux-environment-setup-log.md
│       ├── phase-gate-0A-language-assets.md
│       └── action-items.md
│
├── firmware/README.md         ← ディレクトリ別 README（ここに何が置かれるかの説明）
├── tools/README.md            ← 同上（OTA パッチツール群の使い方）
├── assets/logos/README.md     ← 同上
├── assets/sounds/README.md    ← 同上
│
├── build/matrix.yaml          ← ビルドマトリクス定義（コード扱い）
├── scripts/                   ← セットアップ・検証スクリプト
└── firmware/                  ← ビルド成果物（.gitignored）
```

**命名ルール**:
- **横断的・汎用のドキュメント** → `docs/` 配下
- **ディレクトリ固有の説明**（「ここに何が置かれるか」「このツールの使い方」）→ 当該ディレクトリの `README.md`

---

## 🗺 役割別・読むべきドキュメント

### 👨‍💻 ビルド担当エンジニア

1. [setup/linux.md](setup/linux.md) or [setup/windows.md](setup/windows.md) — 環境構築
2. [build-plan.md](build-plan.md) § Phase 0-C 〜 1-A — ビルド手順
3. [Review/linux-environment-setup-log.md](Review/linux-environment-setup-log.md) — 実測の所要時間・ハマりどころ
4. [Review/action-items.md](Review/action-items.md) — 自分の担当タスク確認

### 🏭 量産ライン作業者

1. [operations/flash-guide.md](operations/flash-guide.md) — **書込手順書（唯一必須）**
2. [firmware/README.md](../firmware/README.md) — ファームウェア格納場所の確認
3. 不具合時: [operations/flash-guide.md § トラブルシューティング](operations/flash-guide.md#-トラブルシューティング)

### 🎙 ウェイクワード担当

1. [operations/wake-word-selection.md](operations/wake-word-selection.md) — 用途別推奨と切替手順
2. [build-plan.md](build-plan.md) § STEP1/STEP2 — 言語バリアント全体計画

### 📱 配布担当・営業

1. [../README.md](../README.md) — プロジェクト概要
2. [build-plan.md](build-plan.md) § 24章 — マイルストーン・出荷スケジュール
3. [asset-spec.md](asset-spec.md) — ロゴ・起動音の素材仕様

### 🈶 翻訳担当

1. [translation-source.md](translation-source.md) — 翻訳対象の範囲
2. [Review/phase-gate-0A-language-assets.md](Review/phase-gate-0A-language-assets.md) — 本家翻訳活用の判断材料

### 📋 プロジェクトマネージャ

1. [build-plan.md](build-plan.md) § 4章 全体スケジュール
2. [Review/action-items.md](Review/action-items.md) — 全アクションの進捗
3. [Review/project-review.md](Review/project-review.md) — 計画完成度評価

---

## 🔄 ドキュメント更新ルール

### 新規ドキュメント追加時

1. カテゴリに応じて配置:
   - セットアップ手順 → `docs/setup/`
   - 運用手順（書込・QA・出荷）→ `docs/operations/`
   - 設計・計画・仕様 → `docs/` 直下
   - レビュー結果・調査報告 → `docs/Review/`
   - ディレクトリ固有の説明 → 該当ディレクトリの `README.md`
2. **本ファイル（`docs/README.md`）のテーブルに追加**
3. 関連ドキュメントからクロスリンクを追加

### 既存ドキュメントの更新時

- 大きな変更は末尾の「**改訂履歴**」テーブルに追記
- 実機検証で古い情報が判明した場合、冒頭に **⚠️ 更新警告** を追加してから本文を修正（履歴を残す）
- 例: [Review/linux-build-compatibility.md](Review/linux-build-compatibility.md) の冒頭を参照

### ファイル移動・リネーム時

1. 全 `.md` ファイル内のリンクを `grep -r "旧パス" docs/` で確認
2. 移動 → リンク一括修正 → 動作確認
3. ルート `README.md` のリンクも忘れず更新

---

## 📞 メンテナ

- xxc (xxc@ctoch.jp)

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版作成。`SETUP.md`/`SETUP-linux.md`/`firmware/FLASH-GUIDE.md` を `docs/` 配下に統合 | xxc@ctoch.jp |
