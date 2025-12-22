from pypdf import PdfReader
import json
import os
import time

# #region agent log
LOG_PATH = "/Users/imranserifovic/market-outlook-rag/.cursor/debug.log"
# #endregion

def extract_pages(pdf_path: str):
    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:11", "message": "extract_pages entry", "data": {"pdf_path": pdf_path}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:16", "message": "Before PdfReader", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    reader = PdfReader(pdf_path)
    # #region agent log
    try:
        num_pages = len(reader.pages)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "pdf_parse.py:23", "message": "PDF reader created", "data": {"num_pages": num_pages}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception as e:
        try:
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:26", "message": "Error getting page count", "data": {"error": str(e)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        raise
    # #endregion
    
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        # #region agent log
        try:
            if i % 10 == 0 or i == 1:
                with open(LOG_PATH, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:33", "message": "Processing page", "data": {"page_num": i, "pages_list_len": len(pages)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        text = page.extract_text() or ""
        # #region agent log
        try:
            text_len = len(text)
            if i % 10 == 0 or i == 1:
                with open(LOG_PATH, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:40", "message": "Page text extracted", "data": {"page_num": i, "text_length": text_len}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        pages.append({"page": i, "text": text})
    
    # #region agent log
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "pdf_parse.py:47", "message": "extract_pages exit", "data": {"total_pages": len(pages)}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    return pages