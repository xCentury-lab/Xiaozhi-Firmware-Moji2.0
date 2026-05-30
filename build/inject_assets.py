"""
アセット注入スクリプト
=====================================

ビルド前に、ボード × ブランド × 言語 に応じたアセット
（ロゴ・起動音・翻訳カスタマイズ）を本家リポジトリの所定パスへコピーする。

本家アセット構造（2026-04-18 調査済み）:
    main/assets/
    ├── common/                    # 言語共通アセット
    └── locales/                   # 言語別アセット
        ├── en-US/
        │   ├── language.json      # UI文字列（60+ エントリ）
        │   ├── activation.ogg     # 音声ファイル群
        │   └── ...
        ├── ja-JP/                 # 日本語（完全存在確認済み）
        └── zh-CN/

使い方（通常は build_matrix.py から呼ばれる）:
    from inject_assets import inject_all
    inject_all(board_sku="waveshare-esp32-s3-touch-lcd-1.85c",
               brand="company",
               language="English")

環境変数:
    XIAOZHI_SRC: 本家 xiaozhi-esp32 リポジトリのローカルパス
"""

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent  # Xiaozhi-Firmware-update/
XIAOZHI_SRC = os.environ.get("XIAOZHI_SRC")

# 本家リポジトリ内の言語アセットパス（Phase 0-A 調査結果）
LOCALES_SUBDIR = Path("main") / "assets" / "locales"


def _ensure_src() -> Path:
    src = XIAOZHI_SRC
    if not src:
        raise RuntimeError("環境変数 XIAOZHI_SRC に本家リポジトリのパスを設定してください")
    p = Path(src)
    if not p.exists():
        raise RuntimeError(f"本家リポジトリが見つかりません: {p}")
    return p


def _backup_if_exists(path: Path) -> None:
    """注入先に既存ファイルがあればバックアップ。"""
    if path.exists():
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(path, backup)


# ========== ロゴ注入 ==========

def inject_logo(board_sku: str, brand: str, dry_run: bool = False) -> None:
    """ボード・ブランド別のロゴをビルドツリーへコピー。"""
    if brand == "stock":
        print(f"  [logo] stock: 本家ロゴを使用（注入スキップ）")
        return

    src_dir = REPO_ROOT / "assets" / "logos" / board_sku / brand
    if not src_dir.exists():
        print(f"  [logo] 素材ディレクトリ未整備: {src_dir}（Phase 1-B で作成）")
        return

    logo_files = list(src_dir.glob("*.c")) + list(src_dir.glob("*.png"))
    if not logo_files:
        print(f"  [logo] 素材ファイルが空: {src_dir}")
        return

    xiaozhi_src = _ensure_src()
    # ロゴの注入先はボード別ディレクトリ
    dst_dir = xiaozhi_src / "main" / "boards" / board_sku
    if not dst_dir.exists():
        # ボード名の亜種を検索
        boards_dir = xiaozhi_src / "main" / "boards"
        if boards_dir.exists():
            candidates = [d for d in boards_dir.iterdir() if d.is_dir() and board_sku in d.name]
            if candidates:
                dst_dir = candidates[0]

    if dry_run:
        print(f"  [DRY-RUN logo] {src_dir} → {dst_dir}")
        return

    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in logo_files:
        dst = dst_dir / f.name
        _backup_if_exists(dst)
        shutil.copy2(f, dst)
        print(f"  [logo] {f.name} → {dst}")


# ========== 起動音注入 ==========

def inject_sound(board_sku: str, brand: str, dry_run: bool = False) -> None:
    """ボード・ブランド別の起動音をビルドツリーへコピー。"""
    if brand == "stock":
        print(f"  [sound] stock: 本家音声を使用（注入スキップ）")
        return

    src_dir = REPO_ROOT / "assets" / "sounds" / board_sku / brand
    if not src_dir.exists():
        print(f"  [sound] 素材ディレクトリ未整備: {src_dir}（Phase 1-C で作成）")
        return

    sound_files = list(src_dir.glob("*.ogg")) + list(src_dir.glob("*.wav")) + list(src_dir.glob("*.c"))
    if not sound_files:
        print(f"  [sound] 素材ファイルが空: {src_dir}")
        return

    xiaozhi_src = _ensure_src()
    # 音声の注入先は言語アセットと同じ locales ディレクトリ、またはボード別
    dst_dir = xiaozhi_src / "main" / "boards" / board_sku
    if not dst_dir.exists():
        boards_dir = xiaozhi_src / "main" / "boards"
        if boards_dir.exists():
            candidates = [d for d in boards_dir.iterdir() if d.is_dir() and board_sku in d.name]
            if candidates:
                dst_dir = candidates[0]

    if dry_run:
        print(f"  [DRY-RUN sound] {src_dir} → {dst_dir}")
        return

    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in sound_files:
        dst = dst_dir / f.name
        _backup_if_exists(dst)
        shutil.copy2(f, dst)
        print(f"  [sound] {f.name} → {dst}")


# ========== 翻訳カスタマイズ ==========

LANG_CODE_MAP = {
    "English": "en-US",
    "Japanese": "ja-JP",
    "Chinese": "zh-CN",
}


def inject_translations(board_sku: str, language: str, dry_run: bool = False) -> None:
    """
    言語アセットのカスタマイズ。

    en-US / ja-JP は本家に完全存在するため、通常はビルド時の Kconfig 選択だけで切替可能。
    カスタム翻訳（UI文字列の上書き）がある場合のみ、ここで language.json を差し替える。
    """
    lang_code = LANG_CODE_MAP.get(language)
    if not lang_code:
        raise ValueError(f"未対応の言語: {language}")

    # 本家の言語アセット存在確認
    xiaozhi_src = _ensure_src()
    upstream_locale = xiaozhi_src / LOCALES_SUBDIR / lang_code
    if upstream_locale.exists():
        print(f"  [translations] {language}: 本家の {lang_code}/ を使用")
    else:
        print(f"  [translations] WARNING: 本家に {lang_code}/ が見つかりません")

    # カスタム翻訳がある場合のみ上書き
    custom_dir = REPO_ROOT / "assets" / "translations" / lang_code
    if custom_dir.exists() and any(custom_dir.iterdir()):
        if dry_run:
            print(f"  [DRY-RUN translations] カスタム翻訳: {custom_dir} → {upstream_locale}")
            return

        for f in custom_dir.glob("*"):
            if f.is_file():
                dst = upstream_locale / f.name
                _backup_if_exists(dst)
                shutil.copy2(f, dst)
                print(f"  [translations] カスタム上書き: {f.name} → {dst}")
    else:
        print(f"  [translations] カスタム翻訳なし — 本家アセットをそのまま使用")


# ========== 一括注入 ==========

def inject_all(board_sku: str, brand: str, language: str, dry_run: bool = False) -> None:
    """build_matrix.py から呼ばれる一括エントリ。"""
    print(f"  [inject] board={board_sku} brand={brand} lang={language}")
    inject_logo(board_sku, brand, dry_run=dry_run)
    inject_sound(board_sku, brand, dry_run=dry_run)
    inject_translations(board_sku, language, dry_run=dry_run)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("使用方法: python inject_assets.py <board_sku> <brand> <language> [--dry-run]")
        sys.exit(2)
    dry = "--dry-run" in sys.argv
    inject_all(sys.argv[1], sys.argv[2], sys.argv[3], dry_run=dry)
