"""
BIN ファイル内の OTA URL 設定を調べるインスペクタ。

patch_bin.py が「旧URL検出: 0 箇所」と出た場合、以下のいずれかを判別するために使う:
  1. すでに classism.net に patch 済み
  2. 最初から別ドメインで build された固件
  3. Partial dump でアプリ領域を読み取れていない

使い方:
    python inspect_ota.py <binファイル>

例:
    python inspect_ota.py test\\backup_full.bin

Exit code:
    0 : 正常（URL が検出された）
    1 : ファイル未存在 / 読み取り失敗 / URL 0 件（partial dump 疑い）
    2 : 使い方エラー
"""
import os
import re
import sys


# ---------- 定数 ----------
URL_REGEX = re.compile(rb"https?://[\x21-\x7e]+")
TRIM_CHARS = ".,;:)]}\"'>`<|^"

# Xiaozhi 固有の確認キーワード
KEYWORDS = [
    b"tenclass.net",     # 旧 OTA
    b"classism.net",     # 新 OTA
    b"xiaozhi",          # プロジェクト名
    b"ota_url",          # ESP-IDF config key
    b"CONFIG_OTA",       # ESP-IDF macro
    b"mqtt",             # MQTT endpoint
    b"websocket",        # WebSocket endpoint
    b"api.",             # API host 接頭辞
]


def extract_urls(data: bytes) -> dict:
    """BIN データから http(s):// URL を抽出。戻り値は {url: 最初の offset}。"""
    seen = {}
    for m in URL_REGEX.finditer(data):
        url = m.group().decode("ascii", errors="ignore").rstrip(TRIM_CHARS)
        # 極端に短い / 長いものは誤検出として除外
        if len(url) < 10 or len(url) > 512:
            continue
        if url not in seen:
            seen[url] = m.start()
    return seen


def print_header(bin_path: str, data: bytes) -> None:
    size_mb = len(data) / (1024 * 1024)
    print("=" * 60)
    print(f" 対象ファイル : {bin_path}")
    print(f" サイズ       : {len(data):,} bytes ({size_mb:.2f} MB)")
    print("=" * 60)
    print()


def print_ota_section(urls: dict) -> list:
    """OTA らしき URL を表示して、そのリストを返す。"""
    ota = [(o, u) for u, o in urls.items() if "ota" in u.lower()]
    ota.sort()
    if ota:
        print("=== 🎯 OTA らしき URL ===")
        for offset, url in ota:
            print(f"  [0x{offset:08x}] {url}")
    else:
        print("=== ⚠️ OTA を含む URL は見つかりませんでした ===")
    print()
    return ota


def print_all_urls(urls: dict) -> None:
    print(f"=== 全 URL 一覧（{len(urls)} 件） ===")
    if not urls:
        print("  （URL は検出されませんでした）")
    else:
        for url, offset in sorted(urls.items(), key=lambda x: x[1]):
            marker = "  ← OTA?" if "ota" in url.lower() else ""
            print(f"  [0x{offset:08x}] {url}{marker}")
    print()


def print_keywords(data: bytes) -> dict:
    """キーワード出現回数を表示。戻り値は {keyword_str: count}。"""
    print("=== キーワード出現箇所 ===")
    result = {}
    for kw in KEYWORDS:
        count = data.count(kw)
        result[kw.decode()] = count
        if count > 0:
            first = data.find(kw)
            print(f"  {kw.decode():15s} : {count:4d} 箇所（初出 0x{first:08x}）")
        else:
            print(f"  {kw.decode():15s} :    0 箇所")
    print()
    return result


def print_verdict(urls: dict, kw_counts: dict) -> int:
    """総合判定を表示。exit code を返す。"""
    print("=== 🔍 総合判定 ===")

    old_cnt = kw_counts.get("tenclass.net", 0)
    new_cnt = kw_counts.get("classism.net", 0)
    xiaozhi_cnt = kw_counts.get("xiaozhi", 0)

    if len(urls) == 0 and xiaozhi_cnt == 0:
        print("  ⚠️  URL もキーワードも検出されません。")
        print("      → Partial dump の可能性が高い。")
        print("      → `read-flash 0x0 0x1000000` で全 Flash を取り直してください。")
        return 1

    if old_cnt > 0 and new_cnt == 0:
        print(f"  🔴 旧 URL (tenclass.net) が {old_cnt} 箇所 残っています。")
        print("      → 未 patch 状態です。`python patch_bin.py <binファイル>` を実行してください。")
        return 0

    if old_cnt == 0 and new_cnt > 0:
        print(f"  ✅ 新 URL (classism.net) が {new_cnt} 箇所 検出されました。")
        print("      → すでに patch 済みです。追加 patch 不要、そのまま書き戻し可能。")
        return 0

    if old_cnt == 0 and new_cnt == 0:
        print("  🤔 tenclass.net も classism.net も見つかりません。")
        print("      → 別ドメインで build された固件の可能性。")
        print("      → 上の「OTA らしき URL」一覧を確認してください。")
        return 0

    # old > 0 かつ new > 0（稀だが混在ケース）
    print(f"  ⚠️  旧 URL {old_cnt} 箇所 / 新 URL {new_cnt} 箇所 が混在しています。")
    print("      → patch 途中で中断された可能性。再度 patch_bin.py を実行してください。")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("使用方法: python inspect_ota.py <binファイル>")
        return 2

    bin_path = sys.argv[1]

    if not os.path.isfile(bin_path):
        print(f"ファイルが見つかりません: {bin_path}")
        return 1

    try:
        with open(bin_path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"読み取り失敗: {e}")
        return 1

    if len(data) == 0:
        print("ファイルが空です。")
        return 1

    print_header(bin_path, data)
    urls = extract_urls(data)
    print_ota_section(urls)
    print_all_urls(urls)
    kw_counts = print_keywords(data)
    return print_verdict(urls, kw_counts)


if __name__ == "__main__":
    sys.exit(main())
