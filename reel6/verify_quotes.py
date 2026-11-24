"""Check every quote against the manuscript text, word for word (whitespace is ignored, nothing else).
Also checks each tile has 8 words or fewer.   python3 verify_quotes.py book.txt"""
import re, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from quotes_data import GROUPS
norm = lambda s: re.sub(r"\s+", " ", s).strip()
book = norm(open(sys.argv[1], encoding="utf-8").read())
bad = 0; n = 0
for g, items in GROUPS:
    for qid, ch, tiles, note in items:
        n += 1
        text = norm(" ".join(tiles))
        ok = text in book
        long_tiles = [t for t in tiles if len(t.split()) > 8]
        if not ok or long_tiles:
            bad += 1
            print("FAIL", qid, "NOT IN BOOK" if not ok else "", "TILE >8 WORDS: %s" % long_tiles if long_tiles else "")
            print("    ", text)
print("%d quotes checked, %d problems" % (n, bad))
sys.exit(1 if bad else 0)
