from __future__ import annotations

import shutil
from pathlib import Path


def copy_file(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src)
    dst_path = Path(dst)
    if not src_path.exists():
        raise FileNotFoundError(f"模板文件不存在：{src_path}")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_path, dst_path)

