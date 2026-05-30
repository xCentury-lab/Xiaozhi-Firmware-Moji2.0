#!/usr/bin/env python3
"""
xiaozhi-build: 4軸カスタマイズを自動適用してファームを生成する

カスタマイズ要件（docs/customization-spec.md 準拠）:
  1. UI 言語             : Japanese (ja-JP)
  2. ウェイクワード      : Alexa + Hi, ESP
  3. OTA URL             : https://classism.net/xiaozhi/ota/
  4. ja-JP 音声マスタ    : assets/sounds/locales/ja-JP/*.ogg を本家に注入 (ja-JP 限定)

旧「ブートロゴ "和合" 」軸と「ブランド」軸は 2026-05-24 廃止。

使い方:
  python xiaozhi_build.py <board-sku> [--hw-rev V1.0] [--date YYYYMMDD]
                         [--no-flash] [--port /dev/ttyACM0]

例:
  python xiaozhi_build.py waveshare-esp32-s3-touch-lcd-1.85c
  python xiaozhi_build.py yunliao-s3
  python xiaozhi_build.py yunliao-s3 --port /dev/ttyACM0
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ========== 固定カスタマイズ要件（4 軸）==========
# 旧 logo_text "和合" と brand axis は 2026-05-24 削除
CUSTOMIZATION = {
    "language": "Japanese (ja-JP)",
    "language_config": "CONFIG_LANGUAGE_JA_JP",
    "wake_words": ["Alexa", "Hi,ESP"],
    "wake_word_models": ["wn9_alexa", "wn9_hiesp"],
    "wake_word_configs": ["CONFIG_SR_WN_WN9_ALEXA", "CONFIG_SR_WN_WN9_HIESP"],
    "ota_url": "https://classism.net/xiaozhi/ota/",
    "brand_name": "company",  # manifest 記録用のみ、独立軸からは除外
    "brand_display": "company (xCentury)",
    # ja-JP 音声マスタ (発音修正): build 時に locales/ja-JP/ から本家 source に上書きコピー
    "ja_jp_audio_master_dir": "assets/sounds/locales/ja-JP/",
}

# すべての CONFIG_LANGUAGE_* / CONFIG_SR_WN_WN9_* を一旦リセットする際の対象
ALL_LANGUAGES = ["ZH_CN", "ZH_TW", "EN_US", "JA_JP", "KO_KR", "VI_VN", "TH_TH",
                 "DE_DE", "FR_FR", "ES_ES", "IT_IT", "RU_RU", "AR_SA", "HI_IN",
                 "PT_PT", "PL_PL", "CS_CZ", "FI_FI", "TR_TR", "ID_ID", "UK_UA",
                 "RO_RO", "BG_BG", "CA_ES", "DA_DK", "EL_GR", "FA_IR", "FIL_PH",
                 "HE_IL", "HR_HR"]

# font 候補（大きい順）。OTA パーティションに収まるまで降順で試行
# FONT_FALLBACK は旧 logo 軸 ("和合") 用、2026-05-24 軸定義変更で廃止

PROJECT_ROOT = Path("/home/xxc/project/Xiaozhi-Firmware-VoCat")
XIAOZHI_SRC = Path(os.environ.get("XIAOZHI_SRC", "/home/xxc/xiaozhi-work/xiaozhi-esp32"))
ESP_IDF_EXPORT = Path("/home/xxc/esp/esp-idf/export.sh")
VERSION = os.environ.get("XIAOZHI_VERSION", "v2.2.4")


# ========== ユーティリティ ==========

def run(cmd, cwd=None, check=True, capture=False, shell=False):
    print(f"  [RUN] {cmd if shell else ' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, shell=shell,
                       capture_output=capture, text=capture)
    if check and r.returncode != 0:
        if capture:
            print(r.stdout)
            print(r.stderr, file=sys.stderr)
        sys.exit(f"Command failed (exit {r.returncode})")
    return r


def run_idf(cmd, cwd=XIAOZHI_SRC, capture=False):
    """ESP-IDF 環境でコマンド実行（export.sh を source してから）"""
    wrapped = f"source {ESP_IDF_EXPORT} > /dev/null 2>&1 && {cmd}"
    return run(wrapped, cwd=cwd, shell=True, capture=capture)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ========== ボード情報取得 ==========

def find_board_kconfig_symbol(board_sku: str) -> str:
    """main/CMakeLists.txt から BOARD_TYPE_* シンボルを逆引き"""
    cmake = (XIAOZHI_SRC / "main" / "CMakeLists.txt").read_text()
    # パターン: elseif(CONFIG_BOARD_TYPE_XXX)\n    set(BOARD_TYPE "yyy")
    pattern = re.compile(
        r'CONFIG_(BOARD_TYPE_\w+)\)\s*\n\s*set\(BOARD_TYPE\s+"([^"]+)"',
        re.MULTILINE,
    )
    for m in pattern.finditer(cmake):
        if m.group(2) == board_sku:
            return "CONFIG_" + m.group(1)
    sys.exit(f"Board SKU '{board_sku}' が main/CMakeLists.txt に見つかりません")


def get_board_extras(board_sku: str) -> dict:
    """ボード固有の追加 sdkconfig 設定を config.json から取得"""
    cfg_path = XIAOZHI_SRC / "main" / "boards" / board_sku / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        cfg = json.loads(cfg_path.read_text())
        extras = {}
        for b in cfg.get("builds", []):
            for line in b.get("sdkconfig_append", []):
                if "=" in line:
                    k, v = line.split("=", 1)
                    extras[k] = v
        return extras
    except Exception as e:
        print(f"  [WARN] config.json パース失敗: {e}")
        return {}


# ========== sdkconfig 操作 ==========

def edit_sdkconfig(board_symbol: str, extras: dict, font_name: str = None):
    sdk = XIAOZHI_SRC / "sdkconfig"
    lines = sdk.read_text().splitlines()
    out = []

    # すべての BOARD_TYPE_*=y を is-not-set にして、指定シンボルのみ =y
    board_re = re.compile(r"^(# )?CONFIG_BOARD_TYPE_\w+( is not set|=y)$")
    # すべての LANGUAGE_*=y をリセットし、JA_JP のみ =y
    lang_re = re.compile(r"^(# )?CONFIG_LANGUAGE_\w+( is not set|=y)$")
    # すべての wake word をリセットし、ALEXA + HIESP のみ =y
    wn_re = re.compile(r"^(# )?CONFIG_SR_WN_WN9\w+( is not set|=y)$")

    seen_board = False
    seen_lang_block = False
    seen_wn_block = False

    for ln in lines:
        if board_re.match(ln):
            # 全 BOARD_TYPE_* を is not set に
            sym = re.search(r"CONFIG_(BOARD_TYPE_\w+)", ln).group(0)
            if sym == board_symbol:
                out.append(f"{sym}=y")
                seen_board = True
            else:
                out.append(f"# {sym} is not set")
            continue

        if lang_re.match(ln):
            # 全 LANGUAGE_* を is not set に
            sym = re.search(r"CONFIG_(LANGUAGE_\w+)", ln).group(0)
            if sym == CUSTOMIZATION["language_config"]:
                out.append(f"{sym}=y")
            else:
                out.append(f"# {sym} is not set")
            seen_lang_block = True
            continue

        if wn_re.match(ln):
            sym = re.search(r"CONFIG_(SR_WN_WN9\w+)", ln).group(0)
            if sym in CUSTOMIZATION["wake_word_configs"]:
                out.append(f"{sym}=y")
            else:
                out.append(f"# {sym} is not set")
            seen_wn_block = True
            continue

        # OTA URL を書き換え
        if ln.startswith("CONFIG_OTA_URL="):
            out.append(f'CONFIG_OTA_URL="{CUSTOMIZATION["ota_url"]}"')
            continue

        # ボード固有 extras を上書き（既存キーがあれば置換、なければ追記後述）
        replaced = False
        for k, v in extras.items():
            if ln.startswith(f"{k}=") or ln.startswith(f"# {k} is not set"):
                out.append(f"{k}={v}")
                replaced = True
                break
        if replaced:
            continue

        out.append(ln)

    if not seen_board:
        sys.exit(f"sdkconfig に {board_symbol} 関連の行が見つかりません。"
                 f"menuconfig 等でボード選択を一度行ってください。")

    # extras のうち sdkconfig に存在しなかったものを末尾追記
    joined = "\n".join(out)
    for k, v in extras.items():
        if f"{k}=" not in joined and f"# {k} is not set" not in joined:
            out.append(f"{k}={v}")

    sdk.write_text("\n".join(out) + "\n")
    print(f"  [sdkconfig] board={board_symbol}, lang={CUSTOMIZATION['language_config']}, "
          f"wake_words={'+'.join(CUSTOMIZATION['wake_word_configs'])}, "
          f"extras={extras}")


# ========== ja-JP 音声マスタを本家 source に注入 (発音修正、ja-JP 限定) ==========
# 旧「ブートロゴ "和合" 注入」処理 (ensure_logo_patch + font fallback) は 2026-05-24 削除

def inject_ja_jp_audio_master():
    """assets/sounds/locales/ja-JP/*.ogg を本家 main/assets/locales/ja-JP/ に上書きコピー"""
    src_dir = PROJECT_ROOT / "assets" / "sounds" / "locales" / "ja-JP"
    dst_dir = XIAOZHI_SRC / "main" / "assets" / "locales" / "ja-JP"
    if not src_dir.exists():
        print(f"  [skip] ja-JP audio master not present: {src_dir}")
        return 0
    count = 0
    for ogg in src_dir.glob("*.ogg"):
        dst = dst_dir / ogg.name
        shutil.copy2(ogg, dst)
        count += 1
    print(f"  [ja-JP audio] {count} *.ogg files injected from {src_dir} -> {dst_dir}")
    return count


# ========== ビルド ==========

def build_firmware() -> bool:
    """単一 build (font フォールバックは旧ロゴ軸廃止により不要)"""
    print(f"\n===== Building =====")
    wrapped = f"source {ESP_IDF_EXPORT} > /dev/null 2>&1 && idf.py build"
    r = subprocess.run(wrapped, cwd=XIAOZHI_SRC, shell=True,
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  [OK] Build succeeded")
        print(r.stdout.splitlines()[-5:] if r.stdout else "")
        return True
    print(r.stdout[-2000:] if r.stdout else "")
    print(r.stderr[-1000:] if r.stderr else "")
    return False


# ========== 成果物配置 ==========

def package_artifacts(board_sku: str, hw_rev: str, date: str,
                      board_extras: dict) -> dict:
    build = XIAOZHI_SRC / "build"
    # merge_bin
    run_idf(
        "python -m esptool --chip esp32s3 merge_bin "
        "--flash_mode dio --flash_freq 80m --flash_size 16MB "
        "-o merged-binary.bin "
        "0x0 bootloader/bootloader.bin "
        "0x8000 partition_table/partition-table.bin "
        "0xd000 ota_data_initial.bin "
        "0x20000 xiaozhi.bin "
        "0x800000 generated_assets.bin",
        cwd=build,
    )

    short_board = board_sku.replace("waveshare-esp32-s3-touch-lcd-", "waveshare-")
    # wake word サフィックス: wn9_alexa + wn9_hiesp → "alexa-hiesp"
    ww_suffix = "-".join(
        m.replace("wn9_", "") for m in CUSTOMIZATION["wake_word_models"]
    )
    dir_name = f"{VERSION}_{short_board}_{hw_rev}_ja-JP_{ww_suffix}_company"
    fw_name = (f"xiaozhi_{VERSION}_{short_board}_{hw_rev}_"
               f"ja-JP_{ww_suffix}_company_{date}")

    out_dir = PROJECT_ROOT / "firmware" / dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in ["bootloader/bootloader.bin", "partition_table/partition-table.bin",
              "ota_data_initial.bin", "xiaozhi.bin", "generated_assets.bin",
              "merged-binary.bin", "flash_args"]:
        src = build / f
        if src.exists():
            shutil.copy(src, out_dir / Path(f).name)

    merged = out_dir / "merged-binary.bin"
    final = out_dir / f"{fw_name}.bin"
    shutil.copy(merged, final)

    sha = sha256_of(final)
    size = final.stat().st_size

    manifest = {
        "firmware_name": fw_name,
        "board_sku": board_sku,
        "hardware_revision": hw_rev,
        "xiaozhi_version": VERSION,
        "language": CUSTOMIZATION["language"],
        "wake_words": CUSTOMIZATION["wake_words"],
        "wake_word_models": CUSTOMIZATION["wake_word_models"],
        "brand": CUSTOMIZATION["brand_display"],
        "ota_url": CUSTOMIZATION["ota_url"],
        "build_date": date,
        "build_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "idf_version": "v5.5.4",
        "target": "esp32s3",
        "flash_size_mb": 16,
        "binary_sha256": f"sha256:{sha}",
        "binary_size_bytes": size,
        "flash_layout": {
            "0x0": "bootloader.bin",
            "0x8000": "partition-table.bin",
            "0xd000": "ota_data_initial.bin",
            "0x20000": "xiaozhi.bin",
            "0x800000": "generated_assets.bin",
        },
        "sdkconfig_key_values": {
            CUSTOMIZATION["language_config"]: "y",
            **{c: "y" for c in CUSTOMIZATION["wake_word_configs"]},
            **board_extras,
            "CONFIG_OTA_URL": CUSTOMIZATION["ota_url"],
        },
        "notes": (
            f"Generated by .claude/skills/xiaozhi-build (project-scoped skill). "
            f"4-axis customization per docs/customization-spec.md: "
            f"ja-JP / {'+'.join(CUSTOMIZATION['wake_words'])} / classism.net OTA / "
            f"ja-JP audio master injection (assets/sounds/locales/ja-JP/)."
        ),
        "builder": os.environ.get("GIT_USER_EMAIL") or os.environ.get("USER") or "unknown",
        "source_commit": f"78/xiaozhi-esp32@{VERSION}",
    }

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    print(f"\n  [OK] {final}")
    print(f"  [OK] {out_dir / 'manifest.json'}")
    return {"out_dir": str(out_dir), "firmware": str(final),
            "sha256": sha, "size": size}


# ========== 書込み（任意）==========

def flash(port: str, merged_bin: Path):
    cmd = (f"python -m esptool --chip esp32s3 -p {port} -b 460800 "
           f"--before default_reset --after hard_reset write_flash 0x0 {merged_bin}")
    run_idf(cmd)


# ========== メイン ==========

def main():
    p = argparse.ArgumentParser(
        description="Xiaozhi ファーム 4軸カスタマイズ自動ビルド"
    )
    p.add_argument("board_sku", help="ボード SKU (main/boards/<sku>/)")
    p.add_argument("--hw-rev", default="V1.0")
    p.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    p.add_argument("--port", help="書込先 /dev/ttyACM0 等（指定時のみ書込み）")
    p.add_argument("--no-build", action="store_true",
                   help="sdkconfig 編集のみ、ビルドしない")
    p.add_argument(
        "--wake-word-models",
        help="ウェイクワードモデルをカンマ区切りで上書き "
             "(例: alexa,nihaomiaoban_tts2)。"
             "デフォルトは alexa+hiesp。"
    )
    args = p.parse_args()

    if args.wake_word_models:
        models = [m.strip().lower() for m in args.wake_word_models.split(",") if m.strip()]
        if not models:
            sys.exit("--wake-word-models is empty")
        CUSTOMIZATION["wake_word_models"] = [f"wn9_{m}" for m in models]
        CUSTOMIZATION["wake_word_configs"] = [f"CONFIG_SR_WN_WN9_{m.upper()}" for m in models]
        CUSTOMIZATION["wake_words"] = [m for m in models]
        print(f"  [override] wake_word_configs = {CUSTOMIZATION['wake_word_configs']}")

    if not XIAOZHI_SRC.exists():
        sys.exit(f"XIAOZHI_SRC が存在しません: {XIAOZHI_SRC}")
    if not ESP_IDF_EXPORT.exists():
        sys.exit(f"ESP-IDF が存在しません: {ESP_IDF_EXPORT}")

    # 1. ボード情報取得
    board_symbol = find_board_kconfig_symbol(args.board_sku)
    board_extras = get_board_extras(args.board_sku)
    print(f"Board   : {args.board_sku} ({board_symbol})")
    print(f"Extras  : {board_extras or '(なし)'}")
    print(f"Date    : {args.date}, HW Rev: {args.hw_rev}")

    # 2. sdkconfig 編集 & ボード切替時は fullclean が必要なので警告
    current_board = subprocess.run(
        ["grep", "-oE", "^CONFIG_BOARD_TYPE_\\w+=y", str(XIAOZHI_SRC / "sdkconfig")],
        capture_output=True, text=True,
    ).stdout.strip()
    need_fullclean = current_board != f"{board_symbol}=y"

    edit_sdkconfig(board_symbol, board_extras)

    if args.no_build:
        print("  [DONE] --no-build 指定のため sdkconfig 編集のみ")
        return

    # 3. fullclean（ボード変更時のみ）
    if need_fullclean:
        print("\n===== Full clean (board switched) =====")
        sdk_backup = XIAOZHI_SRC / "sdkconfig"
        saved = sdk_backup.read_text()
        run_idf("idf.py fullclean")
        sdk_backup.write_text(saved)

    # 4. ja-JP build の場合のみ、自家音声マスタを本家 source に注入 (発音修正)
    if CUSTOMIZATION["language_config"] == "CONFIG_LANGUAGE_JA_JP":
        inject_ja_jp_audio_master()

    # 5. ビルド (旧 font fallback ロジックは 2026-05-24 廃止)
    if not build_firmware():
        sys.exit("Build failed")

    # 6. マージ + 配置 + manifest 生成
    result = package_artifacts(args.board_sku, args.hw_rev, args.date, board_extras)

    # 7. 書込み（--port 指定時のみ）
    if args.port:
        print(f"\n===== Flashing to {args.port} =====")
        flash(args.port, Path(result["firmware"]))

    print("\n===== SUMMARY =====")
    print(f"  Firmware : {result['firmware']}")
    print(f"  SHA256   : {result['sha256']}")
    print(f"  Size     : {result['size']:,} bytes")


if __name__ == "__main__":
    main()
