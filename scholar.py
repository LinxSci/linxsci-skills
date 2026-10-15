"""Compatibility entry point; prefer the linxsci_scholar package."""
from linxsci_scholar.scripts.scholar import main

if __name__ == "__main__":
    raise SystemExit(main())
