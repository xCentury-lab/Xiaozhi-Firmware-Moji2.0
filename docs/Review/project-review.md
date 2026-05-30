# 小智固件更新项目 レビュー報告書

> **レビュー日**: 2026-04-18
> **対象リポジトリ**: `xCentury-lab/Xiaozhi-Firmware-update`
> **レビュー担当**: PAI
> **総合評価**: ★★★★☆（4/5）— 計画・設計は優秀、実装はスケルトン段階

---

## 1. 総合評価サマリ

| 評価軸 | 評価 | コメント |
|---|---|---|
| **計画・戦略** | ★★★★★ | 2段階（STEP1英語→STEP2日本語）の進行方針が明確 |
| **ドキュメント** | ★★★★★ | build-plan.md が極めて詳細、マイルストーン・リスク管理込み |
| **コード品質** | ★★★☆☆ | スケルトン段階。既存ツール群は動作するが改善余地あり |
| **セキュリティ** | ★★★★☆ | .gitignore で鍵・秘密を除外済み。一部改善推奨 |
| **リポジトリ構成** | ★★★★★ | 論理的に整理されたディレクトリ構造 |
| **再現性・自動化** | ★★★☆☆ | 設計は優秀だが、スクリプトが未実装 |

---

## 2. プロジェクト概要の理解

### 2-1. 目的

本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) の ESP32 ファームウェアを以下4軸でカスタマイズし、量産可能な体制を構築する:

1. **英語/日本語 UI 切替** — Kconfig ベースのコンパイル時選択
2. **OTA URL 組込** — `classism.net` をビルド時に埋込
3. **ボード別カスタムロゴ** — LVGL C配列で起動画面差替
4. **ボード別カスタム起動音** — WAV/Opus でブランド音差替

### 2-2. 進行方針

```
STEP 0: 共通基盤（1-2日）→ ESP-IDF構築 + 中国語版再現
STEP 1: 英語版（8-10日）→ 出荷可能状態まで
STEP 2: 日本語版（6-8日）→ 日本市場展開
合計: 15-20営業日
```

この段階的アプローチは**リスク分散**と**早期市場投入**の観点で非常に優れている。

---

## 3. ファイル別レビュー

### 3-1. ドキュメント層

| ファイル | 行数 | 評価 | コメント |
|---|---|---|---|
| `README.md` | 167行 | ★★★★★ | Quick Start、構成図、関連リソースが網羅的 |
| `SETUP.md` | 152行 | ★★★★☆ | 初回push手順が丁寧。トラブルシューティング充実 |
| `docs/build-plan.md` | 972行 | ★★★★★ | 計画書として非常に高品質。27章構成 |
| `docs/asset-spec.md` | 99行 | ★★★☆☆ | テンプレート段階。Phase 0-A で埋める前提 |
| `docs/translation-source.md` | 76行 | ★★★☆☆ | STEP2用テンプレート。現時点では想定のみ |
| `LICENSE` | 28行 | ★★★★★ | MIT + 本家派生の明記あり |

**特筆事項:**
- `build-plan.md` は972行の包括的計画書で、Phase定義・マイルストーン・リスク表・トリアージガイド・QAチェックリストまで含む。商用プロジェクトの計画書として非常に高い完成度。

### 3-2. ビルドパイプライン層

| ファイル | 行数 | 状態 | 評価 |
|---|---|---|---|
| `build/matrix.yaml` | 92行 | **実装済み** | ★★★★★ |
| `build/build_matrix.py` | 243行 | **スケルトン** | ★★★☆☆ |
| `build/inject_assets.py` | 132行 | **スケルトン** | ★★★☆☆ |
| `build/verify_build.py` | 168行 | **実装済み** | ★★★★☆ |

**matrix.yaml** — 非常に良い設計:
- ブランド別（company/stock）の定義が明確
- QA設定（サイズ範囲、必須/禁止文字列）がYAML内に統合
- STEP2 用の `Japanese` が準備済み（コメントアウト）

**build_matrix.py** — スケルトンだが設計は堅実:
- `build_one()` の5段階フロー（Kconfig注入→アセット注入→ビルド→配置→manifest生成）が論理的
- `--all` / `--board` / `--lang` / `--brand` / `--only-failed` のCLIインターフェース設計が良い
- `fail_fast` オプションで量産時の挙動を制御可能

**verify_build.py** — ほぼ実装完了:
- 6段階検証（サイズ/OTA URL/禁止文字列/言語キーワード/manifest整合性/SHA256照合）
- manifest.json との突合が組込済み

### 3-3. 既存ツール層

| ファイル | 行数 | 状態 | 評価 |
|---|---|---|---|
| `tools/patch_bin.py` | 45行 | 実装済み | ★★★☆☆ |
| `tools/patch_bin_2.py` | 45行 | 実装済み | ★★☆☆☆ |
| `tools/patch_release_zip.py` | 57行 | 実装済み | ★★★★☆ |
| `tools/inspect_ota.py` | 173行 | 実装済み | ★★★★★ |
| `tools/check.py` | 14行 | 実装済み | ★★☆☆☆ |
| `tools/check_bin.py` | 11行 | 実装済み | ★★☆☆☆ |

**inspect_ota.py** — 最高品質のツール:
- URL正規表現抽出、キーワード検出、総合判定の3層構造
- exit code の設計が適切（0=検出成功、1=読取問題、2=引数エラー）
- ユーザーフレンドリーなメッセージ出力

**patch_bin.py / patch_bin_2.py** — 機能するが改善余地:
- 2ファイルでほぼ同一コード（`OLD_URL` が異なるだけ）→ 統合推奨
- `patch_bin_2.py` の検証ロジックが `tenclass.net` をチェックしているが、このツールは `xiaozhi.jp` を置換するもの → **バグの可能性**

**check.py / check_bin.py** — 最小限の検証スクリプト:
- ZIPパス/binパスがハードコーディングされている
- CLIツールとして汎用化されていない

### 3-4. アセット層

| ディレクトリ | 状態 | 評価 |
|---|---|---|
| `assets/logos/master/` | 空（.gitkeep） | 素材待ち |
| `assets/logos/waveshare-.../company/` | 空（.gitkeep） | 素材待ち |
| `assets/sounds/master/` | 空（.gitkeep） | 素材待ち |
| `assets/sounds/waveshare-.../company/` | 空（.gitkeep） | 素材待ち |

ディレクトリ構造は設計通りに準備済み。READMEに命名規則・フォーマット要件・変換手順が記載されており、素材投入後すぐに作業開始可能。

---

## 4. 強み（Good Points）

### 4-1. 計画の質が非常に高い
- 2段階構成（英語先行→日本語追加）により、STEP1 だけで出荷可能
- 16項目のリスク表と対策が事前に定義済み
- マイルストーンに具体的な日付と完了条件が設定

### 4-2. トレーサビリティ設計
- `manifest.json` による全数照合（SHA256、ビルド日時、ソースcommit）
- QA基準がYAMLに定義され、自動検証可能

### 4-3. .gitignore が包括的
- ファームウェアバイナリ（.bin/.zip）除外
- OTA暗号鍵・署名鍵（.pem/.key/.crt/secrets/）除外
- ESP-IDF ビルド成果物の個別除外
- アセット中間ファイル除外

### 4-4. ドキュメントの一貫性
- README → SETUP → build-plan → asset-spec → translation-source が論理的に連鎖
- 各ディレクトリに README.md があり、自己説明的

### 4-5. ライセンス管理
- MIT License で本家との互換性を確保
- 派生物であることを LICENSE に明記
- OEM素材の著作権管理方針がドキュメント化

---

## 5. 改善提案

### 5-1. 高優先度（Phase 0 着手前に推奨）

#### A. patch_bin_2.py のバグ修正

```python
# 現状: xiaozhi.jp を置換するが、検証で tenclass.net をチェックしている
if b'classism.net' in patched and b'tenclass.net' not in patched:
    # ↑ xiaozhi.jp の残存チェックが漏れている
```

**修正案:**
```python
if b'classism.net' in patched and b'xiaozhi.jp' not in patched:
    print("OK: 新URL確認")
    print("OK: 旧URL消去確認")
```

#### B. patch_bin.py と patch_bin_2.py の統合

2ファイルが `OLD_URL` のみ異なるほぼ同一コード。以下のように統合推奨:

```python
# patch_bin.py（統合版）
PRESETS = {
    "tenclass": b'https://api.tenclass.net/xiaozhi/ota/',
    "xiaozhi-jp": b'https://xiaozhi.jp/xiaozhi/ota/',
}
# --preset tenclass / --preset xiaozhi-jp で切替
```

#### C. check.py / check_bin.py のハードコーディング除去

```python
# 現状: パスがハードコーディング
zip_path = "v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_patched.zip"

# 改善: CLI引数対応
if __name__ == '__main__':
    import sys
    zip_path = sys.argv[1] if len(sys.argv) > 1 else "..."
```

### 5-2. 中優先度（STEP1 中に対応推奨）

#### D. build_matrix.py の実装完了

現在 `[TODO]` マーカーが5箇所。Phase 0-A 完了後に以下を実装:
- `write_sdkconfig_defaults()` — 実際の Kconfig キー名で sdkconfig 書込
- `run_idf()` — subprocess.run のコメント解除
- `inject_assets` の実呼出し

#### E. CI/CD パイプライン整備

GitHub Actions で以下を自動化:
- matrix.yaml のバリデーション（YAML lint）
- Python スクリプトの構文チェック（flake8/mypy）
- verify_build.py のユニットテスト

#### F. Python 依存関係管理

```
# requirements.txt（未作成）
pyyaml>=6.0
Pillow>=10.0    # generate_board_logos.py で使用
```

### 5-3. 低優先度（STEP2 以降で検討）

#### G. セキュリティ強化

- `patch_release_zip.py` の `urllib.request.urlretrieve` は HTTPS 証明書検証がデフォルトだが、明示的に検証を強制する `ssl.create_default_context()` の使用を推奨
- OTA URL をソースコードにハードコーディングするのではなく、環境変数または暗号化設定ファイルからの読込を検討

#### H. テストの追加

- `verify_build.py` のユニットテスト（ダミーbin生成→検証）
- `inspect_ota.py` のユニットテスト
- `patch_bin.py` の統合テスト（パッチ前後の差分検証）

---

## 6. セキュリティレビュー

### 6-1. 良好な点

| 項目 | 状態 | 詳細 |
|---|---|---|
| 鍵ファイル除外 | ✅ | `.pem`, `.key`, `.crt`, `secrets/`, `.env` が .gitignore |
| Private リポジトリ | ✅ | OEM 情報の漏洩防止 |
| バイナリ除外 | ✅ | `.bin`, `.zip` が .gitignore |
| ライセンス明記 | ✅ | MIT + 本家派生を明示 |

### 6-2. 注意点

| 項目 | リスク | 推奨対応 |
|---|---|---|
| OTA URL がソースに平文 | 低 | ビルド時の環境変数注入を検討 |
| `push.ps1` にメールアドレス | 低 | Private リポジトリなら許容範囲 |
| `urllib.request.urlretrieve` | 低 | 証明書検証は有効だが明示的に |
| manifest.json に `builder` メールアドレス | 低 | 出荷バイナリ同梱時は要判断 |

---

## 7. アーキテクチャ評価

### 7-1. ビルドパイプライン設計

```
matrix.yaml (定義)
    ↓
build_matrix.py (オーケストレーション)
    ├── inject_assets.py (アセット注入)
    │   ├── inject_logo()
    │   ├── inject_sound()
    │   └── inject_translations()
    ├── idf.py (ESP-IDF ビルド)
    └── verify_build.py (品質検証)
        ↓
    firmware/{version}_{board}_{lang}_{brand}/
        ├── merged-binary.bin
        └── manifest.json
```

この設計は**関心の分離**が適切で、各コンポーネントが独立してテスト可能。`matrix.yaml` を中心としたデータ駆動設計は量産パイプラインとして理想的。

### 7-2. ディレクトリ構造

```
Xiaozhi-Firmware-update/
├── docs/          # 計画・仕様（人間向け）
├── build/         # ビルド自動化（マシン向け）
├── tools/         # 既存ツール（レガシー、段階的廃止予定）
├── assets/        # 素材（ボード×ブランド別）
└── firmware/      # 成果物（.gitignored）
```

5層の分離が明確で、新メンバーのオンボーディングが容易。

---

## 8. 進捗状況の確認

| 項目 | 状態 | 備考 |
|---|---|---|
| リポジトリ作成 | ✅ 完了 | GitHub Private |
| 計画書 | ✅ 完了 | build-plan.md（972行） |
| ビルドマトリクス定義 | ✅ 完了 | matrix.yaml |
| ビルドスクリプト | ⬜ スケルトン | Phase 0-A 後に実装 |
| アセット注入スクリプト | ⬜ スケルトン | Phase 0-A 後に実装 |
| 検証スクリプト | ✅ ほぼ完了 | verify_build.py |
| OTA パッチツール | ✅ 動作可能 | tools/ 配下 |
| ロゴ素材 | ⬜ 未着手 | Phase 1-B で対応 |
| 音声素材 | ⬜ 未着手 | Phase 1-C で対応 |
| ESP-IDF 環境構築 | ⬜ 未着手 | Phase 0-B |
| 中国語版ビルド再現 | ⬜ 未着手 | Phase 0-C |

**現在地: Phase 0 開始前（計画・設計フェーズ完了）**

---

## 9. 次のアクション推奨

### 即座に対応（今日）
1. `patch_bin_2.py` のバグ修正（旧URL検証ロジック）
2. `requirements.txt` の作成

### Phase 0-A 着手時
3. 本家リポジトリの `main/assets/en-US/` 有無確認（STEP1 工数を左右）
4. `Kconfig.projbuild` の実キー名確認
5. `asset-spec.md` の未確定項目を埋める

### Phase 0-B 着手時
6. ESP-IDF v5.4.x のインストール
7. `check.py` / `check_bin.py` のCLI引数対応

---

## 10. 結論

本プロジェクトは**計画・設計フェーズとして非常に高い完成度**を持っている。特に `build-plan.md` の972行にわたる計画書は、2段階構成・リスク管理・QA基準・出荷フローまでカバーしており、商用ファームウェア量産プロジェクトの計画書として模範的。

スクリプトはスケルトン段階だが、アーキテクチャ設計（matrix.yaml 中心のデータ駆動・関心分離）は堅実で、Phase 0-A 完了後にスムーズに実装に移行できる構造になっている。

**最大のリスク**は本家の `en-US` アセットの有無であり、Phase 0-A での確認が最優先。

---

*本レビューは 2026-04-18 時点のリポジトリ状態に基づく。*
