import zipfile

zip_path = "v2.2.4_waveshare-esp32-s3-touch-lcd-1.85c_patched.zip"

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open("merged-binary.bin") as f:
        data = f.read()

if b'classism.net' in data:
    print("OK: 新URL確認")
else:
    print("NG: 新URLが見つからない")

if b'tenclass.net' not in data:
    print("OK: 旧URL消去確認")
else:
    print("NG: 旧URLが残っている")