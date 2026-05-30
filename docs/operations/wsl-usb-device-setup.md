# WSL から ESP32 デバイスへの USB アクセス手順

> **対象**: WSL2 (Ubuntu 22.04 等) で作業しながら、Windows ホストに接続された ESP-VoCat / ESP32 デバイスに `esptool` で書込・読込・erase を実行する手順
> **対象 OS**: Windows 10 21H2+ / Windows 11、WSL2 kernel 5.10.60.1+
> **作成日**: 2026-05-24
> **関連 doc**: [esp32s3-download-mode.md](esp32s3-download-mode.md) / [flash-guide.md](flash-guide.md) / [../../firmware/ESP-VoCat/boot-rst-sequence.md](../../firmware/ESP-VoCat/boot-rst-sequence.md)

---

## 0. 結論サマリ

| 質問 | 答え |
|---|---|
| WSL から `/dev/ttyACM0` が見えるか? | ❌ default では見えない (WSL2 の USB host 非対応) |
| Windows host に USB 接続したデバイスを WSL から扱えるか? | ✅ **2 つの方法あり**: (A) `usbipd-win` で attach / (B) Windows PowerShell 直接実行 |
| 推奨はどちら? | **案 A (`usbipd-win`)** — 商品化フローを WSL で完結できる、一度設定すれば永続的 |

---

## 1. なぜ WSL2 は USB device を直接見れないか (First Principles)

### 1.1 アーキテクチャ的理由

WSL2 は **軽量 Hyper-V VM** の中で独立した Linux カーネルを動かす:

```
┌─────────────────────────────────────────────────┐
│  Windows Host                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Windows USB Stack                       │    │
│  │  (USB driver) ← USB Device 認識         │    │
│  └──────────┬───────────────────────────────┘    │
│             │ (default で bridge なし)            │
│  ┌──────────▼───────────────────────────────┐    │
│  │  Hyper-V VM (WSL2)                       │    │
│  │  Linux kernel 6.x (USB host driver 無効) │    │
│  │  /dev/ttyACM0 ← 見えない                 │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

→ Windows USB stack は device を認識するが、**WSL2 kernel には伝わらない**。

### 1.2 解決原理

`usbipd-win` (Microsoft 公式 + dorssel/usbipd-win OSS) が **USB over IP (USB/IP) protocol** で bridge する:

```
┌────────────────────────────────────────────────────┐
│  Windows Host                                       │
│  USB Device  →  Windows USB Stack                   │
│                    │                                │
│                    ↓                                │
│              usbipd-win (USB/IP server)             │
│                    │ (TCP/3240, localhost)          │
│                    ↓                                │
│  Hyper-V VM (WSL2):                                 │
│              vhci_hcd kernel module (USB/IP client) │
│                    │                                │
│                    ↓                                │
│              /dev/ttyACM0 ← 見える!                 │
└────────────────────────────────────────────────────┘
```

→ `usbipd attach --wsl` 実行で WSL kernel に vhci_hcd module がロードされ、Windows 側 USB が WSL 内に仮想 device として現れる。

### 1.3 別解 (案 B) の根拠

`esptool` は Python 製で Windows でも完全動作する。よって `esptool` だけは Windows で動かす case 分岐も有効 — ただし WSL 主導の商品化フロー doc 化が複雑化する。

---

## 2. 案 A: `usbipd-win` で WSL に attach (推奨、永続化)

### 2.1 初回セットアップ (Windows 側、1 回のみ)

**Windows PowerShell (管理者権限) で実行**:

```powershell
# 1. usbipd-win インストール (winget 経由、Windows 10 21H2+ / 11)
winget install --interactive --exact dorssel.usbipd-win

# 2. インストール後、PowerShell を再起動

# 3. インストール確認
usbipd --version
# 例: 4.x.x
```

### 2.2 デバイスの初回バインド (Windows 側、デバイスごとに 1 回)

ESP-VoCat を USB 接続した状態で:

```powershell
# 1. 接続中の USB device 一覧
usbipd list

# 出力例:
# BUSID  VID:PID    DEVICE                                  STATE
# 2-3    303a:1001  USB JTAG/serial debug unit (COM3)       Not shared
# 2-4    8087:0029  Intel(R) Wireless Bluetooth(R)          Not shared
```

ESP-VoCat の BUSID を特定 (典型的に `USB JTAG/serial debug unit`、`CP210x`、`CH340` 等のいずれか)。

```powershell
# 2. 共有可能化 (initial bind)
usbipd bind --busid 2-3
# Not shared → Shared に変わる
```

### 2.3 毎回の attach フロー (Windows 側、device 接続毎)

```powershell
# 3. WSL に attach
usbipd attach --busid 2-3 --wsl
# 注: --wsl で default WSL distro に attach
# 特定 distro 指定: --wsl Ubuntu-22.04
```

**ヒント**: `usbipd list` の STATE が `Attached` になっていれば成功。`Not attached` のままなら WSL distro が起動していない可能性。

### 2.4 WSL 側で確認

```bash
# WSL bash で:
ls /dev/ttyACM*
# /dev/ttyACM0 が見えれば OK

# dmesg で attach 確認
sudo dmesg | tail -5
# [xxx] cdc_acm 1-1:1.0: ttyACM0: USB ACM device
```

### 2.5 detach (Windows 側)

```powershell
# WSL から外す (esptool 実行終了後)
usbipd detach --busid 2-3

# 完全に bind 解除 (今後 attach しない)
usbipd unbind --busid 2-3
```

---

## 3. 案 B: Windows PowerShell から `esptool` 直接実行 (即時、設定不要)

### 3.1 初回セットアップ (Windows 側、1 回のみ)

```powershell
# Python インストール確認 (3.8+ 必要)
python --version
# なければ https://www.python.org/downloads/ または:
# winget install --interactive --exact Python.Python.3.12

# esptool インストール
python -m pip install --upgrade esptool

# 確認
python -m esptool version
# esptool v4.x.x
```

### 3.2 COM ポート特定

**方法 1**: デバイスマネージャー (`Win + X` → デバイスマネージャー → ポート (COM と LPT))

**方法 2**: PowerShell コマンド

```powershell
# 接続中の COM ポート一覧
Get-WMIObject Win32_SerialPort | Select-Object DeviceID, Description, Manufacturer

# 出力例:
# DeviceID  Description                       Manufacturer
# COM3      USB JTAG/serial debug unit (COM3) FTDI / Espressif Systems / WCH.CN
```

### 3.3 esptool 実行 (Windows PowerShell)

bash と PowerShell の構文差に注意:

| 観点 | WSL (bash) | Windows (PowerShell) |
|---|---|---|
| 行継続 | `\` (バックスラッシュ) | `` ` `` (バッククォート) |
| port 指定 | `-p /dev/ttyACM0` | `-p COM3` |
| パス区切り | `/` | `\` |

例 (PowerShell):
```powershell
python -m esptool --chip esp32s3 -p COM3 -b 460800 `
    --before no_reset --after hard_reset `
    erase_region 0x9000 0x4000
```

---

## 4. 案 A vs 案 B 選択ガイド

| 観点 | 案 A: `usbipd-win` | 案 B: Windows 直接 |
|---|---|---|
| 初回コスト | 5 分 | 2 分 |
| 2 回目以降 | `usbipd attach` 1 行 (Windows PowerShell) | PowerShell で esptool 直接実行 |
| 商品化フローの一貫性 | ✅ WSL で全工程完結 | ❌ flash/erase だけ Windows 切替 |
| 量産ライン作業者向け doc 化 | ✅ 1 つの bash script で完結 | ⚠️ Windows / WSL 切替手順を doc に追記必要 |
| ESP-IDF + idf.py monitor 統合 | ✅ WSL 内 ESP-IDF が直接 USB アクセス | ⚠️ Windows 側にも ESP-IDF が必要 |
| USB device の同時 attach 制約 | 1 device は WSL/Windows どちらか排他 | Windows のみ |
| **推奨度** | ⭐⭐⭐ | ⭐⭐ |

**推奨原則:**
- 商品化フェーズで継続的に USB device を扱う → **案 A**
- 1 回だけの単発オペレーション → **案 B** でも可

---

## 5. 共通 ESP32 オペレーション例

以下は `/dev/ttyACM0` (WSL via usbipd-win) と `COM3` (Windows direct) の両方で動作確認済パターン。

### 5.1 firmware 一括書込 (merged-binary)

```bash
# WSL
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before no_reset --after hard_reset \
    write_flash 0x0 merged-binary.bin
```

```powershell
# Windows PowerShell
python -m esptool --chip esp32s3 -p COM3 -b 460800 `
    --before no_reset --after hard_reset `
    write_flash 0x0 merged-binary.bin
```

### 5.2 NVS partition のみ erase (volume issue 検証等)

ESP-VoCat 用 NVS partition は `offset=0x9000, size=16KB (0x4000)` ([esp-vocat-partition-layout.md](esp-vocat-partition-layout.md) §1):

```bash
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before no_reset --after hard_reset \
    erase_region 0x9000 0x4000
```

### 5.3 Flash 全消去 (factory reset)

```bash
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before no_reset --after no_reset \
    erase_flash
# 続けて write_flash で firmware 書戻す必要あり
```

### 5.4 Flash dump (バックアップ / forensics)

```bash
# 16MB flash の全 dump
python -m esptool --chip esp32s3 -p /dev/ttyACM0 -b 460800 \
    --before no_reset --after no_reset \
    read_flash 0x0 0x1000000 esp-vocat_dump_$(date +%Y%m%d).bin
```

### 5.5 シリアル monitor (起動 log 確認)

#### WSL + ESP-IDF
```bash
source ~/esp/esp-idf/export.sh
idf.py -p /dev/ttyACM0 monitor    # Ctrl+] で終了
```

#### WSL + 軽量 (ESP-IDF 不要)
```bash
sudo apt install screen
screen /dev/ttyACM0 115200    # Ctrl+A K で終了
```

#### Windows PowerShell
```powershell
# Espressif Idf-tools (ESP-IDF v5.x) 必要
idf.py -p COM3 monitor
# または Tera Term / PuTTY 等の terminal app
```

---

## 6. トラブルシューティング

### 6.1 `usbipd list` で device が出ない

**症状**: USB 接続したが `usbipd list` に表示されない。

**対策**:
- USB ケーブルを差し直す (USB device 自体は Windows に認識されているか「デバイスマネージャー」で確認)
- ESP-VoCat 側の **BOOT ボタン押し続けて再接続** (download mode で USB JTAG/Serial として認識される)
- USB ハブ経由なら直接接続を試す

### 6.2 `usbipd attach` が `error: WSL is not running` で失敗

**症状**: attach 時に WSL 起動チェックでエラー。

**対策**:
```powershell
# WSL distro 起動状態確認
wsl --list --verbose
# STATE が Stopped なら:
wsl -d Ubuntu-22.04
# WSL bash 起動後、再度 attach
```

### 6.3 attach 後も WSL から `/dev/ttyACM0` が見えない

**症状**: `usbipd attach` は成功するが `ls /dev/ttyACM*` で no such file。

**対策**:
```bash
# WSL 内で vhci_hcd module 確認
lsmod | grep vhci
# 出ない場合:
sudo modprobe vhci-hcd

# dmesg で attach event 確認
sudo dmesg | tail -20
```

WSL kernel 5.10.60.1 未満は vhci-hcd 内蔵されていないため、kernel update 必要:
```powershell
# Windows PowerShell で
wsl --update
```

### 6.4 `Permission denied: '/dev/ttyACM0'`

**症状**: WSL から見えているが esptool 実行時に permission エラー。

**対策**:
```bash
# dialout group に追加 (恒久対策)
sudo usermod -a -G dialout $USER
# ↑ 反映には WSL 再起動必要 (wsl --shutdown → 再起動)

# 一時対応
sudo chmod 666 /dev/ttyACM0
```

### 6.5 esptool が `Connecting...` でハングする

**症状**: download mode に入っていない。

**対策**: ESP-VoCat 固有の BOOT+RST シーケンスで手動 download mode 投入。詳細は [../../firmware/ESP-VoCat/boot-rst-sequence.md](../../firmware/ESP-VoCat/boot-rst-sequence.md) と [esp32s3-download-mode.md](esp32s3-download-mode.md)。

**重要**: esptool 実行時は `--before no_reset --after hard_reset` を必ず付ける (自動 RTS リセットを抑止し、手動 download mode を保護)。

---

## 7. 量産ライン作業者向けクイックリファレンス

### 案 A (`usbipd-win`) を使う場合の毎回フロー

```
1. Windows: USB ケーブル接続
2. Windows: ESP-VoCat の BOOT+RST シーケンスで download mode 投入
   (BOOT 押下 → RST 短押し → BOOT 離す)
3. Windows PowerShell (管理者): usbipd attach --busid 2-3 --wsl
4. WSL: ls /dev/ttyACM*  ← 確認
5. WSL: python -m esptool ... write_flash 0x0 merged-binary.bin
6. デバイス自動再起動、動作確認
7. Windows PowerShell: usbipd detach --busid 2-3  (任意)
```

### 案 B (Windows 直接) を使う場合の毎回フロー

```
1. Windows: USB ケーブル接続
2. Windows: ESP-VoCat の BOOT+RST で download mode 投入
3. Windows PowerShell: Get-WMIObject Win32_SerialPort | ... ← COM ポート確認
4. Windows PowerShell: python -m esptool -p COM3 ... write_flash 0x0 merged-binary.bin
5. デバイス自動再起動、動作確認
```

---

## 8. 関連ドキュメント

- [esp32s3-download-mode.md](esp32s3-download-mode.md) — BOOT+RST シーケンスの詳細、ハング対処
- [flash-guide.md](flash-guide.md) — 量産ライン作業者向け 10 ステップ書込手順
- [esp-vocat-partition-layout.md](esp-vocat-partition-layout.md) — ESP-VoCat の partition table (NVS = `0x9000`, 16KB)
- [esp-vocat-build-procedure.md](esp-vocat-build-procedure.md) — ESP-VoCat firmware ビルド完全手順
- [../../firmware/ESP-VoCat/boot-rst-sequence.md](../../firmware/ESP-VoCat/boot-rst-sequence.md) — ESP-VoCat 固有 BOOT+RST 詳細
- [../plans/replace-wificonfig-ogg-ja-JP-2026-05-24.md](../plans/replace-wificonfig-ogg-ja-JP-2026-05-24.md) — esp-vocat 商品化路線、Phase 6 実機検証で本 doc を参照

## 9. 外部参照

- **usbipd-win GitHub**: https://github.com/dorssel/usbipd-win
- **Microsoft 公式 USB on WSL ドキュメント**: https://learn.microsoft.com/ja-jp/windows/wsl/connect-usb
- **esptool 公式 docs**: https://docs.espressif.com/projects/esptool/
- **WSL2 update**: https://learn.microsoft.com/ja-jp/windows/wsl/install

## 10. メモリ参照

- [[feedback_wsl2_localhost_vs_127]] — WSL2 関連の別制約 (localhost 限定 / 127.0.0.1 NG)。本 doc と並ぶ「WSL2 制約」シリーズ
- [[xiaozhi_firmware_build_pitfalls]] — flash/build 関連の落とし穴集

---

## 改訂履歴

| 日付 | バージョン | 内容 | 作成者 |
|---|---|---|---|
| 2026-05-24 | 1.0 | 初版作成。WSL2 USB 制約の First Principles 解説 + 案 A/B 完全手順 + ESP32 オペレーション 5 種 + トラブルシューティング 5 件 | PAI / xxc@ctoch.jp |
