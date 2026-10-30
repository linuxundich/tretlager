#!/usr/bin/env python3
"""F0-Spike: Einrichtungsschritte ohne Oberfläche ausführen und auf der Konsole protokollieren.
    flatpak run --command=tretlager-spike-setup de.linuxundich.Tretlager [Schritt-ID …]"""
import os
import sys

sys.path.insert(0, "/app/share/tretlager")
from tretlager.core import setup  # noqa: E402

wanted = set(sys.argv[1:])
if wanted:
    setup.STEPS[:] = [s for s in setup.STEPS if s.id in wanted]
print("Schritte:", [s.id for s in setup.STEPS], "WINEPREFIX:", setup.paths.PREFIX, flush=True)
ctx = setup.Context(progress=lambda st, pct, text: print(f"[{st} {pct:5.1f}%] {text}", flush=True),
                    log=lambda text: print("  " + text, flush=True))
ok = setup.run_setup(ctx, lambda i, st, t: print(f"=== {i}: {st} {t}", flush=True))
sys.exit(0 if ok else 1)
