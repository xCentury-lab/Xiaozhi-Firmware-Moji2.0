# Xiaozhi-Firmware-Moji2.0 — プロジェクト概要

> **Movecall Moji 2.0 (ESP32-C5) 商品化のための xCentury 自家ビルドプロジェクト**
> 本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) v2.2.6 を 5 軸 + emoji でカスタマイズし、assets.bin パスベースの新フローで量産する。

---

## 🎯 何を解決するか

| 課題 | 解決策 |
|---|---|
| 本家 firmware は中国語版・本家 OTA サーバ前提 | 5 軸 + emoji で日本市場向けに再構築 |
| メーカー出荷品は emoji が標準 Twemoji | xCentury 黒猫 cat_master_2k v2 21 感情に置換 |
| 旧来は emoji を C 配列で固定 | **assets.bin パスベース** で Web UI から差替可能 |
| ESP-VoCat は ESP32-S3、Moji2.0 は ESP32-C5 | チップ別 doc + skill 分離 |

### 5 軸 + emoji カスタマイズ要件

1. **UI 言語** — ja-JP (Kconfig 切替)
2. **OTA サーバ URL** — `classism.net` ビルド時組込
3. **ja-JP 音声マスタ** (発音修正、ja-JP 限定) ⚠️ — `assets/sounds/locales/ja-JP/` を **★ ビルド前 rsync で本家 `main/assets/locales/ja-JP/` に必ず上書き** (xiaozhi.bin embed なので OTA 部分差替不可、Step 3.5 で sha256 guard 必須)
4. **ウェイクワード** — **assets.bin 内蔵 WakeNet9s シリーズモデル** (Alexa / Hi,ESP / ひかりん / ねこちゃん等、ESP-C5 専用の `wn9s_*` 形式)
5. **emoji コレクション** ★ — **assets.bin 内蔵** xCentury 黒猫 21 感情 (cat_master_2k v2、Web UI 生成済)

> **ESP-C5 / Moji2.0 assets.bin 一元化原則**:
>
> ESP-C5 では **emoji + wake word + フォントの 3 種類はすべて assets.bin に同梱**される (sdkconfig での個別 enable / C 配列方式は不要)。
>
> - **Wake word**: ESP-C5 は **WakeNet9s シリーズのみ**サポート (フル WakeNet9 は S3/P4 用)。`wn9s_*` 形式のモデルが assets.bin 内に格納。
> - **Emoji**: cat_master_2k v2 (21 感情、256×256 RGBA、xCentury 黒猫) が assets.bin にコンパイル済 → C 配列方式 (`emoji_to_lvgl_c.py`) / `lcd_display.cc` patch は **不要**。
> - **フォント**: 阿里巴巴普惠体等の subset が assets.bin 同梱。
>
> Firmware 側は assets.bin への依存度が非常に高い → 量産時の SHA256 検証は必須、出荷後の差替も assets partition (0x800000) の書込だけで完結する。

---

## 📍 現在の状態 (2026-05-29)

| 項目 | 値 |
|---|---|
| 商品化対象 | **movecall-moji2-esp32c5** 1 SKU |
| Firmware version | v2.2.6 (本家 commit `78/xiaozhi-esp32 v2.2.6`) |
| Target chip | **ESP32-C5** (RISC-V、Wi-Fi 6) |
| 言語 | ja-JP |
| Wake words | **assets.bin 内蔵 WakeNet9s モデル** (Alexa / Hi,ESP / ひかりん / ねこちゃん、全て `wn9s_*`) |
| OTA URL | `https://classism.net/xiaozhi/ota/` |
| Brand | company (xCentury) |
| Emoji pack | xCentury 黒猫 cat_master_2k v2 (21 感情、透明背景、256×256→assets.bin) |
| Assets.bin 状態 | ✅ **配置済** (`firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin`) |
| ビルド状態 | ⏳ 未実施 (初回ビルド待機) |
| 進行中の課題 | 初回 merge_bin + 動作確認 |

---

## 📁 リポジトリ構造

```
Xiaozhi-Firmware-Moji2.0/
├── README.md                                ★ 詳細仕様
├── docs/                                    ★ ドキュメント集約
│   ├── PROJECT_OVERVIEW.md                  ← 本ファイル
│   ├── README.md                            ← ドキュメントインデックス
│   ├── build-plan.md                        ← メイン計画書
│   ├── customization-spec.md
│   ├── operations/                          ← 運用手順
│   │   ├── firmware-build-v2.2.6-esp32c5.md ⭐ ★ ビルド完全手順
│   │   ├── audio-assets.md
│   │   ├── flash-guide.md
│   │   ├── wsl-usb-device-setup.md
│   │   └── ...
│   ├── plans/                               ← Phase 別実行プラン
│   ├── setup/                               ← OS 別環境構築
│   └── Review/                              ← Phase 0 事前調査
├── build/                                   量産ビルドパイプライン
├── tools/                                   OTA URL 後加工パッチツール
├── assets/                                  音声マスタ
│   └── sounds/locales/ja-JP/                ← 日本語音声 (継承)
├── firmware/                                ビルド成果物
│   └── v2.2.6_movecall-moji2-esp32c5/       ⭐ 商品化ターゲット
│       └── assets.bin                       ★ 配置済 (xiaozhi-assets-generator 生成)
├── scripts/                                 ワンショット環境構築
├── patches/                                 本家へ当てるパッチ
└── .claude/skills/                          ビルド・OTA 書換 skill
```

---

## 📚 次に読むべきドキュメント

| 役割 | 読むべき doc |
|---|---|
| **概要把握** | 本ファイル → [`docs/README.md`](README.md) |
| **開発者 (初回)** | [`docs/setup/linux.md`](setup/linux.md) / [`windows.md`](setup/windows.md) |
| **★ Moji2.0 ビルド担当** | [`docs/operations/firmware-build-v2.2.6-esp32c5.md`](operations/firmware-build-v2.2.6-esp32c5.md) |
| **量産ライン書込担当** | [`docs/operations/flash-guide.md`](operations/flash-guide.md) + [`wsl-usb-device-setup.md`](operations/wsl-usb-device-setup.md) |
| **計画/マイルストーン** | [`docs/build-plan.md`](build-plan.md) |
| **assets.bin 生成 (Web UI)** | 別プロジェクト `xiaozhi-assets-generator/docs/11-emoji-pack-generation.md` |

---

## 🔧 標準ビルドフロー (簡略版)

```bash
# 1. 本家 source clean checkout
cd ~/xiaozhi-work/xiaozhi-esp32
git worktree add ../xiaozhi-esp32-moji2-rebuild v2.2.6

# 2. ESP-IDF v5.5+
source $HOME/esp/esp-idf-5.5.2/export.sh

# 3. ターゲット切替 (★ ESP32-C5 専用)
cd ../xiaozhi-esp32-moji2-rebuild
idf.py fullclean
idf.py set-target esp32c5

# 3.5. ★ ja-JP 音声マスタ置換 (★ ビルド前 必須)
#      本家 ja-JP 音声 (発音誤りあり) を xCentury 整備済 master で必ず上書き。
#      xiaozhi.bin に embed されるため、ビルド後 OTA 部分差替不可。
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
SRC_LOCALE=~/xiaozhi-work/xiaozhi-esp32/main/assets/locales/ja-JP
[ -d "${SRC_LOCALE}.orig" ] || cp -r "$SRC_LOCALE" "${SRC_LOCALE}.orig"
rsync -av --include='*.ogg' --include='language.json' --exclude='*' \
  "$PROJ/assets/sounds/locales/ja-JP/" "$SRC_LOCALE/"
diff <(cd "$PROJ/assets/sounds/locales/ja-JP" && sha256sum *.ogg language.json | sort) \
     <(cd "$SRC_LOCALE"                       && sha256sum *.ogg language.json | sort) \
  || { echo "🛑 ja-JP master 置換漏れ — 上書き失敗"; exit 1; }

# 4. Board 選択
idf.py menuconfig
# → Xiaozhi Assistant → Board Type → "Movecall Moji2.0 小智AI衍生版"

# 5. ビルド
idf.py build

# 6. merge_bin (★ User の assets.bin を 0x800000 に組込)
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
cd build && python -m esptool --chip esp32c5 merge_bin \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  -o merged-binary.bin \
  0x0 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin"

# 7. worktree クリーンアップ
cd ~/xiaozhi-work/xiaozhi-esp32
git worktree remove ../xiaozhi-esp32-moji2-rebuild
```

詳細: [`docs/operations/firmware-build-v2.2.6-esp32c5.md`](operations/firmware-build-v2.2.6-esp32c5.md)

---

## 🌐 外部連携

| 種別 | 場所 |
|---|---|
| 本家リポジトリ | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) v2.2.6 |
| assets.bin 生成元 | [xCentury-lab/xiaozhi-assets-generator](https://github.com/xCentury-lab/xiaozhi-assets-generator) Web UI |
| OTA サーバ | `https://classism.net/xiaozhi/ota/` (AWS EC2 `ubuntu@54.65.243.80`) |
| Shopify ストア | `xiaozhi-ai.myshopify.com` |
| ESP-IDF | **v5.5+** 必須 (ESP32-C5 サポート) |
| Movecall 公式 hw | https://oshwhub.com/movecall/moji2 |

---

## ⚖️ ライセンス・メンテナ

- **License**: MIT
- **メンテナ**: xxc (xxc@ctoch.jp) / xCentury PAI
- **公開範囲**: Private

---

*最終更新: 2026-05-29 | 詳細は [README.md](../README.md) と [`docs/build-plan.md`](build-plan.md) 参照。*
