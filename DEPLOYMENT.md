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

2. **Test from Vercel frontend:**
   - Open your Vercel app
   - Open browser DevTools → Network tab
   - Submit a question
   - Check if the request goes to your Render URL (not localhost)

3. **Check CORS errors:**
   - If you see CORS errors in the browser console, verify `ALLOWED_ORIGINS` includes your exact Vercel URL (no trailing slash)

