import sys, os, zipfile, tempfile, urllib.request

OLD_URL = b'https://api.tenclass.net/xiaozhi/ota/'
NEW_URL = b'https://classism.net/xiaozhi/ota/'
NEW_URL_PADDED = NEW_URL.ljust(len(OLD_URL), b'\x00')

def patch_bin(data):
    count = data.count(OLD_URL)
    if count == 0:
        return data, 0
    return data.replace(OLD_URL, NEW_URL_PADDED), count

def process(zip_path):
    print("=" * 60)
    print("小智 Release 固件 OTA 替換")
    print(f"  旧: {OLD_URL.decode()}")
    print(f"  新: {NEW_URL.decode()}")
    print("=" * 60)

    base = os.path.splitext(zip_path)[0]
    out_zip = base + "_patched.zip"

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zin:
            zin.extractall(tmpdir)

        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root, dirs, files in os.walk(tmpdir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    with open(fpath, 'rb') as f:
                        data = f.read()
                    arcname = os.path.relpath(fpath, tmpdir)
                    if fname.endswith('.bin'):
                        patched, count = patch_bin(data)
                        new_count = patched.count(NEW_URL)
                        old_remain = patched.count(OLD_URL)
                        status = "OK" if count > 0 and old_remain == 0 else "WARNING"
                        print(f"  [{fname}] 替換 {count} 処 | 新URL {new_count} | 残留旧URL {old_remain}  {status}")
                        zout.writestr(arcname, patched)
                    else:
                        zout.writestr(arcname, data)

    print(f"\n出力: {out_zip}")
    print("完成!")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python patch_release_zip.py <zipファイル>")
        sys.exit(1)
    arg = sys.argv[1]
    if arg.startswith('http'):
        print(f"ダウンロード中: {arg}")
        fname = arg.split('/')[-1]
        urllib.request.urlretrieve(arg, fname)
        arg = fname
    process(arg)