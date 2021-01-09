# zip_import

- 推荐(最新的版本)

```bash
pip install https://github.com/cn-kali-team/zip_import/archive/master.zip
```

- 内存加载Python模块

```python
import io
import sys
import zipfile
from zip_import import ZipPathFinder


def _get_zip(path, password=None):
    with open(path, "rb") as f:
        zip_bytes = io.BytesIO(f.read())
        zip_instantiation = zipfile.ZipFile(zip_bytes)
        if password is not None:
            zip_instantiation.setpassword(pwd=bytes(str(password), 'utf-8'))
        return zip_instantiation


sys.meta_path.append(
    ZipPathFinder(zip_path='zip://pocsuite3.zip', zip_ins=_get_zip(path='pocsuite3.zip', password="11")))
import pocsuite3

print(dir(pocsuite3))
```

- zip_path随意字符串，zip_ins是zipfile.ZipFile返回的实例化对象