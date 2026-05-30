# patches/

本家 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) に対する改変を git format-patch 形式で保存するディレクトリ。

## 現状

**現在パッチなし** (2026-05-24 軸定義変更により、ブートロゴ "和合" 注入パッチを廃止)。

## 目的 (将来再導入時の参考)

- 本家ソースツリー（`XIAOZHI_SRC`）は upstream のままに保ち、本プロジェクトはパッチのみを追跡
- `.claude/skills/xiaozhi-build` は正規表現で冪等に同等の改変を再適用可能
- パッチファイルは **人間がレビュー・引継ぎ・再現する際の正典**として機能

## 適用手順 (パッチがある場合)

```bash
cd $XIAOZHI_SRC
git apply /home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-VoCat/patches/<patch-name>.patch
```

## 再生成手順 (パッチを新規作成する場合)

```bash
cd $XIAOZHI_SRC
git diff HEAD -- <path> > \
    /home/user/project/xiaozhi-work-firmware/Xiaozhi-Firmware-VoCat/patches/<patch-name>.patch
```

## 廃止履歴

| 日付 | パッチ | 廃止理由 |
|---|---|---|
| 2026-05-24 | `xiaozhi-esp32-v2.2.4-wahe-logo.patch` | ブートロゴ "和合" 軸自体を削除 (ESP-VoCat は emote::EmoteDisplay 主体でロゴ非表示) |
