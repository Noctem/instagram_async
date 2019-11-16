# flake8: noqa
# pylint: disable=unused-import

try:
    from orjson import dumps as _jdumps, loads as jloads

    def jdumps(obj):
        """orjdumps converted to str"""
        return _jdumps(obj).decode()

    def jdump(obj, fp):
        """helper to write to file since orjson lacks that functionality"""
        fp.write(jdumps(obj))

    def jload(fp):
        """helper to read from file since orjson lacks that functionality"""
        return jloads(fp.read())
except ImportError:
    # fallback to (slower) standard library json if orjson is not found
    from functools import partial
    from json import dump as _jdump, dumps as _jdumps, load as jload, loads as jloads

    jdump = partial(_jdump, indent=4, sort_keys=True, ensure_ascii=False)
    jdumps = partial(_jdumps, separators=(',', ':'))  # compact encoding
