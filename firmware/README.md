# firmware/

このディレクトリはビルド成果物 (`.bin`) の配置場所です。サイズが大きいため `.gitignore` で除外されますが、**`assets.bin` のみ Git 管理**します (xiaozhi-assets-generator 生成済 master)。

## 現在のディレクトリ構造

```
firmware/
├── README.md                                  ← 本ファイル
└── v2.2.6_movecall-moji2-esp32c5/             ⭐ 商品化対象
    ├── assets.bin                              ★ 配置済 (2.1 MB、Git 管理)
    └── (build 後に追加)
        ├── bootloader.bin
        ├── partition-table.bin
        ├── ota_data_initial.bin
        ├── xiaozhi.bin
        ├── merged-binary.bin                    ← 書込用メイン
        ├── flash_args
        └── manifest.json
```

## 命名規則

```
v{ver}_{board-sku}/                                              ディレクトリ
xiaozhi_v{ver}_{board-sku}_{YYYYMMDD}_idf{X.Y.Z}.bin              ファイル
```

例: `firmware/v2.2.6_movecall-moji2-esp32c5/xiaozhi_v2.2.6_movecall-moji2-esp32c5_20260530_idf552.bin`

## assets.bin について

- **生成元**: [xiaozhi-assets-generator Web UI](https://github.com/xCentury-lab/xiaozhi-assets-generator)
- **内容**: xCentury 黒猫 21 感情 emoji (256×256 RGBA) + Custom MultiNet (hikarin, nekochan) + フォント
- **書込先**: Flash `0x800000` partition (assets / spiffs、8 MB)
- **build 時の組込**: `merge_bin` で `0x800000 assets.bin` として merged-binary に統合

詳細: [docs/operations/firmware-build-v2.2.6-esp32c5.md](../docs/operations/firmware-build-v2.2.6-esp32c5.md) Step 4-(α) / Step 6

## ビルドコマンド (要約)

```bash
PROJ=/home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-Moji2.0
cd build && python -m esptool --chip esp32c5 merge_bin \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  -o merged-binary.bin \
  0x0 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 "$PROJ/firmware/v2.2.6_movecall-moji2-esp32c5/assets.bin"
```

## 関連 doc

- [../docs/operations/firmware-build-v2.2.6-esp32c5.md](../docs/operations/firmware-build-v2.2.6-esp32c5.md) — ビルド完全手順
- [../docs/operations/flash-guide.md](../docs/operations/flash-guide.md) — 量産ライン書込
- [../docs/architecture/moji2-board-overview.md](../docs/architecture/moji2-board-overview.md) — Moji 2.0 ボード仕様
