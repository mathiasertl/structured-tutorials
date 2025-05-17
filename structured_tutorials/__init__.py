from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("structured-tutorials")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "not-installed"
