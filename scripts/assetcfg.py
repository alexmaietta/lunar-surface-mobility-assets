import importlib.util
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.path.join(ROOT, "families") not in sys.path:
    sys.path.append(os.path.join(ROOT, "families"))


def load(asset_id):
    path = os.path.join(ROOT, "configs", f"{asset_id}.py")
    spec = importlib.util.spec_from_file_location(f"cfg_{asset_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_dir(asset_id, *parts):
    d = os.path.join(ROOT, "build", asset_id, *parts)
    os.makedirs(d if not os.path.splitext(d)[1] else os.path.dirname(d), exist_ok=True)
    return d


def arg(argv, name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


def version():
    with open(os.path.join(ROOT, "VERSION")) as f:
        return f.read().strip()


def asset_dir(cfg, *parts):
    return os.path.join(ROOT, "assets", cfg.ASSET_PATH, *parts)
