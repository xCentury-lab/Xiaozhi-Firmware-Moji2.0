import sys, os

OLD_URL = b'https://api.tenclass.net/xiaozhi/ota/'
NEW_URL = b'https://classism.net/xiaozhi/ota/'
NEW_URL_PADDED = NEW_URL.ljust(len(OLD_URL), b'\x00')

if len(sys.argv) < 2:
    print("使用方法: python patch_bin.py <binファイル>")
    sys.exit(1)

bin_path = sys.argv[1]

if not os.path.isfile(bin_path):
    print(f"ファイルが見つかりません: {bin_path}")
    sys.exit(1)

with open(bin_path, 'rb') as f:
    data = f.read()

count = data.count(OLD_URL)
print(f"旧URL検出: {count} 箇所")

if count == 0:
    print("NG: 旧URLが見つかりません")
    sys.exit(1)

patched = data.replace(OLD_URL, NEW_URL_PADDED)

# 出力ファイル名を生成
base, ext = os.path.splitext(bin_path)
out_path = base + "_patched" + ext

with open(out_path, 'wb') as f:
    f.write(patched)

# 確認
if b'classism.net' in patched and b'tenclass.net' not in patched:
    print("OK: 新URL確認")
    print("OK: 旧URL消去確認")
else:
    print("NG: 確認失敗")
    sys.exit(1)

print(f"\n出力: {out_path}")
print("完成!")