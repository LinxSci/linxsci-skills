"""Compatibility entry point; prefer the linxsci package."""
from linxsci.scripts.scholar import main

if __name__ == "__main__":
    raise SystemExit(main())
