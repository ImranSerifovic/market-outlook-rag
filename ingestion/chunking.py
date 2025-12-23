import re
import json
import os
import time
from pathlib import Path

# #region agent log
# Write logs to a safe location in any environment (override via MOA_LOG_PATH if desired)
_DEFAULT_LOG = Path(os.getenv("TMPDIR", "/tmp")) / "market_outlook_debug.log"
LOG_PATH = os.getenv("MOA_LOG_PATH", str(_DEFAULT_LOG))
# Ensure log directory exists
try:
    Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # If we can't create the directory, logging will just fail silently
# #endregion

def chunk_text(text: str, max_chars: int = 1800, overlap: int = 250):
    # #region agent log
    try:
        text_len = len(text)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "chunking.py:11", "message": "chunk_text entry", "data": {"text_length": text_len, "max_chars": max_chars}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        # #region agent log
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "chunking.py:18", "message": "chunk_text empty text", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        return []
    chunks = []
    start = 0
    iterations = 0
    while start < len(text):
        iterations += 1
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        
        # If we've reached the end of the text, break to avoid infinite loop
        if end >= len(text):
            break
            
        # Calculate next start position with overlap
        next_start = end - overlap
        # Ensure we always make progress (next_start must be > start)
        if next_start <= start:
            next_start = start + 1
        start = next_start
        
        # #region agent log
        try:
            if iterations > 1000:
                with open(LOG_PATH, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "chunking.py:37", "message": "chunking loop excessive iterations", "data": {"iterations": iterations, "start": start, "text_len": len(text)}, "timestamp": int(time.time() * 1000)}) + "\n")
                break
        except: pass
        # #endregion
    
    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "chunking.py:36", "message": "chunk_text exit", "data": {"num_chunks": len(chunks)}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    return chunks