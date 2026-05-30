# 音量設定ガイド（起動時デフォルトボリューム）

> **対象**: 本プロジェクトでビルドする全 Xiaozhi ファーム
> **目的**: 起動時デフォルト音量の仕組みを明文化し、今後の調整方針（OEM 納入先ごとの音量最適化等）を検討する際の参考資料とする
> **最終更新**: 2026-04-18
> **関連**: [customization-spec.md](../customization-spec.md)

---

## 📋 現状（2026-04-18 時点）

### デフォルト音量: **70%**（全ボード一律）

### 根拠

| 場所 | 値 | 実際に使われているか |
|---|---|---|
| [main/audio/audio_codec.h:54](../../../xiaozhi-work/xiaozhi-esp32/main/audio/audio_codec.h) | `int output_volume_ = 70;` | ✅ **実効値** |
| [main/boards/yunliao-s3/config.h:10](../../../xiaozhi-work/xiaozhi-esp32/main/boards/yunliao-s3/config.h) | `#define AUDIO_DEFAULT_OUTPUT_VOLUME 70` | ❌ **参照されていない** |
| [main/boards/kevin-sp-v3-dev/config.h:9](../../../xiaozhi-work/xiaozhi-esp32/main/boards/kevin-sp-v3-dev/config.h) | `#define AUDIO_DEFAULT_OUTPUT_VOLUME 90` | ❌ 同上（実効値は 70 のまま） |
| [main/boards/taiji-pi-s3/config.h:11](../../../xiaozhi-work/xiaozhi-esp32/main/boards/taiji-pi-s3/config.h) | `#define AUDIO_DEFAULT_OUTPUT_VOLUME 80` | ❌ 同上（実効値は 70 のまま） |

### 📌 本家 78/xiaozhi-esp32 v2.2.4 の設計上のバグっぽい挙動

ボード固有 `AUDIO_DEFAULT_OUTPUT_VOLUME` マクロは定義されているが、**コード内から一切参照されていない**。結果として全ボードが `audio_codec.h` のベースクラスデフォルト `70` を使用する。

- kevin-sp-v3-dev: 意図は 90 だが実効 70
- taiji-pi-s3: 意図は 80 だが実効 70
- yunliao-s3: 意図 70、実効 70（偶然一致）

### 起動時の音量決定フロー

[main/audio/audio_codec.cc:29-38](../../../xiaozhi-work/xiaozhi-esp32/main/audio/audio_codec.cc):

```cpp
void AudioCodec::Start() {
    Settings settings("audio", false);
    output_volume_ = settings.GetInt("output_volume", output_volume_);  // NVS から読取
    if (output_volume_ <= 0) {
        output_volume_ = 10;  // 0以下ならフォールバック
    }
}
```

1. NVS 名前空間 `"audio"` のキー `output_volume` を読取
2. 値がなければベースクラスのデフォルト **70** を使用
3. 値があればそれを使用（前回 `SetOutputVolume()` で保存された値）

### 実行時の音量変更方法

| 方法 | 実装場所 | 備考 |
|---|---|---|
| **MCP ツール**: `self.audio_speaker.set_volume` | 起動ログ `MCP: Add tool: self.audio_speaker.set_volume` | 0〜100 の整数で設定、NVS 永続化 |
| **音声コマンド経由** | LLM がサーバー側で上記 MCP ツールを呼出す | 「音量上げて」「音量を50にして」等の自然言語 |
| **物理ボタン** | ボードによる | yunliao-s3 には音量ボタンなし（`BOOT_BUTTON_PIN` のみ）、waveshare-1.85c 系も同様にタッチパネル経由のみ |

---

## 🎛 起動時デフォルトを 70% から変更する 3 つの方針

今後、OEM 納入先の利用環境（店舗展示 / 家庭用 / 展示会ブース等）に応じてデフォルト音量を最適化する際の選択肢。

### 方針 A: 軽量修正（全ボード一律変更）★最速

**内容**: [`main/audio/audio_codec.h:54`](../../../xiaozhi-work/xiaozhi-esp32/main/audio/audio_codec.h) の `int output_volume_ = 70;` を直接変更

```cpp
// Before
int output_volume_ = 70;

// After (例: 50% に変更)
int output_volume_ = 50;
```

#### メリット
- 1 行修正で済む
- ビルドシステムへの影響ゼロ
- [/xiaozhi-build スキル](../../.claude/skills/xiaozhi-build/) の正規表現パッチに組込みやすい

#### デメリット
- **全ボード一律**の変更になる。ボード別最適化不可
- upstream の共通ヘッダを改変するため、本家 v2.2.5+ 更新時にコンフリクト再発

#### 向いている状況
- 「とりあえず全製品のデフォルト音量を下げたい / 上げたい」という横断的要求
- OEM 納入先が単一で、全製品同じ設定で出荷する場合

---

### 方針 B: ボード別修正（config.h のマクロを正しく参照させる）★本来あるべき設計

**内容**: 各ボードの `config.h` に既存する `AUDIO_DEFAULT_OUTPUT_VOLUME` マクロを、実際にコードから読むよう修正。**upstream 側のパッチが必要**。

#### 実装例

1. [`main/audio/audio_codec.h:54`](../../../xiaozhi-work/xiaozhi-esp32/main/audio/audio_codec.h) でデフォルト値をマクロから取得:

   ```cpp
   #include "config.h"  // ボード固有 config

   #ifndef AUDIO_DEFAULT_OUTPUT_VOLUME
   #define AUDIO_DEFAULT_OUTPUT_VOLUME 70
   #endif

   class AudioCodec {
       // ...
       int output_volume_ = AUDIO_DEFAULT_OUTPUT_VOLUME;
   };
   ```

2. 各ボードの `config.h` に定義するだけで効く:
   ```c
   // main/boards/yunliao-s3/config.h
   #define AUDIO_DEFAULT_OUTPUT_VOLUME 50   // 店舗展示用は控えめに
   ```

3. 変更後、本プロジェクトの [patches/](../../patches/) に `xiaozhi-esp32-v2.2.4-default-volume-per-board.patch` として保存

#### メリット
- **ボードごとに最適化可能**（展示会用ボードは 90、家庭用は 50 等）
- 既存の未使用マクロを正しく機能させるので、本家設計の意図に沿う
- 将来の upstream マージで本家側が修正する可能性も高い（その時はパッチ不要化）

#### デメリット
- upstream ヘッダ（`main/audio/audio_codec.h`）の改変が必要
- パッチファイルメンテナンスが必要（upstream バージョンアップごとに再適用確認）
- [/xiaozhi-build スキル](../../.claude/skills/xiaozhi-build/) の `ensure_*_patch()` に新しい正規表現追加が必要

#### 向いている状況
- 複数 OEM / 複数用途で**ボードごとに異なる音量**が要求される場合
- 「和合」ロゴと同じくパッチファイル管理体制に組込みたい場合

---

### 方針 C: ユーザー設定経由（NVS 書込み）★ファーム変更不要

**内容**: 初回起動時や出荷前キッティング時に MCP ツール `self.audio_speaker.set_volume` を呼出して NVS に目標値を保存

#### 実装例

##### C-1: 出荷時キッティング（手動）
1. デバイスを初期化状態でフラッシュ
2. 起動後、シリアル経由 or WebSocket 経由で MCP コール:
   ```json
   {"type":"mcp","payload":{"jsonrpc":"2.0","method":"tools/call",
    "params":{"name":"self.audio_speaker.set_volume","arguments":{"volume":50}},
    "id":1}}
   ```
3. NVS に `audio/output_volume=50` が永続化される
4. 次回起動時からこの値が使われる

##### C-2: サーバー側自動化
- WebSocket `hello` 完了直後にサーバー側で MCP コール送信
- 全端末で一律に初期音量を強制セット
- classism.net 側の実装拡張で対応可能

#### メリット
- **ファーム再ビルド不要**。既存ファームにそのまま適用可能
- 個別端末ごとに微調整可能（シリアル番号別に音量差別化等）
- 出荷後も遠隔で変更可能（サーバー経由 MCP）

#### デメリット
- 工場キッティング工程に「MCP コール」工程を追加する必要がある（C-1）
- サーバー側の自動化実装が必要（C-2）
- NVS を消去（出荷時リセット）すると 70% に戻る

#### 向いている状況
- 既に出荷済みの端末に対する事後調整
- 同一ファームで複数顧客（異なる音量要望）に対応する場合
- A/B テストで音量を動的に切替えたい場合

---

## 📊 3 方針の比較表

| 観点 | A: 軽量修正 | B: ボード別修正 | C: ユーザー設定 |
|---|---|---|---|
| 実装工数 | ★☆☆ 1 行 | ★★☆ ヘッダ + パッチ | ★★★ サーバー or 工程追加 |
| ボード別制御 | ❌ | ✅ | ✅（端末別も可） |
| ファーム再ビルド | 必要 | 必要 | 不要 |
| 出荷後の変更 | 不可（再ファーム必要） | 不可（再ファーム必要） | 可 |
| upstream 追従性 | 低（毎回当て直し） | 中 | 高（非改変） |
| パッチ管理の必要 | スキル正規表現のみ | [patches/](../../patches/) に追加 | 不要 |
| NVS 消去時の挙動 | 修正後の値に戻る | 修正後の値に戻る | 70%（ベースデフォルト）に戻る |

---

## 🎯 推奨決定ツリー

```
Q1: 全ボード一律に変更したい？
    YES → 方針 A（軽量修正）
    NO  → Q2

Q2: 出荷後の変更や個別調整も必要？
    YES → 方針 C（ユーザー設定）
    NO  → 方針 B（ボード別修正）

Q3: OEM 納入先が複数で、ボード別の静的な値で十分？
    YES → 方針 B
    NO  → 方針 C（納入先別サーバーで動的制御）
```

---

## 🔬 ボード別の音量特性（推奨値の参考）

音量の「主観的な大きさ」はスピーカー・筐体・用途で大きく変わります。以下は参考値（実機計測は別途必要）:

| ボード | スピーカー | 用途想定 | 推奨デフォルト |
|---|---|---|---|
| waveshare-esp32-s3-touch-lcd-1.85c | 内蔵小型 | デモ・卓上 | 60〜70% |
| yunliao-s3 | 2000mAh 電池付き小型 | ポータブル・家庭内 | 50〜60% |
| waveshare-p4-* 大型 | 外付けまたは大型内蔵 | 展示会・店頭 | 70〜90% |

**夜間・静音環境**: 40〜50%、**騒音環境**: 80〜90%。

---

## 💾 NVS を保持したままファーム更新する方法

### 背景: なぜ NVS が消えるのか

ユーザーが `self.audio_speaker.set_volume(N)` で変更した音量は **NVS パーティション（0x9000〜0xd000、16KB）** に永続化される。通常の電源 OFF/ON やリセットボタンでは保持されるが、**ファーム再書込み時に消える場合がある**。

#### パーティション配置（[partitions/v2/16m.csv](../../../xiaozhi-work/xiaozhi-esp32/partitions/v2/16m.csv)）

| 領域 | オフセット | サイズ | 内容 |
|---|---|---|---|
| bootloader | 0x0 | 〜0x8000 | ブートローダ |
| partition-table | 0x8000 | 0x1000 | パーティションテーブル |
| **nvs** | **0x9000** | **0x4000 (16KB)** | **ユーザー設定（audio/output_volume 等）** |
| otadata | 0xd000 | 0x2000 | OTA 状態フラグ |
| phy_init | 0xf000 | 0x1000 | Wi-Fi キャリブレーション |
| ota_0 (app) | 0x20000 | 0x3f0000 | アプリ本体 |
| ota_1 (app) | 0x410000 | 0x3f0000 | OTA 予備 |
| assets (spiffs) | 0x800000 | 8MB | 音声/画像/フォント |

#### 現行の `merged-binary.bin` は NVS を上書きする ⚠️

```bash
# 本プロジェクトで生成される merged-binary.bin のマージ引数:
python -m esptool --chip esp32s3 merge_bin \
    -o merged-binary.bin \
    0x0      bootloader.bin \          # 0x0 - ~0x4000
    0x8000   partition-table.bin \     # 0x8000 - 0x9000
    0xd000   ota_data_initial.bin \    # 0xd000 - ~0xf000
    0x20000  xiaozhi.bin \
    0x800000 generated_assets.bin
```

`merge_bin` は指定オフセット間の隙間を **0xFF で埋める**ため、出力ファイルは 0x0 から 10MB 連続する。NVS 領域（0x9000〜0xd000）も 0xFF で埋められる。
これを `write_flash 0x0 merged-binary.bin` で書込むと、**NVS が 0xFF（空）で上書きされユーザー設定がリセットされる**。

---

### 更新方法別の NVS 挙動

| 操作 | コマンド例 | NVS |
|---|---|---|
| 通常の電源 OFF/ON / リセットボタン | — | **維持** ✅ |
| OTA 更新（サーバー配信、app のみ差替え） | サーバー発信 | **維持** ✅ |
| app パーティションのみ書込み | `esptool write_flash 0x20000 xiaozhi.bin` | **維持** ✅ |
| 個別パーティション列挙（NVS は除外） | `write_flash 0x0 bootloader.bin 0x8000 partition-table.bin 0xd000 ota_data_initial.bin 0x20000 xiaozhi.bin 0x800000 generated_assets.bin` | **維持** ✅ |
| `merged-binary.bin` で一括書込み ⚠️ | `write_flash 0x0 merged-binary.bin` | **消去** ❌（70% に戻る） |
| 全 flash 消去 | `esptool erase_flash` | **消去** ❌ |

---

### 🛠 NVS 保持でファーム更新する具体的手順

#### 方法 α: アプリのみ書込み（最速・最軽量）

軽微な修正（UI テキスト変更等）でアプリのみ差替えたい場合:

```bash
cd firmware/v2.2.4_yunliao-s3_V1.0_ja-JP_alexa-hiesp_company
esptool.py --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before default_reset --after hard_reset write_flash \
    0x20000 xiaozhi.bin
```

- 書込み時間: 約 15 秒（4MB）
- NVS: **維持** ✅
- assets 変更時は別途 `0x800000 generated_assets.bin` も追加

#### 方法 β: 個別パーティション列挙（NVS をスキップ）

本家 `idf.py flash` と同等の挙動。bootloader 等も含めてフル更新しつつ NVS だけ保持:

```bash
cd firmware/v2.2.4_yunliao-s3_V1.0_ja-JP_alexa-hiesp_company
esptool.py --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before default_reset --after hard_reset write_flash \
    0x0      bootloader.bin \
    0x8000   partition-table.bin \
    0xd000   ota_data_initial.bin \
    0x20000  xiaozhi.bin \
    0x800000 generated_assets.bin
```

- 書込み時間: 約 60 秒（フル更新）
- NVS: **維持** ✅（0x9000〜0xd000 を飛ばす）
- `flash_args` ファイルの内容を直接 `write_flash @flash_args` で指定しても同じ

#### 方法 γ: OTA（Over-The-Air）更新

量産フィールド運用の本命。サーバー `classism.net/xiaozhi/ota/` から app のみ配信:

```
デバイス → OTA チェック → 新バージョン検知 → xiaozhi.bin ダウンロード
    → ota_0/ota_1 の未使用側に書込み → otadata 更新 → 再起動 → 新版起動
```

- NVS: **維持** ✅（触らない）
- bootloader / partition-table / assets は更新されない（制限）
- 量産出荷後のフィールドアップデートで**ユーザー設定を失わない**

---

### 量産ラインでの運用指針

| シーン | 推奨手法 | NVS |
|---|---|---|
| 工場出荷時の初期ファーム書込み | `merged-binary.bin` 一括書込み（現行スキル） | リセット（70%） |
| 検品工程での個別設定書込み | MCP `set_volume(N)` 呼出 or [NVS 事前生成方式](#量産工程への展開要検討) | ユーザー設定反映 |
| 修理・再生品のフル更新 | 方法 β（個別パーティション列挙） | **維持** |
| フィールド OTA 更新 | 方法 γ | **維持** |
| 開発者のデバッグ再書込み（設定保持したい） | 方法 α or β | **維持** |
| 全リセット（デバッグ用） | `erase_flash` + `merged-binary.bin` | リセット |

---

### 量産工程への展開（要検討）

工場出荷時に「デフォルト 70% ではなく、納入先別の値（例: 50%）」を NVS に焼付けたい場合、本ファイル冒頭 § 3 方針 C（ユーザー設定）の派生として、以下が選択肢:

#### 方式 1: NVS 事前生成 + 同時書込み（推奨）
```bash
# 1. 音量 50 を含む NVS バイナリ生成
cat > volume_50.csv <<EOF
key,type,encoding,value
audio,namespace,,
output_volume,data,i32,50
EOF
python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py \
    generate volume_50.csv nvs_volume_50.bin 0x4000

# 2. merged-binary.bin 生成時に NVS も同梱
python -m esptool merge_bin --chip esp32s3 --flash_size 16MB \
    -o merged_with_nvs.bin \
    0x0      bootloader.bin \
    0x8000   partition-table.bin \
    0x9000   nvs_volume_50.bin \       ← NVS を追加
    0xd000   ota_data_initial.bin \
    0x20000  xiaozhi.bin \
    0x800000 generated_assets.bin

# 3. 通常フラッシュ
esptool write_flash 0x0 merged_with_nvs.bin
```

- **Wi-Fi/サーバー不要**、完全オフライン工場に対応
- `/xiaozhi-build` スキルに `--volume <N>` オプション追加で自動化可能

#### 方式 2: サーバー経由 MCP キッティング ★本プロジェクトで採用方針
- 工場 Wi-Fi → classism.net `hello` 直後にサーバーが MCP `set_volume(N)` を自動送信
- 端末別（Device-Id 別）に異なる値配布可能
- 出荷後の遠隔調整・監査ログ記録も同じ仕組みで実現
- サーバー側の実装要件は **[../server/factory-kitting-mcp-spec.md](../server/factory-kitting-mcp-spec.md)** に詳述

→ 採用決定済（2026-04-18）。サーバーエンハンス実装後に本番投入。

---

## ⚠️ 音量変更時の注意事項

### 1. ES8388 / ES8311 等のハードウェア上限

各コーデックチップは内部で音量→ゲイン変換テーブルを持っており、**80% 以上では歪みが発生する個体差**があります。実機試聴での品質確認が必須。

### 2. 初回起動と工場出荷リセットの挙動

- **初回起動**: NVS 空 → ベースクラスのデフォルト（70%）
- **ユーザー音量変更後**: NVS 保存 → 以降はその値
- **NVS 消去（工場リセット）**: 再度 70% に戻る

方針 C を採用する場合、「工場リセット後の自動再キッティング」のフローも合わせて設計すること。

### 3. 関連メッセージ

- 音量変更時 MCP ツールは `ESP_LOGI(TAG, "Set output volume to %d", ...)` をシリアル出力
- デバイス画面上にも `Lang::Strings::VOLUME` + 数値で通知表示される（[sensecap_watcher 等で実装例](../../../xiaozhi-work/xiaozhi-esp32/main/boards/sensecap-watcher/sensecap_watcher.cc)）

---

## 🔗 関連ドキュメント

- [customization-spec.md](../customization-spec.md) — カスタマイズ要件定義
- [logo-redesign-guide.md](logo-redesign-guide.md) — ロゴ再設計ガイド
- [wake-word-selection.md](wake-word-selection.md) — ウェイクワード選定
- **[../server/factory-kitting-mcp-spec.md](../server/factory-kitting-mcp-spec.md)** — サーバー側エンハンス要件（方式 2 採用）
- [/.claude/skills/xiaozhi-build/](../../.claude/skills/xiaozhi-build/) — ビルドスキル
- [patches/](../../patches/) — 本家ソース改変パッチ

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版。デフォルト音量 70% の根拠と変更 3 方針（A/B/C）を整理 | xxc@ctoch.jp |
| 2026-04-18 | 1.1 | 「NVS 保持でファーム更新する方法」セクション追記。`merged-binary.bin` が NVS を上書きする挙動、更新方法別の NVS 挙動マトリクス、量産ライン運用指針、NVS 事前生成によるキッティング方式を整理 | xxc@ctoch.jp |
| 2026-04-18 | 1.2 | 方式 2（サーバー経由 MCP キッティング）を本プロジェクトで採用決定。詳細要件は別紙 [server/factory-kitting-mcp-spec.md](../server/factory-kitting-mcp-spec.md) に分離 | xxc@ctoch.jp |
