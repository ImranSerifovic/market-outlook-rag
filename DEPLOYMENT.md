# Deployment Configuration

## Environment Variables Setup

### Vercel (Frontend) Environment Variables

Set the following in your Vercel project settings:

```
NEXT_PUBLIC_API_BASE=https://your-render-app.onrender.com
```

**Where to set it:**
1. Go to your Vercel project dashboard
2. Settings → Environment Variables
3. Add `NEXT_PUBLIC_API_BASE` with your Render backend URL (no trailing slash)

**Example:**
- If your Render service is at `https://market-outlook-api.onrender.com`
- Set `NEXT_PUBLIC_API_BASE=https://market-outlook-api.onrender.com`

---

### Render (Backend) Environment Variables

Set the following in your Render service settings:

```
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
```

**Where to set it:**
1. Go to your Render service dashboard
2. Environment tab
3. Add `ALLOWED_ORIGINS` with your Vercel frontend URL(s)

**Example:**
- If your Vercel app is at `https://market-outlook-rag.vercel.app`
- Set `ALLOWED_ORIGINS=https://market-outlook-rag.vercel.app,http://localhost:3000`
- (Include localhost for local development)

**Also make sure you have:**
```
OPENAI_API_KEY=your-openai-api-key
CHROMA_DIR=/path/to/chroma/storage  # Optional, defaults to storage/chroma
```

---

## Quick Checklist

- [ ] Render backend is deployed and accessible (test with `/health` endpoint)
- [ ] `NEXT_PUBLIC_API_BASE` is set in Vercel to your Render URL
- [ ] `ALLOWED_ORIGINS` is set in Render to your Vercel URL
- [ ] `OPENAI_API_KEY` is set in Render
- [ ] ChromaDB data is accessible on Render (if using persistent storage)
- [ ] Both services are redeployed after setting environment variables

---

## Testing

1. **Test Render backend directly:**
   ```bash
   curl https://your-render-app.onrender.com/health
   ```
   This will show:
   - Collection count (number of chunks indexed)
   - Pages in index (which pages are indexed)
   - Page range (e.g., "1-50" means pages 1-50 are indexed)

2. **Test from Vercel frontend:**
   - Open your Vercel app
   - Open browser DevTools → Network tab
   - Submit a question
   - Check if the request goes to your Render URL (not localhost)

3. **Check CORS errors:**
   - If you see CORS errors in the browser console, verify `ALLOWED_ORIGINS` includes your exact Vercel URL (no trailing slash)

---

## ChromaDB Index Issue

**Problem:** If you're only getting results from the first few pages, the ChromaDB index on Render might be incomplete or empty.

**Solution:** The Dockerfile now includes a startup script that automatically builds the index if it's missing. On first deployment (or if the index is deleted), it will:
1. Extract all pages from the PDF
2. Chunk and embed all content
3. Build the complete ChromaDB index
4. Then start the API server

**To verify the index is complete:**
1. Check the `/health` endpoint - it shows which pages are indexed
2. Look at Render logs during startup - you'll see "Building index..." if it's rebuilding
3. The index build takes a few minutes on first deploy

**Note:** The `storage/` directory is gitignored (correctly), so the index is built on Render during deployment.

