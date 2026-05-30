# Xiaozhi ファームウェア書込手順書

> **対象**: Waveshare ESP32-S3-Touch-LCD-1.85C（V1.0）への書込作業
> **対象読者**: 量産ライン作業者・サポート・エンジニア（PC 操作の基本知識があれば可）
> **作業時間**: 準備 5 分 + 書込 2 分 + 確認 2 分 = **合計 10 分**
> **作成日**: 2026-04-18
> **ドキュメント目次**: [../README.md](../README.md)

---

## 📋 作業前チェックリスト

作業を始める前に、以下がすべて揃っているか確認してください。

### ハードウェア

- [ ] **Waveshare ESP32-S3-Touch-LCD-1.85C 実機**（V1.0 リビジョン）
- [ ] **USB-C ケーブル**（データ通信対応品。**充電専用ケーブルは不可**）
- [ ] **Windows 11 または Ubuntu Desktop の PC**（セットアップ済み）

### ソフトウェア（初回のみ。2 回目以降はスキップ）

- [ ] ESP-IDF v5.5.2 以上がインストール済み（推奨 v5.5.4）
- [ ] Linux 環境の場合: ユーザーが `dialout` グループに所属

> **初回セットアップ**: [../setup/linux.md](../setup/linux.md) または [../setup/windows.md](../setup/windows.md) 参照

### ファームウェア

- [ ] `firmware/` ディレクトリ配下に書込対象の `.bin` ファイル存在

**本手順書では以下のファイルを例に説明します**:

```
/home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin
```

書込ファイルを変更する場合は、下記コマンド中のパスを対象ファイルに差替えてください。

---

## 🎯 方法 1: シェル 1 行で書込（推奨・失敗が少ない）

### ステップ 0: PC へのデバイス接続

1. **PC の USB-C ポートに Waveshare 1.85C を接続**（USB-C ケーブル経由）
2. 実機の LCD が点灯することを確認（書込済なら前ファームが起動、未書込なら真っ暗でも OK）

### ステップ 1: ターミナルを開く

- **Ubuntu**: キーボード `Ctrl+Alt+T` または「アプリ一覧」→「端末」
- **Windows**: スタートメニューから「**ESP-IDF 5.5 PowerShell**」を検索して開く（普通の PowerShell/CMD は ❌ 不可）

### ステップ 2: デバイス認識を確認

ターミナルに以下を 1 行ずつ入力して実行（Enter キー）:

**Ubuntu**:
```bash
ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

期待する出力:
```
/dev/ttyACM0
```

- ✅ `/dev/ttyACM0` が表示される → ステップ 3 へ
- ❌ `No such file or directory` → [トラブルシューティング A](#a-デバイスが認識されない) へ

**Windows**（PowerShell）:
```powershell
Get-PnpDevice -Class Ports | Format-Table -AutoSize
```

表示された `COMx`（例: `COM7`）をメモ。以降のコマンドで `/dev/ttyACM0` を `COM7` に置き換えます。

### ステップ 3: ESP-IDF 環境を有効化

**Ubuntu の場合**:
```bash
source ~/esp/esp-idf/export.sh
```

または、`get_idf` エイリアスが設定済みなら:
```bash
get_idf
```

期待する出力（最後の数行）:
```
Done! You can now compile ESP-IDF projects.
Go to the project directory and run:

  idf.py build
```

**Windows の場合**: ステップ 1 で **ESP-IDF PowerShell** を開いたならスキップ（自動有効化済）

### ステップ 4: 書込ツールが動くか確認

```bash
python -m esptool version
```

期待する出力:
```
esptool.py v4.12.dev1
...
```

- ✅ バージョン番号が表示される → ステップ 5 へ
- ❌ `No module named esptool` → ステップ 3 をやり直し

### ステップ 5: ファームウェアファイルの存在確認

```bash
ls -la /home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin
```

期待する出力:
```
-rw-rw-r-- 1 xxc xxc 9895941  4月 18 15:45 /home/xxc/...
                    ^^^^^^^
                    9,895,941 バイト (約 9.44 MB)
```

- ✅ サイズが **9,895,941 バイト** → ステップ 6 へ
- ❌ `No such file` → パスを確認。正しい `.bin` ファイル名・ディレクトリ名か再確認

### ステップ 6: 書込前のフル Flash バックアップ（初回のみ強く推奨）

**既存の工場ファームを必ず保全**してください。書込失敗や不具合時の復元用です。

```bash
mkdir -p ~/xiaozhi-work/backup
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    read_flash 0x0 0x1000000 \
    ~/xiaozhi-work/backup/waveshare-1.85c_stock_$(date +%Y%m%d_%H%M).bin
```

所要 3〜4 分。以下のような進行バーが流れます:
```
Reading 16777216 bytes at 0x00000000 in 4096-byte blocks...
4096 (0 %)...
...
16777216 (100 %)
Read 16777216 bytes at 0x0 in 163.1 seconds (823.0 kbit/s)...
Hard resetting via RTS pin...
```

完了すると `~/xiaozhi-work/backup/` 配下にバックアップファイルが作成されます。

> **2 回目以降の同一基板**: 既にバックアップがあればスキップ可

### ステップ 7: 書込実行 🔥

以下を **1 コマンド**として入力してください（全体を 1 行にしても改行付きでも OK）:

```bash
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before default_reset --after hard_reset \
    write_flash --flash_mode dio --flash_size 16MB --flash_freq 80m \
    0x0 /home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin
```

#### 各オプションの意味（参考）

| オプション | 意味 |
|---|---|
| `--chip esp32s3` | ESP32-S3 向けビルドであることを明示 |
| `-p /dev/ttyACM0` | シリアルポート指定（Windows は `-p COM7` など） |
| `-b 460800` | 書込時のボーレート（高速）。失敗時は `115200` に下げる |
| `--before default_reset` | 書込前に自動リセット |
| `--after hard_reset` | 書込後に自動起動 |
| `write_flash` | 書込サブコマンド |
| `--flash_mode dio` | DIO モード（W25Q128 対応）|
| `--flash_size 16MB` | Flash 容量 |
| `--flash_freq 80m` | Flash クロック |
| `0x0` | 書込開始アドレス（merged-binary は必ず 0x0）|
| `xiaozhi_...bin` | 書込対象ファイル |

### ステップ 8: 進行バーを見守る

コマンド実行後、以下のような流れで進行します。

```
esptool.py v4.12.dev1
Serial port /dev/ttyACM0
Connecting...
Chip is ESP32-S3 (QFN56) (revision v0.2)
Features: WiFi, BLE, Embedded PSRAM 8MB (AP_3v3)
Crystal is 40MHz
USB mode: USB-Serial/JTAG
MAC: 98:a3:16:d8:06:84
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 460800
Changed.
Configuring flash size...
Auto-detected Flash size: 16MB
Flash will be erased from 0x00000000 to 0x0096ffff...
Compressed 9895941 bytes to 7015846...
Writing at 0x00000000... (0 %)
Writing at 0x00010000... (1 %)
...
Writing at 0x00960000... (99 %)
Writing at 0x00968000... (100 %)
Wrote 9895941 bytes (7015846 compressed) at 0x00000000 in 110.4 seconds (effective 716.0 kbit/s)...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
```

**所要時間**: 約 1 分 30 秒〜2 分（ボーレート 460800 の場合）

#### ⚠️ 重要なメッセージ（書込成否の判定）

**✅ 成功の印**:
- `Hash of data verified.` が表示される（データ整合性チェック通過）
- `Hard resetting via RTS pin...` で自動リセット

**❌ 失敗の印**:
- 途中で `A fatal error occurred:` と表示される
- `Writing at ...` が途中で止まる
- → [トラブルシューティング B](#b-書込が途中で止まる) へ

### ステップ 9: 実機 LCD の動作確認

書込成功後、Waveshare 1.85C が **自動リブート**します。以下を目視確認:

1. ✅ **LCD が点灯**（真っ暗でないこと）
2. ✅ **ブート画面が 1〜2 秒表示される**（Xiaozhi ロゴ or 黒地に文字）
3. ✅ **初回起動時は Wi-Fi 設定モード** — 画面に **QR コード**または **Wi-Fi 設定の案内**が表示される
4. ✅ **2 回目以降**（Wi-Fi 設定済の場合）— Xiaozhi の待機画面が表示され、「**Jarvis**」または「**Hi, ESP**」の呼びかけに反応

動作確認 OK なら作業完了 🎉

---

## 🔍 書込結果の SHA256 検証（品質保証）

量産ラインでは書込内容の整合性を SHA256 で確認することを推奨:

```bash
# 期待する SHA256（manifest.json から取得）
cat /home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/manifest.json | grep sha256

# 書込ファイルの SHA256 実測
sha256sum /home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin
```

両者の SHA256 文字列が完全に一致すれば OK。

---

## 🚨 トラブルシューティング

### A. デバイスが認識されない

症状: `/dev/ttyACM0` が `ls` で表示されない

#### 対処 A-1: USB ケーブル確認

- ケーブルを抜いて差し直す
- **充電専用ケーブル**は NG。PC 付属のデータ通信対応 USB-C ケーブルを使用
- 別の USB-C ポートに挿し替え

#### 対処 A-2: USB 認識確認（Linux）

```bash
lsusb | grep 303a
```

- ✅ `Bus 001 Device N: ID 303a:1001 Espressif USB JTAG/serial debug unit` と表示 → USB は認識している。次の対処へ
- ❌ 何も出ない → ケーブル不良 or 実機不良

#### 対処 A-3: dialout グループ（Linux のみ）

```bash
groups | grep dialout
```

- ✅ `dialout` が表示される → 次の対処へ
- ❌ 表示されない → 下記を実行後、**ログアウトして再ログイン**:
  ```bash
  sudo usermod -a -G dialout $USER
  ```

#### 対処 A-4: brltty 干渉（Ubuntu 22.04 のみ）

```bash
dpkg -l brltty 2>/dev/null | grep ii
```

- ✅ 何も出ない → OK
- ❌ `ii brltty` と表示される → 下記で削除後に USB 抜き差し:
  ```bash
  sudo apt remove -y brltty
  ```

### B. 書込が途中で止まる

症状: `Writing at 0x00???... (xx %)` で停止、または `Timeout` エラー

#### 対処 B-1: ボーレートを下げる

コマンド中の `-b 460800` を `-b 115200` に変更して再実行。

#### 対処 B-2: ケーブル変更

USB ケーブル品質不良の可能性。**別の高品質ケーブル**で再挑戦。

#### 対処 B-3: BOOT ボタンを押しながら接続

通常は不要ですが、どうしても書込モードに入れない場合:

1. 実機の **BOOT ボタンを押しっぱなし**
2. USB ケーブルを接続
3. そのまま書込コマンド実行
4. `Connecting......` と表示されたら BOOT ボタンを離す

### C. 書込は成功したが LCD が映らない

#### 対処 C-1: ハードウェアリビジョン確認

V1.0 / V2.0 の基板違いの可能性。本手順書の `.bin` は **V1.0 専用**です。

- **V2.0 機に V1.0 ファームを書込** → オーディオコーデック初期化でクラッシュ、ブートループ
- 症状: LCD がチカチカする、数秒毎に LCD が消えて再表示される

対処: バックアップから復元（[対処 D](#d-緊急リカバリ既存ファームに戻す) 参照）するか、V2.0 用ファームを入手して書込。

#### 対処 C-2: バックライト確認

- 完全に真っ暗で何も映らない → バックライト故障の可能性。別の実機で試す
- 一瞬だけ光ってすぐ消える → 電源/USB 給電不足。電源供給能力 5V/2A 以上の USB ポートへ

### D. 緊急リカバリ（既存ファームに戻す）

ステップ 6 でバックアップしていれば、いつでも復元可能:

```bash
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before default_reset --after hard_reset \
    write_flash 0x0 ~/xiaozhi-work/backup/waveshare-1.85c_stock_YYYYMMDD_HHMM.bin
```

`YYYYMMDD_HHMM` はバックアップ時のタイムスタンプ。ファイル名補完（Tab キー）で楽に入力可能。

---

## 📱 ファイル差替のバリエーション

本手順書は **日本語版 + tenclass.net OTA** を例にしています。他のバリアントを書込む場合、**ステップ 7 のファイルパスを下記に差替え**:

| バリアント | 書込パス |
|---|---|
| **英語 + tenclass.net** | `firmware/v2.2.4_waveshare-1.85c_V1.0_en-US_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_en-US_jarvis-hiesp_20260418.bin` |
| **日本語 + tenclass.net** | `firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin` |
| **英語 + classism.net**（自社OTA）| `firmware/v2.2.4_waveshare-1.85c_V1.0_en-US_jarvis-hiesp_company/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_en-US_jarvis-hiesp_company_20260418.bin` |
| **日本語 + classism.net**（自社OTA）| `firmware/v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_company/xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_company_20260418.bin` |

ベースパス `/home/xxc/project/Xiaozhi-Firmware-VoCat/` は共通。

---

## 🛠 補足: その他の書込方法

### 方法 2: Python スクリプト化（量産ライン自動化向け）

毎回コマンドを手入力するのを避けるため、`flash.py` スクリプトを用意:

```python
#!/usr/bin/env python3
"""Xiaozhi firmware flasher."""
import subprocess
import sys
import glob
from pathlib import Path

FIRMWARE = Path(
    "/home/xxc/project/Xiaozhi-Firmware-VoCat/firmware/"
    "v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp/"
    "xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin"
)

def find_port() -> str:
    for pattern in ["/dev/ttyACM*", "/dev/ttyUSB*"]:
        ports = sorted(glob.glob(pattern))
        if ports:
            return ports[0]
    raise SystemExit("❌ ESP32 が見つかりません")

def main():
    port = find_port()
    print(f"📡 Port: {port}")
    print(f"📦 Firmware: {FIRMWARE.name}")
    subprocess.run([
        sys.executable, "-m", "esptool",
        "--chip", "esp32s3", "-p", port, "-b", "460800",
        "--before", "default_reset", "--after", "hard_reset",
        "write_flash", "--flash_mode", "dio",
        "--flash_size", "16MB", "--flash_freq", "80m",
        "0x0", str(FIRMWARE),
    ], check=True)
    print("✅ 書込成功")

if __name__ == "__main__":
    main()
```

保存して以下で実行:
```bash
get_idf
python3 flash.py
```

### 方法 3: Windows GUI（Flash Download Tool）

ターミナル操作に不慣れな作業者向け:

1. https://www.espressif.com/en/support/download/other-tools から **Flash Download Tool** ダウンロード
2. 起動 → **ESP32-S3** → **Develop** を選択
3. ファイル欄に `.bin`、オフセット欄に **`0x0`**
4. SPI フラッシュ設定: **DIO / 80MHz / 16MB**
5. COM ポート選択、ボーレート **460800**
6. **START** ボタンで書込

---

## 📝 作業記録テンプレート（量産ラインの記録用）

各実機の書込時に以下を記録することを推奨（Excel/CSV 管理）:

| 項目 | 記入例 |
|---|---|
| 作業日時 | 2026-04-18 15:30:00 |
| 作業者 | 山田太郎 |
| 実機 MAC | `98:a3:16:d8:06:84`（ログ冒頭に表示）|
| 書込ファーム名 | `xiaozhi_v2.2.4_waveshare-1.85c_V1.0_ja-JP_jarvis-hiesp_20260418.bin` |
| ファーム SHA256 | `449f665f...037` |
| バックアップ保存先 | `~/xiaozhi-work/backup/waveshare-1.85c_stock_20260418_1530.bin` |
| 書込結果 | ✅ Hash verified / ❌ エラー: ___ |
| 動作確認 | ✅ LCD 表示 / ✅ Wi-Fi / ✅ ウェイクワード / ❌ ___ |
| 備考 | |

---

## 📚 関連ドキュメント

- [../../README.md](../../README.md) — プロジェクト概要
- [../README.md](../README.md) — ドキュメントマスターインデックス
- [../setup/linux.md](../setup/linux.md) / [../setup/windows.md](../setup/windows.md) — 初回環境構築
- [../../firmware/README.md](../../firmware/README.md) — ファームウェア管理方針
- [../build-plan.md](../build-plan.md) — 計画書（Phase 別詳細）
- [../Review/linux-environment-setup-log.md](../Review/linux-environment-setup-log.md) — セットアップ実測ログ
- 各 firmware サブディレクトリの `manifest.json` — ビルドメタデータ

---

## 🔗 外部参照

- esptool 公式ドキュメント: https://docs.espressif.com/projects/esptool/en/latest/esp32s3/
- ESP-IDF Flash Encryption: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/security/flash-encryption.html
- Flash Download Tool: https://www.espressif.com/en/support/download/other-tools

---

*本手順書は 2026-04-18 時点の実機動作検証に基づいて作成されました。更新時は末尾に改訂履歴を追記してください。*

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-04-18 | 1.0 | 初版作成（V1.0 実機動作検証済） | xxc@ctoch.jp |
