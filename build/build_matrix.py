"""
量産ビルドスクリプト
=====================================

ビルドマトリクス（matrix.yaml）に従って、
「ボード × 言語 × ブランド」の全組合せ、または指定した組合せで
Xiaozhi ファームウェアをビルドする。

使い方:
    # 全バリエーション一括ビルド
    python build/build_matrix.py --all

    # 単一ボード・単一言語
    python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English

    # 日本語版ビルド
    python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang Japanese

    # 失敗したものだけ再ビルド
    python build/build_matrix.py --only-failed

    # ドライラン（実際のビルドは行わず、組合せと設定を確認）
    python build/build_matrix.py --dry-run --all

前提:
    - 本家 78/xiaozhi-esp32 をクローンし、環境変数 XIAOZHI_SRC にそのパスを設定
    - ESP-IDF 5.4+ 環境（idf.py が PATH に通っていること）で実行
    - Windows: ESP-IDF PowerShell / Linux: source export.sh 済み
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

try:
    import yaml
except ImportError:
    sys.exit("pyyaml が必要です: pip install -r requirements.txt")


# ========== 設定 ==========

DEFAULT_CONFIG = Path(__file__).parent / "matrix.yaml"
XIAOZHI_SRC = os.environ.get("XIAOZHI_SRC")


# ========== ユーティリティ ==========

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def find_serial_port() -> str:
    """接続中の ESP32 シリアルポートを自動検出。"""
    if sys.platform == "win32":
        # Windows: COM ポートの列挙は省略、手動指定を推奨
        return "COM7"
    # Linux / macOS
    for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*"]:
        from glob import glob
        ports = glob(pattern)
        if ports:
            return sorted(ports)[0]
    return "/dev/ttyUSB0"


# ========== sdkconfig 注入 ==========

LANG_KCONFIG_MAP = {
    "Chinese": "CONFIG_LANGUAGE_ZH_CN",
    "English": "CONFIG_LANGUAGE_EN_US",
    "Japanese": "CONFIG_LANGUAGE_JA_JP",
}

# sdkconfig.defaults 内の言語キーを検出するパターン
LANG_KEY_PATTERN = re.compile(r"^CONFIG_LANGUAGE_\w+=y$", re.MULTILINE)


def write_sdkconfig_overrides(board: dict, language: str, brand: dict, config: dict, src: Path) -> Path:
    """
    sdkconfig.defaults の末尾に上書きセクションを追記する。
    ESP-IDF は sdkconfig.defaults を先頭から読み、同一キーは後勝ちなので、
    末尾に追記するだけで安全に上書きできる。

    冪等性: 既存の「# --- Xiaozhi-Firmware-update overrides ---」ブロックを
    検出した場合はそのブロックを差し替える。
    """
    lang_key = LANG_KCONFIG_MAP.get(language)
    if not lang_key:
        raise ValueError(f"未対応の言語: {language}")

    override_lines = [
        "",
        "# --- Xiaozhi-Firmware-update overrides ---",
        f"{lang_key}=y",
        f'CONFIG_XIAOZHI_OTA_URL="{brand["ota_url"]}"',
        "# --- end overrides ---",
    ]

    sdkconfig_path = src / "sdkconfig.defaults"
    if not sdkconfig_path.exists():
        sdkconfig_path.write_text("", encoding="utf-8")

    content = sdkconfig_path.read_text(encoding="utf-8")

    # 既存のオーバーライドブロックを除去
    marker_start = "# --- Xiaozhi-Firmware-update overrides ---"
    marker_end = "# --- end overrides ---"
    if marker_start in content:
        before = content[:content.index(marker_start)].rstrip()
        after_idx = content.index(marker_end) + len(marker_end)
        after = content[after_idx:]
        content = before + after

    content = content.rstrip() + "\n" + "\n".join(override_lines) + "\n"
    sdkconfig_path.write_text(content, encoding="utf-8")

    print(f"  [sdkconfig] 言語={language}, OTA={brand['ota_url']}")
    return sdkconfig_path


def cleanup_sdkconfig_overrides(src: Path) -> None:
    """ビルド後にオーバーライドブロックを除去してクリーンに戻す。"""
    sdkconfig_path = src / "sdkconfig.defaults"
    if not sdkconfig_path.exists():
        return
    content = sdkconfig_path.read_text(encoding="utf-8")
    marker_start = "# --- Xiaozhi-Firmware-update overrides ---"
    marker_end = "# --- end overrides ---"
    if marker_start in content:
        before = content[:content.index(marker_start)].rstrip()
        after_idx = content.index(marker_end) + len(marker_end)
        after = content[after_idx:]
        content = (before + after).rstrip() + "\n"
        sdkconfig_path.write_text(content, encoding="utf-8")


# ========== ビルド実行 ==========

def run_idf(command: list[str], cwd: Path, dry_run: bool = False) -> None:
    cmd_str = " ".join(command)
    if dry_run:
        print(f"  [DRY-RUN] {cmd_str}")
        return
    print(f"  [RUN] {cmd_str}")
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"コマンド失敗 (exit {result.returncode}): {cmd_str}")


def build_one(board: dict, language: str, brand: dict, config: dict, dry_run: bool = False) -> dict:
    print(f"\n{'='*60}")
    print(f"  Building: {board['sku']} / {language} / {brand['name']}")
    print(f"{'='*60}")

    if not XIAOZHI_SRC:
        raise RuntimeError("環境変数 XIAOZHI_SRC に本家リポジトリのパスを設定してください")

    src = Path(XIAOZHI_SRC)
    if not src.exists():
        raise RuntimeError(f"本家リポジトリが見つかりません: {src}")

    project_root = Path(__file__).parent.parent

    # 1. sdkconfig.defaults に注入
    write_sdkconfig_overrides(board, language, brand, config, src)

    # 2. アセット注入（ロゴ・音声）
    sys.path.insert(0, str(Path(__file__).parent))
    from inject_assets import inject_all
    inject_all(board["sku"], brand["name"], language, dry_run=dry_run)

    # 3. ビルド
    if config["build_options"]["clean_before_build"]:
        run_idf(["idf.py", "fullclean"], cwd=src, dry_run=dry_run)

    # sdkconfig を削除して defaults から再生成させる
    sdkconfig = src / "sdkconfig"
    if sdkconfig.exists() and not dry_run:
        sdkconfig.unlink()

    run_idf(["idf.py", "set-target", board["target"]], cwd=src, dry_run=dry_run)
    run_idf(["idf.py", "build"], cwd=src, dry_run=dry_run)

    # 4. 成果物の配置
    out_path = project_root / config["output_pattern"].format(
        version=config["version"].lstrip("v"),
        board=board["sku"],
        lang=language.lower(),
        brand=brand["name"],
    )

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        built = src / "build" / "merged-binary.bin"
        if built.exists():
            shutil.copy(built, out_path)
            print(f"  [OK] 出力: {out_path}")
        else:
            print(f"  [WARN] ビルド成果物が見つかりません: {built}")
    else:
        print(f"  [DRY-RUN] 出力先: {out_path}")

    # 5. manifest.json 生成
    manifest = generate_manifest(out_path, board, language, brand, config)
    manifest_path = project_root / config["manifest_pattern"].format(
        version=config["version"].lstrip("v"),
        board=board["sku"],
        lang=language.lower(),
        brand=brand["name"],
    )

    if not dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [OK] manifest: {manifest_path}")
    else:
        print(f"  [DRY-RUN] manifest: {manifest_path}")

    # 6. クリーンアップ
    cleanup_sdkconfig_overrides(src)

    return {"board": board["sku"], "language": language, "brand": brand["name"], "success": True}


def generate_manifest(bin_path: Path, board: dict, language: str, brand: dict, config: dict) -> dict:
    return {
        "board_sku": board["sku"],
        "firmware_version": config["version"],
        "language": language,
        "brand": brand["name"],
        "ota_url": brand["ota_url"],
        "logo_hash": sha256_of_file(
            Path(__file__).parent.parent / "assets" / "logos" / board["sku"] / brand["name"]
        ) if (Path(__file__).parent.parent / "assets" / "logos" / board["sku"] / brand["name"]).exists() else None,
        "sound_hash": sha256_of_file(
            Path(__file__).parent.parent / "assets" / "sounds" / board["sku"] / brand["name"]
        ) if (Path(__file__).parent.parent / "assets" / "sounds" / board["sku"] / brand["name"]).exists() else None,
        "build_time": datetime.now().isoformat(),
        "builder": os.environ.get("GIT_USER_EMAIL", os.environ.get("USER", "unknown")),
        "idf_version": config["defaults"]["idf_version"],
        "source_commit": f"78/xiaozhi-esp32@{config['defaults']['xiaozhi_commit']}",
        "binary_sha256": sha256_of_file(bin_path) if bin_path.exists() else None,
        "build_os": sys.platform,
    }


# ========== メインループ ==========

def main() -> int:
    parser = argparse.ArgumentParser(description="Xiaozhi ファームウェア量産ビルド")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--board", help="単一ボードのみビルド")
    parser.add_argument("--lang", help="単一言語のみビルド (English / Japanese)")
    parser.add_argument("--brand", help="単一ブランドのみビルド (company / stock)")
    parser.add_argument("--all", action="store_true", help="全組合せビルド")
    parser.add_argument("--only-failed", action="store_true", help="前回失敗分のみリトライ")
    parser.add_argument("--dry-run", action="store_true", help="実際のビルドは行わず、設定を確認")
    args = parser.parse_args()

    if not any([args.all, args.board, args.lang, args.brand, args.only_failed]):
        parser.print_help()
        print("\n使用例:")
        print("  python build/build_matrix.py --board waveshare-esp32-s3-touch-lcd-1.85c --lang English")
        print("  python build/build_matrix.py --all")
        print("  python build/build_matrix.py --dry-run --all")
        return 2

    config = load_config(args.config)

    # only-failed: 前回の失敗ログから対象を取得
    failed_set = set()
    if args.only_failed:
        fail_log = Path("build-failures.log")
        if fail_log.exists():
            for entry in json.loads(fail_log.read_text(encoding="utf-8")):
                failed_set.add((entry["board"], entry["lang"], entry["brand"]))
        else:
            print("build-failures.log が見つかりません。")
            return 2

    results = []
    failures = []

    print(f"\n{'='*60}")
    print(f"  Xiaozhi ファームウェア量産ビルド")
    print(f"  バージョン: {config['version']}")
    print(f"  XIAOZHI_SRC: {XIAOZHI_SRC or '未設定'}")
    print(f"  OS: {sys.platform}")
    if args.dry_run:
        print(f"  モード: DRY-RUN（実ビルドなし）")
    print(f"{'='*60}")

    for board in config["boards"]:
        if not board.get("enabled"):
            continue
        if args.board and board["sku"] != args.board:
            continue

        for language in config["languages"]:
            if args.lang and language != args.lang:
                continue

            for brand_name, brand_cfg in config["brands"].items():
                if args.brand and brand_name != args.brand:
                    continue

                if args.only_failed and (board["sku"], language, brand_name) not in failed_set:
                    continue

                brand = {"name": brand_name, **brand_cfg}

                try:
                    result = build_one(board, language, brand, config, dry_run=args.dry_run)
                    results.append(result)
                except Exception as e:
                    print(f"  [FAIL] {e}")
                    failures.append({
                        "board": board["sku"],
                        "lang": language,
                        "brand": brand_name,
                        "error": str(e),
                        "time": datetime.now().isoformat(),
                    })
                    if config["build_options"]["fail_fast"]:
                        break

    # サマリ出力
    print(f"\n{'='*60}")
    print(f"  ビルド結果: 成功 {len(results)} / 失敗 {len(failures)}")
    print(f"{'='*60}")

    if failures:
        fail_log = Path("build-failures.log")
        fail_log.write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  失敗ログ: {fail_log}")
        for f in failures:
            print(f"    ✗ {f['board']} / {f['lang']} / {f['brand']}: {f['error']}")

    if results:
        for r in results:
            print(f"    ✓ {r['board']} / {r['language']} / {r['brand']}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
