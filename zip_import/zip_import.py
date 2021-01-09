import sys
import types
from importlib.abc import SourceLoader, PathEntryFinder
from importlib.machinery import ModuleSpec


# 加载单文件
class ModuleLoader(SourceLoader):
    def __init__(self, zip_ins, zip_path):
        self.zip_path = zip_path
        self._zip = zip_ins
        self._source_cache = {}

    def create_module(self, spec):
        """这边只要调用父类的实现即可."""

        mod = sys.modules.setdefault(spec.name, types.ModuleType(spec.name))
        mod.__file__ = self.get_filename(spec.name)
        mod.__loader__ = self
        mod.__package__ = spec.name.rpartition('.')[0]
        return mod

    def exec_module(self, module):
        """在_post_import_hooks中查找对应模块中的回调函数并执行."""
        code = self.get_code(module.__name__)
        exec(code, module.__dict__)

    def _get_zip_code(self, filename):
        zip_path_c = self._zip.comment.decode()
        return self._zip.open(filename[len(zip_path_c) + 1:]).read().decode('utf-8')

    def get_code(self, fullname):
        src = self.get_source(fullname)
        return compile(src, self.get_filename(fullname), 'exec')

    def get_data(self, path):
        pass

    def get_filename(self, fullname):
        return self.zip_path + '.py'

    def get_source(self, fullname):
        filename = self.get_filename(fullname)
        if filename in self._source_cache:
            return self._source_cache[filename]
        try:
            source = self._get_zip_code(filename)
            self._source_cache[filename] = source
            return source
        except KeyError as e:
            raise ImportError("Can't load %s" % filename)

    def is_package(self, fullname):
        return False


# 加载库
class PackageLoader(ModuleLoader):
    def create_module(self, spec):
        mod = super().create_module(spec)
        mod.__path__ = [self.zip_path]
        mod.__package__ = spec.name
        return mod

    def get_filename(self, fullname):
        return self.zip_path + '/' + '__init__.py'

    def is_package(self, fullname):
        return True


class ZipPathFinder(PathEntryFinder):
    """查找zip中的模块."""

    def __init__(self, zip_path: str, zip_ins):
        self._paths = None
        self._zip_path = zip_path
        zip_ins.comment = zip_path.encode()
        self._zip = zip_ins

    def find_spec(self, fullname, paths=None, target=None):
        if self._paths is None:
            self._paths = []
            self._paths = self._zip.namelist()
        spec = None
        if fullname.replace(".", "/") + '/__init__.py' in self._paths:
            full_uri = self._zip_path + '/' + fullname.replace(".", "/")
            try:
                loader = PackageLoader(self._zip, full_uri)
                loader.load_module(fullname)
                spec = ModuleSpec(fullname, loader, origin=paths)
            except ImportError as ie:
                spec = None
            except Exception as e:
                spec = None
        elif fullname.replace(".", "/") + '.py' in self._paths:
            full_uri = self._zip_path + '/' + fullname.replace(".", "/")
            try:
                loader = ModuleLoader(self._zip, full_uri)
                spec = ModuleSpec(fullname, loader, origin=paths)
            except ImportError as ie:
                spec = None
            except Exception as e:
                spec = None
        else:
            pass
        return spec

    def invalidate_caches(self):
        # warnings.warn("invalidating link cache", UserWarning)
        self._paths = None

# import 某个模块
#         |
#         |
#   遍历sys.meta_path
#         |
#         |---有执行<finder>.find_spec()后返回非None的---------|
#         |                                                 |- 使用<finder>.find_spec()返回的spec对象生成模块
# 执行<finder>.find_spec()后返回的都为None
#         |
#         |
# 遍历sys.path
#         |
#         |
# 检查sys.path_importer_cache上有没有各个path对应的finder缓存--有finder缓存---|
#         |                                                              |-使用<finder>.find_spec()返回的spec对象生成模块
#         |
#     没有缓存
#         |
#     遍历sys.path_hooks
#         |
#   执行其中的可执行对象,直到获得返回值为finder的终止 --------------------|
#         |                                                        |-将这个finder设为这个path的缓存finder
#         |                                                        |
#         |                                                        |-使用<finder>.find_spec()返回的spec对象生成模块
#   没有一个找到finder-----抛出ModuleNotFoundError
