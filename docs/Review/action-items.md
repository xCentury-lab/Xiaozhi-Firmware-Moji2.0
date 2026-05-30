# アクションアイテム一覧

> **作成日**: 2026-04-18
> **最終更新**: 2026-04-18（実機セットアップで判明した追加事項を反映）
> **レビューに基づくアクションアイテムの優先度別一覧**

---

## 2026-04-18 実機セットアップで判明した追加事項

| # | アクション | 対象 | 理由 | 状態 |
|---|---|---|---|---|
| D-1 | ESP-IDF **v5.5.2+ 必須**へ全ドキュメント・スクリプト修正 | `setup-ubuntu.sh` / `SETUP*.md` / `README.md` / `build/matrix.yaml` 等 | xiaozhi-esp32 v2.2.4 の `main/idf_component.yml` が `idf >=5.5.2` を要求、v5.4.x ではビルド不可 | ✅ 済 |
| D-2 | `en-US` / `ja-JP` アセットは本家 v2.2.4 に既存 → 計画書 § 5-1 の最優先確認項目を完了マーク | `docs/build-plan.md` § 5-1 | `main/assets/locales/` に 39 ロケール同梱、各 `language.json` 58行で完全翻訳済み | 🔄 要確認（build-plan.md 編集は未実施） |
| D-3 | STEP 2 日本語化工数見直し（新規翻訳制作不要の可能性） | `docs/build-plan.md` § STEP2 / `docs/translation-source.md` | 本家翻訳が既存、OEM用途の文言レビュー判断のみ残る | 🟠 営業・サポート確認待ち |
| D-4 | `curl` を apt 必須リストに追加 | `docs/setup/linux.md` / `docs/build-plan.md` / `README.md` | `check-env.sh` の必須コマンドチェックに含まれる | ✅ 済 |
| D-5 | 新シェルでの `check-env.sh` 実行前に `get_idf` が必要なことを明記 | `docs/setup/linux.md` | 子シェルが IDF_PATH を継承しない場合の混乱を防ぐ | ✅ 済 |
| D-6 | 実機セットアップログを永続化 | `docs/Review/linux-environment-setup-log.md` 新規 | 次回以降の環境構築再現と工数見積りの基礎データ | ✅ 済 |
| D-7 | Waveshare 1.85C の V1.0/V2.0 リビジョン対応をマトリクスに追加 | `build/matrix.yaml` / `build/build_matrix.py` / 出荷フロー | 本家デフォルトは V2.0 だが、現物実機（xxc 所持）は V1.0。V2.0 構成を V1.0 に書込むと ES8311 assert → ブートループ（2026-04-18 実機で確認） | 🟠 未（設計検討中） |
| D-8 | 出荷前検査に実機リビジョン確認ステップを追加 | `shipping-workflow-en.md` / `shipping-workflow-ja.md`（未作成） | リビジョン混入による出荷不良を防ぐ。Waveshare 1.85C 以外のボードにも同様の問題がないか要調査 | 🟠 未 |
| D-9 | ファームウェア書込手順書を新規作成（量産ライン向け） | `docs/operations/flash-guide.md` | 非エンジニアでも書込作業ができる 10 ステップ手順、トラブルシューティング A〜D、SHA256 検証、作業記録テンプレ含む | ✅ 済 |
| D-10 | ドキュメントを `docs/` 配下に統合管理 | `docs/README.md`（新規）/ `docs/setup/` / `docs/operations/` | `SETUP.md` / `SETUP-linux.md` / `firmware/FLASH-GUIDE.md` を `docs/` 配下に移動、マスターインデックス作成、クロスリンク一斉修正 | ✅ 済 |
| D-11 | **日本語版ウェイクワードを Jarvis → Alexa に変更** | `build/matrix.yaml`（次回ビルド）/ `docs/operations/wake-word-selection.md`（新規ガイド）| 2026-04-18 実機検証で日本語話者による Jarvis 検出失敗確認（Hi,ESP は成功）。原因は ESP-SR モデルの学習データが英語ネイティブ TTS ベースのため。日本語版 OEM 推奨組合せは **`Hi,ESP + Alexa`** | 🟠 未（次回ビルド時に適用）|
| D-12 | 音声アセット実地調査結果をドキュメント化 | `docs/operations/audio-assets.md`（新規）/ `docs/asset-spec.md`（一部 Phase 0-A 確定マーク）| 音声ファイルの所在・用途・埋込方式（CMake EMBED_FILES）・Kconfig 制御・カスタム差替手順を一元整理。実機ビルドに含まれる 22 ファイル（common 5 + locales 17）の詳細、本家オリジナル音声の商用利用（OEM 配布）時の法務確認事項を明記 | ✅ 済 |

詳細は [linux-environment-setup-log.md](linux-environment-setup-log.md) および [../operations/wake-word-selection.md](../operations/wake-word-selection.md) / [../operations/audio-assets.md](../operations/audio-assets.md) 参照。

## 即時対応（Phase 0 前）

| # | アクション | 対象ファイル | 理由 |
|---|---|---|---|
| A-1 | `patch_bin_2.py` のバグ修正 | `tools/patch_bin_2.py:36` | 検証ロジックが旧URLと不整合 |
| A-2 | `requirements.txt` 作成 | 新規 | 依存関係の明示 |
| A-3 | `check.py` / `check_bin.py` のハードコーディング除去 | `tools/check.py`, `tools/check_bin.py` | CLIツールとして汎用化 |

## STEP1 中に対応

| # | アクション | 対象ファイル | 理由 |
|---|---|---|---|
| B-1 | `patch_bin.py` と `patch_bin_2.py` の統合 | `tools/` | コード重複解消 |
| B-2 | `sha256_of_file()` の共通化 | `build/utils.py` 新規 | 2箇所で重複 |
| B-3 | `build_matrix.py` の実装完了 | `build/build_matrix.py` | Phase 0-A 後 |
| B-4 | `inject_assets.py` の実装完了 | `build/inject_assets.py` | Phase 0-A 後 |
| B-5 | `asset-spec.md` の未確定項目埋め | `docs/asset-spec.md` | Phase 0-A で実地確認 |

## STEP2 以降で検討

| # | アクション | 対象ファイル | 理由 |
|---|---|---|---|
| C-1 | GitHub Actions CI 整備 | `.github/workflows/` 新規 | YAML lint + Python lint |
| C-2 | ユニットテスト追加 | `tests/` 新規 | verify_build.py, inspect_ota.py |
| C-3 | `push.ps1` のユーザー情報環境変数化 | `push.ps1` | チーム共有時 |
| C-4 | レガシーツールの `tools/legacy/` 移動 | `tools/` | STEP1 完了後 |

---

## 進捗トラッキング

- [ ] A-1: patch_bin_2.py バグ修正
- [ ] A-2: requirements.txt 作成
- [ ] A-3: check.py / check_bin.py 改修
- [ ] B-1: パッチツール統合
- [ ] B-2: 共通関数切出し
- [ ] B-3: build_matrix.py 実装
- [ ] B-4: inject_assets.py 実装
- [ ] B-5: asset-spec.md 更新
- [ ] C-1: CI 整備
- [ ] C-2: テスト追加
- [ ] C-3: push.ps1 改修
- [ ] C-4: レガシーツール移動

---

*各アクションの完了時にチェックを入れ、日付を追記すること。*
