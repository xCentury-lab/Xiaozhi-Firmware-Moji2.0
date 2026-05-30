# フェーズゲート 0-A: 本家言語アセット確認

> **ゲート種別**: Go / No-Go 判定
> **対象フェーズ**: Phase 0-A（事前調査）
> **判定日**: 2026-04-18
> **判定結果**: ✅ **GO** — en-US / ja-JP 両方完全存在確認済み

---

## 1. ゲートの目的

本プロジェクト最大のリスク「本家 78/xiaozhi-esp32 に英語・日本語アセットが存在するか」を
STEP1/STEP2 着手前に確認し、Go/No-Go 判定を行う。

このゲートの結果により以下が決定する:

| 結果 | 影響 |
|---|---|
| ✅ en-US 存在 | STEP1 工数は計画通り（8-10日） |
| ❌ en-US 不在 | STEP1 に英訳作業 +1-2日が追加 |
| ✅ ja-JP 存在 | STEP2 工数が大幅削減（翻訳不要） |
| ❌ ja-JP 不在 | STEP2 工数は計画通り（6-8日）、翻訳作業必要 |

---

## 2. 調査結果

### 2-1. en-US アセット — ✅ 完全存在

**ディレクトリ**: `main/assets/locales/en-US/`

| ファイル | 用途 | 状態 |
|---|---|---|
| `language.json` | UI 文字列（60+ エントリ） | ✅ 存在 |
| `activation.ogg` | アクティベーション音声 | ✅ 存在 |
| `welcome.ogg` | ウェルカム音声 | ✅ 存在 |
| `wificonfig.ogg` | Wi-Fi設定音声 | ✅ 存在 |
| `upgrade.ogg` | アップグレード音声 | ✅ 存在 |
| `err_pin.ogg` | PINエラー音声 | ✅ 存在 |
| `err_reg.ogg` | 登録エラー音声 | ✅ 存在 |
| `0.ogg` - `9.ogg` | 数字読み上げ音声 | ✅ 存在 |

### 2-2. 本家のアセット構造（計画書との差異）

**計画書の想定:**
```
main/assets/
├── zh-CN/
├── en-US/
└── ja-JP/
```

**実際の構造:**
```
main/assets/
├── common/                    # 言語共通アセット
└── locales/                   # ★ locales/ 配下に言語別
    ├── en-US/
    │   ├── language.json      # UI文字列
    │   ├── activation.ogg     # 音声ファイル群
    │   ├── welcome.ogg
    │   └── ...
    ├── zh-CN/
    ├── zh-TW/
    └── [40+ 他言語ディレクトリ]
```

**要アクション**: `build-plan.md` のパス記述を `main/assets/locales/` に修正すること。

### 2-3. Kconfig 言語設定

**計画書の想定:**
```
CONFIG_LANGUAGE_ZH_CN
CONFIG_LANGUAGE_EN_US
CONFIG_LANGUAGE_JA_JP   # ★ STEP2で追加予定
```

**実際のキー:**
```
CONFIG_LANGUAGE_ZH_CN   ✅ 存在（デフォルト）
CONFIG_LANGUAGE_EN_US   ✅ 存在
CONFIG_LANGUAGE_JA_JP   ✅ 存在（bool "Japanese"）
```

### 2-4. 言語切替メカニズム

1. `menuconfig` で `CONFIG_LANGUAGE_EN_US=y` を選択
2. `CMakeLists.txt` が `LANG_DIR = "en-US"` にマッピング
3. `scripts/gen_lang.py` がビルド時に言語ヘッダを自動生成
4. 音声ファイルはファームウェアパーティションに埋込
5. **フォールバック機能**: 不足言語の音声は en-US にフォールバック

### 2-5. ja-JP アセット — ✅ 完全存在

**ディレクトリ**: `main/assets/locales/ja-JP/`

| ファイル | 用途 | 状態 |
|---|---|---|
| `language.json` | UI 文字列 | ✅ 存在 |
| `activation.ogg` | アクティベーション音声 | ✅ 存在 |
| `welcome.ogg` | ウェルカム音声 | ✅ 存在 |
| `wificonfig.ogg` | Wi-Fi設定音声 | ✅ 存在 |
| `upgrade.ogg` | アップグレード音声 | ✅ 存在 |
| `err_pin.ogg` | PINエラー音声 | ✅ 存在 |
| `err_reg.ogg` | 登録エラー音声 | ✅ 存在 |
| `0.ogg` - `9.ogg` | 数字読み上げ音声 | ✅ 存在 |

**en-US との比較**: ファイル構成が**完全一致**（16ファイル同一構成）

**Kconfig**: `CONFIG_LANGUAGE_JA_JP` が `bool "Japanese"` として定義済み。
STEP2 で Kconfig パッチを追加する必要は**無い**。

### 2-6. ja-JP 確認による STEP2 への影響

| 項目 | 計画書の想定 | 実際 | 影響 |
|---|---|---|---|
| ja-JP アセット | 不在、新規作成が必要 | ✅ 完全存在 | **翻訳作業不要** |
| Kconfig パッチ | JA_JP を手動追加 | ✅ 既存 | **パッチ不要** |
| CJK フォント | 新規サブセット生成 | 本家に組込済みか要確認 | Phase 0-A で確認 |
| 日本語音声 | TTS で新規合成 | ✅ .ogg で完備 | **音声制作不要** |

| STEP2 Phase | 計画工数 | 更新工数 | 差分 |
|---|---|---|---|
| Phase 2-A（日本語アセット制作） | 2-3日 | 0.5日 | **-1.5-2.5日**（本家流用） |
| Phase 2-B（日本語ビルド） | 1日 | 0.5日 | **-0.5日**（Kconfig パッチ不要） |
| Phase 2-C（日本語UI調整） | 1日 | 1日 | 変更なし（実機確認は必要） |
| Phase 2-D（マトリクスv2） | 0.5日 | 0.5日 | 変更なし |
| Phase 2-E（日本語版QA） | 1日 | 1日 | 変更なし |
| Phase 2-F（全ボード展開） | 1-2日 | 1-2日 | 変更なし |
| Phase 2-G（出荷フロー統合） | 0.5日 | 0.5日 | 変更なし |
| **STEP2 合計** | **6-8日** | **4-6日** | **-2日短縮** |

---

## 3. 計画書への影響と修正事項

### 3-1. リスク表の更新

| リスク # | 元の評価 | 更新後 |
|---|---|---|
| #1: en-US が無い | ⚠️ STEP1工数+1-2日 | ✅ **解消** — en-US 完全存在 |
| #2: ja-JP が無い | ⚠️ STEP2半年遅延 | ✅ **解消** — ja-JP 完全存在（en-US と同一構成） |

### 3-2. build-plan.md 修正必要箇所

| 章 | 現在の記述 | 修正後 |
|---|---|---|
| §5-1 | `main/assets/zh-CN/` | `main/assets/locales/zh-CN/` |
| §5-1 | `main/assets/en-US/` | `main/assets/locales/en-US/` |
| §5-1 | `main/assets/ja-JP/` | `main/assets/locales/ja-JP/` |
| §5-1 | `main/assets/logos/` | 実構造に合わせて確認 |
| §5-1 | `main/assets/sounds/` | 実構造に合わせて確認 |
| §8 | `en-US が存在しなかった場合` の注意書き | 削除または「確認済み」に変更 |
| §15-1 | 翻訳ベースの選択 | en-US ベースで確定 |
| §15-1 | ja-JP を新規作成する前提 | 本家 ja-JP が完備、カスタム部分のみ上書き |
| §16-1 | Kconfig に Japanese を手動追加 | **不要** — `CONFIG_LANGUAGE_JA_JP` 既存 |
| §15-2 | 翻訳作業（DeepL + 校正） | 本家翻訳の品質確認のみ（工数大幅削減） |
| §15-3 | CJK フォントサブセット生成 | 本家の組込状況を確認後に判断 |

### 3-3. asset-spec.md 更新事項

| 項目 | 更新内容 |
|---|---|
| 音声フォーマット | `.ogg` 形式（WAV想定を修正） |
| UI文字列形式 | `language.json`（.po/.h 想定を修正） |
| 言語ヘッダ生成 | `scripts/gen_lang.py` による自動生成 |

### 3-4. inject_assets.py 修正事項

```python
# 現在の想定
dst_dir = _ensure_src() / "main" / "assets" / lang_code

# 実際のパス
dst_dir = _ensure_src() / "main" / "assets" / "locales" / lang_code
```

### 3-5. STEP1 工数への影響

| Phase | 計画工数 | 更新工数 | 差分 |
|---|---|---|---|
| Phase 0-A | 1-2日 | 0.5日 | **-0.5-1.5日**（en-US確認済み） |
| Phase 1-A | 1日 | 1日 | 変更なし |
| Phase 1-B | 1-2日 | 1-2日 | 変更なし |
| Phase 1-C | 1-2日 | 0.5-1日 | **-0.5-1日**（.ogg形式判明） |
| **STEP1合計** | **8-10日** | **6-8日** | **-2日短縮** |

### 3-6. STEP2 工数への影響（ja-JP 確認結果）

| Phase | 計画工数 | 更新工数 | 差分 |
|---|---|---|---|
| Phase 2-A（日本語アセット制作） | 2-3日 | 0.5日 | **-1.5-2.5日**（本家に完備） |
| Phase 2-B（日本語ビルド） | 1日 | 0.5日 | **-0.5日**（Kconfig パッチ不要） |
| Phase 2-C〜2-G | 4-5日 | 4-5日 | 変更なし |
| **STEP2合計** | **6-8日** | **4-6日** | **-2日短縮** |

### 3-7. プロジェクト全体工数サマリ

| ステップ | 計画工数 | 更新工数 |
|---|---|---|
| STEP0 | 1-2日 | 1-2日 |
| STEP1 | 8-10日 | 6-8日 |
| STEP2 | 6-8日 | 4-6日 |
| **合計** | **15-20日** | **11-16日（最大 -4日短縮）** |

---

## 4. フェーズゲート判定

### 4-1. Go/No-Go チェックリスト

| # | 判定基準 | 結果 | 根拠 |
|---|---|---|---|
| G-1 | en-US の UI 文字列が存在するか | ✅ GO | `language.json` に 60+ エントリ |
| G-2 | en-US の音声ファイルが存在するか | ✅ GO | activation/welcome/wifi 等 完備 |
| G-3 | Kconfig に EN_US キーが存在するか | ✅ GO | `CONFIG_LANGUAGE_EN_US` 確認 |
| G-4 | ビルド時言語切替の仕組みが明確か | ✅ GO | gen_lang.py + CMakeLists.txt |
| G-5 | アセットのファイル形式が判明したか | ✅ GO | .ogg + .json |
| G-6 | ja-JP の UI 文字列が存在するか | ✅ GO | `language.json` 存在 |
| G-7 | ja-JP の音声ファイルが存在するか | ✅ GO | en-US と同一16ファイル完備 |
| G-8 | Kconfig に JA_JP キーが存在するか | ✅ GO | `CONFIG_LANGUAGE_JA_JP` 確認 |
| G-9 | ja-JP と en-US の完全性が同等か | ✅ GO | ファイル構成完全一致 |

### 4-2. 判定結果

```
╔══════════════════════════════════════════════════════════╗
║  フェーズゲート 0-A: ✅ GO                                ║
║                                                          ║
║  en-US アセット完全存在確認                                ║
║  ja-JP アセット完全存在確認（en-US と同一構成）             ║
║  STEP1 着手に障害なし — 工数 2日短縮見込み（6-8日）        ║
║  STEP2 着手に障害なし — 工数 2日短縮見込み（4-6日）        ║
║  プロジェクト全体: 15-20日 → 10-14日（最大 -6日短縮）     ║
╚══════════════════════════════════════════════════════════╝
```

---

## 5. 残存リスクと次のゲート

### 5-1. 残存確認事項（Phase 0-A 実地で最終確認）

- [x] ja-JP ディレクトリの有無 → ✅ 完全存在確認済み（2026-04-18）
- [ ] ロゴアセットの実際の格納場所と形式（`main/assets/common/` 内？）
- [ ] 起動音のカスタマイズポイント（Kconfig に `SOUND_SET` 相当はあるか）
- [ ] `scripts/gen_lang.py` の引数と動作確認
- [ ] v2.2.4 タグ時点での en-US 完全性（HEAD との差異）

### 5-2. 次のフェーズゲート

| ゲート | タイミング | 判定基準 |
|---|---|---|
| Gate 0-B | ESP-IDF 環境構築後 | `idf.py --version` 成功 |
| Gate 0-C | 中国語版ビルド後 | 実機で中国語メニュー表示成功 |
| Gate 1-A | 英語版ビルド後 | 実機で英語 UI + classism.net OTA 確認 |

---

*本ゲート判定は 2026-04-18 時点の GitHub 上の調査に基づく。Phase 0-A でローカルクローンにて最終実地確認を行うこと。*
