bin_path = "v2.0.3_esp32-s3-touch-lcd-1.85c\\merged-binary_patched.bin"

with open(bin_path, 'rb') as f:
    data = f.read()

if b'classism.net' in data:
    print("OK: 新URL確認")
else:
    print("NG: 新URLが見つからない")

if b'tenclass.net' not in data:
    print("OK: 旧URL消去確認")
else:
    print("NG: 旧URLが残っている")