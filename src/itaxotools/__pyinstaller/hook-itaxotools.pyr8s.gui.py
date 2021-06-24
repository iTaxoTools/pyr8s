# Include all package data

from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files('itaxotools.common.resources')

# Until pyinstaller is updated on pypi, this is required
import importlib.resources
path = importlib.resources.files('PySide6')
dir = 'plugins/platforms'
datas.append((str(path / dir), 'PySide6/' + dir))
