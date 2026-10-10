import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 (such as Rupee ₹ symbol) on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is on python search path
backend_root = Path(__file__).resolve().parent.parent
load_dotenv(backend_root / ".env")
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.gemini_service import analyze_content

test_text = (
    "Congratulations! You've won ₹50,000. "
    "Pay ₹499 to claim your reward within 2 hours at "
    "https://sbi-reward-claim.example"
)

try:
    res = analyze_content(test_text)
    print("--- MANUAL GEMINI CONTENT ANALYSIS RESULT ---")
    print(f"Language: {res.language.name} ({res.language.code}), confidence={res.language.confidence}")
    print("\nExtracted Claims:")
    for c in res.claims:
        print(f"  - [{c.id}] ({c.claim_type} | {c.category}): \"{c.statement}\" (importance={c.importance}, confidence={c.confidence})")

    print("\nExtracted Entities:")
    for e in res.entities:
        print(f"  - {e.name} ({e.type}) | Context: \"{e.context}\" (confidence={e.confidence})")

    print("\nExtracted URLs:")
    for u in res.urls:
        print(f"  - URL: {u.url} | Domain: {u.domain} | Context: \"{u.context}\"")

    print("\nSuspicious Behavioral Signals:")
    for s in res.suspicious_signals:
        print(f"  - [{s.type}]: {s.description} | Evidence: \"{s.evidence}\" (confidence={s.confidence})")

except Exception as err:
    print(f"Manual test failed: {err.__class__.__name__}: {err}")
    sys.exit(1)
