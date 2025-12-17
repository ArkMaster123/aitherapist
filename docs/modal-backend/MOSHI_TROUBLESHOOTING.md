# Moshi Voice Chat Troubleshooting

## Connection Error: "Failed to connect to voice server"

This error means the frontend cannot connect to the Modal WebSocket endpoint.

## Quick Diagnostic Steps

### 1. Check Environment Variables

Make sure these are set in your `.env.local` file:

```bash
MODAL_USERNAME=your-modal-username
MODAL_APP_NAME=therapist-voice-chat
```

**Where to find your Modal username:**
- After running `modal setup`, it's shown in the terminal
- Or check: `modal token show` (look for the username in the output)
- Or check your Modal dashboard URL

### 2. Check if Modal App is Deployed

**First, activate your virtual environment:**
```bash
source venv/bin/activate  # Activate venv first!
cd modal-backend
modal app list
```

Look for an app named `therapist-voice-chat` with a function `moshi-web`.

### 3. Check if App is Running

```bash
modal app logs therapist-voice-chat
```

Or check the specific function:

```bash
modal function logs therapist-voice-chat::moshi-web
```

### 4. Verify the WebSocket URL

The frontend constructs the URL as:
```
wss://${MODAL_USERNAME}--${MODAL_APP_NAME}-moshi-web.modal.run/ws
```

Example:
```
wss://your-username--therapist-voice-chat-moshi-web.modal.run/ws
```

You can test this URL directly:
```bash
# Check if endpoint is accessible
curl https://your-username--therapist-voice-chat-moshi-web.modal.run/status
```

Should return HTTP 200 if the app is running.

## Fixes

### Fix 1: Deploy the Modal App

If the app is not deployed:

```bash
# Activate venv first!
source venv/bin/activate
cd modal-backend
modal deploy -m src.moshi
```

**Important:** Always activate your venv before running Modal commands!

This will output a URL like:
```
✓ Created objects.
✓ Deployed function therapist-voice-chat::moshi-web

https://your-username--therapist-voice-chat-moshi-web.modal.run
```

**Important:** Note your Modal username from the deployment output.

### Fix 2: Redeploy if Already Deployed

If the app exists but isn't working, redeploy:

```bash
# Activate venv first!
source venv/bin/activate
cd modal-backend
modal deploy -m src.moshi --force
```

### Fix 3: Check Modal Authentication

Make sure you're authenticated:

```bash
source venv/bin/activate  # Activate venv first!
modal token show
```

If not authenticated:
```bash
source venv/bin/activate
modal setup
modal token new
```

### Fix 4: Verify Environment Variables in Frontend

Check that your Next.js app can access the variables:

```bash
# In your Next.js app directory
cat .env.local | grep MODAL
```

Make sure they're set correctly (no extra spaces, correct values).

### Fix 5: Test the Endpoint Manually

Test if the Modal endpoint is accessible:

```bash
# Replace with your actual values
curl https://your-username--therapist-voice-chat-moshi-web.modal.run/status
```

Should return:
```json
{"status": "ok"}
```

If you get 404 or connection refused, the app is not deployed or not running.

### Fix 6: Check Browser Console

Open browser DevTools (F12) → Console tab, and look for WebSocket connection errors:

```
WebSocket connection to 'wss://...' failed
```

This will show the actual URL being used and the specific error.

## Common Issues

### Issue: "Modal username not configured"

**Solution:** Set `MODAL_USERNAME` in `.env.local`

### Issue: "Connection refused" or "404 Not Found"

**Cause:** Modal app is not deployed or wrong URL

**Solution:**
1. Deploy: `cd modal-backend && modal deploy -m src.moshi`
2. Check the deployment output for the correct URL
3. Verify `MODAL_USERNAME` matches your actual username

### Issue: WebSocket connects but immediately disconnects

**Cause:** Modal app crashed or model loading failed

**Solution:**
1. Check Modal logs: `modal app logs therapist-voice-chat`
2. Look for Python errors or model loading failures
3. Redeploy: `modal deploy -m src.moshi --force`

### Issue: Works locally but not in production (Vercel)

**Cause:** Environment variables not set in Vercel

**Solution:**
1. Go to Vercel dashboard → Your project → Settings → Environment Variables
2. Add:
   - `MODAL_USERNAME` = your-modal-username
   - `MODAL_APP_NAME` = therapist-voice-chat
3. Redeploy on Vercel

## Verification Steps

After deploying, verify everything works:

### Step 1: Check App Status
```bash
cd modal-backend
modal app list | grep therapist-voice-chat
```

### Step 2: Test HTTP Endpoint
```bash
curl https://your-username--therapist-voice-chat-moshi-web.modal.run/status
```

Should return HTTP 200.

### Step 3: Test from Frontend
1. Start your Next.js app: `npm run dev`
2. Visit: `http://localhost:3000/voice`
3. Click "Start Session"
4. Check browser console for errors
5. Check Modal logs: `modal app logs therapist-voice-chat --follow`

## Modal App Status Commands

```bash
# List all apps
modal app list

# Show app details
modal app show therapist-voice-chat

# View logs
modal app logs therapist-voice-chat --follow

# Restart app (redeploy)
modal deploy -m src.moshi --force
```

## Still Not Working?

1. **Check Modal Dashboard**: https://modal.com/apps
   - Look for `therapist-voice-chat` app
   - Check if it's running or has errors

2. **Check Deployment Output**: When you ran `modal deploy -m src.moshi`, did it succeed?
   - Look for errors in the terminal output
   - Note the exact URL it created

3. **Check Network Tab**: In browser DevTools → Network tab
   - Filter by WS (WebSocket)
   - See the actual connection attempt
   - Check status code and error messages

4. **Check Modal Logs**: 
   ```bash
   modal app logs therapist-voice-chat --follow
   ```
   - Connect from frontend
   - Watch logs for errors or connection attempts

## Quick Redeploy Script

Create `modal-backend/redeploy-moshi.sh`:

```bash
#!/bin/bash
# Activate venv from project root
cd "$(dirname "$0")/.."
source venv/bin/activate

# Deploy
cd modal-backend
echo "Redeploying Moshi voice chat..."
modal deploy -m src.moshi --force
echo "Done! Check the output above for the WebSocket URL."
```

Make it executable:
```bash
chmod +x modal-backend/redeploy-moshi.sh
```

Run it:
```bash
./modal-backend/redeploy-moshi.sh
```

## Important: Always Activate venv First!

**Before running any Modal commands, always activate your virtual environment:**

```bash
# From project root
source venv/bin/activate

# Then run Modal commands
cd modal-backend
modal deploy -m src.moshi
modal app list
modal app logs therapist-voice-chat
```

