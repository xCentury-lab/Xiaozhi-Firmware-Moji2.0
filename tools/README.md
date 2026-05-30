# tools/

既存の OTA URL パッチツール群。`Xiaozhi-Firmware-OTA/` からの移管。

## ファイル一覧

| ツール | 用途 |
|---|---|
| `patch_bin.py` | bin ファイル内の `api.tenclass.net` → `classism.net` 置換 |
| `patch_bin_2.py` | bin ファイル内の `xiaozhi.jp` → `classism.net` 置換 |
| `patch_release_zip.py` | リリース ZIP を展開→bin 一括パッチ→再ZIP化 |
| `inspect_ota.py` | bin 内の URL・キーワード抽出、未パッチ/パッチ済み判定 |
| `check.py` | ZIP 内 bin のパッチ結果検証 |
| `check_bin.py` | 生 bin のパッチ結果検証 |

## 位置づけ

本計画の **STEP 1 Phase 1-A** で `classism.net` をビルド時に組込むため、
原則これらのバイナリ後加工ツールは**不要**になります。

ただし以下の場合に緊急用として残します:

1. 本家リリース直後のホットフィックス（自前ビルドが間に合わないとき）
2. 第三者フォーク（iotsystem/x22x22/txp666）の英語 bin を借りる場合
3. サーバー障害時の URL 緊急切替

## 使い方

### OTA URL 書換（単一 bin）

```powershell
python tools/patch_bin.py firmware/backup/waveshare-1.85c_stock_20260418.bin
# → firmware/backup/waveshare-1.85c_stock_20260418_patched.bin
```

### リリース ZIP 一括

```powershell
python tools/patch_release_zip.py v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c.zip
# → v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_patched.zip
```

### bin の現状調査

```powershell
python tools/inspect_ota.py firmware/backup/waveshare-1.85c_stock_20260418.bin
# → 旧URL / 新URL / キーワード検出結果を表示
```

## STEP 1 完了後の運用

- これらのツールは `tools/legacy/` へ移動予定
- 通常運用では `build/verify_build.py` のみ使用
