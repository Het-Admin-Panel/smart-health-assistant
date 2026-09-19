import os

print("=" * 55)
print("GEMINI DEBUG TOOL - shows the REAL problem")
print("=" * 55)

# ---- 1. Key file check ----
print("\n[1] gemini_key.txt check")
key = None
if os.path.exists("gemini_key.txt"):
    raw = open("gemini_key.txt", "rb").read()
    print("    Found. File size:", len(raw), "bytes")
    key = open("gemini_key.txt", encoding="utf-8-sig").read().strip()
    print("    Key length:", len(key), "chars | First 10 chars:", key[:10])
    if key[:10] == "AIzaSyAbCd":
        print("    !!! THIS IS THE FAKE EXAMPLE KEY FROM MY MESSAGE!")
        print("        Get your OWN key at https://aistudio.google.com")
    if not key.startswith("AIza"):
        print("    !!! Real keys start with 'AIza' - this looks wrong")
    if '"' in key or "'" in key:
        print("    !!! Quotes found in key - remove them!")
else:
    print("    NOT FOUND! Folder checked:", os.getcwd())

# ---- 2. Environment variable ----
env = os.environ.get("GEMINI_API_KEY", "").strip()
print("[2] Environment variable:", "set" if env else "not set")
if env and not key:
    key = env

if not key:
    print("\n>>> NO KEY FOUND ANYWHERE - that is the whole problem!")
    raise SystemExit

# ---- 3. Library check ----
print("\n[3] Library check")
try:
    import google.generativeai as genai
    print("    google.generativeai imported OK")
except ImportError:
    print("    MISSING! Run: pip install google-generativeai")
    raise SystemExit

# ---- 4. Was ai_doctor.py actually updated? ----
print("\n[4] ai_doctor.py version check")
try:
    import ai_doctor
    if hasattr(ai_doctor, "_load_key"):
        print("    UPDATED version - reads gemini_key.txt correctly")
    else:
        print("    !!! OLD VERSION - your _load_key edit was NOT applied!")
except Exception as e:
    print("    Could not import ai_doctor:", e)

# ---- 5. Connect to Google ----
print("\n[5] Connecting to Google API...")
genai.configure(api_key=key)
try:
    models = list(genai.list_models())
    names = [m.name for m in models
             if "generateContent" in getattr(m, "supported_generation_methods", [])]
    print("    CONNECTION OK! Available models:")
    for n in names[:8]:
        print("       ", n)
except Exception as e:
    print("    CONNECTION FAILED:", type(e).__name__)
    print("   ", str(e)[:200])

# ---- 6. The real generation test ----
print("\n[6] Generation test (moment of truth)")
for model in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]:
    try:
        r = genai.GenerativeModel(model).generate_content(
            "Reply with exactly one word: WORKING")
        print(f"    {model} -> SUCCESS: {(r.text or '').strip()}")
        print(f"\n>>> THIS MODEL WORKS - note it down!")
        break
    except Exception as e:
        print(f"    {model} -> FAILED: {type(e).__name__}: {str(e)[:130]}")

print("\n" + "=" * 55)
print("SEND THIS COMPLETE OUTPUT BACK FOR THE EXACT FIX")