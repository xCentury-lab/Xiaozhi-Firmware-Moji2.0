"""
ビルド成果物検証スクリプト
=====================================

ビルドマトリクスで生成された merged-binary.bin が
量産出荷基準を満たしているか自動検証する。

検証項目:
    1. ファイルサイズが想定範囲内
    2. OTA URL が classism.net（または指定URL）になっている
    3. 旧URL (tenclass.net) が残っていない
    4. 言語別の必須キーワード文字列が含まれる
    5. manifest.json が全フィールド充足
    6. binary_sha256 がファイル実体と一致

使い方:
    # 単一ファイル検証
    python build/verify_build.py firmware/v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_en_company/merged-binary.bin

    # ディレクトリ内全 bin 検証
    python build/verify_build.py --all firmware/

終了コード:
    0 = 全件合格
    1 = 1件以上不合格
    2 = 使い方エラー

関連ツール:
    - tools/inspect_ota.py  より詳細なURL/キーワード抽出
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml が必要です: pip install pyyaml")


DEFAULT_CONFIG = Path(__file__).parent / "matrix.yaml"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def verify_one(bin_path: Path, config: dict) -> tuple[bool, list[str]]:
    """1ファイルを検証。(passed, messages) を返す。"""
    errors: list[str] = []
    warnings: list[str] = []

    if not bin_path.is_file():
        return False, [f"ファイルが存在しません: {bin_path}"]

    data = bin_path.read_bytes()
    size_mb = len(data) / (1024 * 1024)

    qa = config["qa"]

    # 1. サイズ検証
    if not (qa["expected_size_min_mb"] <= size_mb <= qa["expected_size_max_mb"]):
        errors.append(
            f"サイズ逸脱: {size_mb:.2f} MB "
            f"(想定 {qa['expected_size_min_mb']}〜{qa['expected_size_max_mb']} MB)"
        )

    # 2. OTA URL 検証
    required_url = qa["required_ota_url"].encode()
    if required_url not in data:
        errors.append(f"必須OTA URL '{qa['required_ota_url']}' が見つかりません")

    # 3. 旧URL残存チェック
    for forbidden in qa["forbidden_strings"]:
        if forbidden.encode() in data:
            errors.append(f"禁止文字列 '{forbidden}' がバイナリ内に残存")

    # 4. 言語別必須キーワード
    # manifest.json から language を取得
    manifest_path = bin_path.parent / "manifest.json"
    language = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        language = manifest.get("language")
    else:
        warnings.append(f"manifest.json が見つかりません: {manifest_path}")

    if language and language in qa["required_strings"]:
        for kw in qa["required_strings"][language]:
            # 日本語の場合は UTF-8 でエンコード
            kw_bytes = kw.encode("utf-8")
            if kw_bytes not in data:
                errors.append(
                    f"言語 '{language}' の必須キーワード '{kw}' が含まれない"
                )

    # 5. manifest.json 必須フィールド
    if manifest_path.exists():
        required_fields = [
            "board_sku", "firmware_version", "language", "brand",
            "ota_url", "build_time", "idf_version", "binary_sha256"
        ]
        for field in required_fields:
            if field not in manifest or not manifest[field]:
                errors.append(f"manifest.json に必須フィールド '{field}' が欠落")

        # 6. SHA256 照合
        if manifest.get("binary_sha256"):
            actual = sha256_of_file(bin_path)
            if actual != manifest["binary_sha256"]:
                errors.append(
                    f"binary_sha256 不一致: manifest={manifest['binary_sha256']}, actual={actual}"
                )

    passed = len(errors) == 0
    messages = [f"[ERROR] {e}" for e in errors] + [f"[WARN]  {w}" for w in warnings]
    return passed, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="ビルド成果物検証")
    parser.add_argument("target", type=Path, help="検証対象の .bin または ディレクトリ")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--all", action="store_true", help="ディレクトリ内の全 bin を検証")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))

    targets: list[Path] = []
    if args.target.is_dir() or args.all:
        targets = sorted(args.target.rglob("merged-binary.bin"))
    else:
        targets = [args.target]

    if not targets:
        print(f"検証対象が見つかりません: {args.target}")
        return 2

    total_pass = 0
    total_fail = 0

    for bin_path in targets:
        print("=" * 60)
        print(f"検証: {bin_path}")
        passed, messages = verify_one(bin_path, config)
        for msg in messages:
            print(f"  {msg}")
        print(f"  結果: {'✅ PASS' if passed else '❌ FAIL'}")
        if passed:
            total_pass += 1
        else:
            total_fail += 1

    print("=" * 60)
    print(f"合計: PASS {total_pass} / FAIL {total_fail}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
