# Deployment Guide

## Pre-Commit Checklist

Before committing to GitHub, make sure to:

1. **Run the secrets checker**:
```bash
./check-secrets.sh
```

2. **Verify no sensitive files are tracked**:
```bash
git status
# Make sure .env, .env.local, and any files with secrets are not staged
```

3. **Test the build locally**:
```bash
npm install
npm run build
```

## GitHub Setup

1. **Initialize git repository** (if not already done):
```bash
git init
```

2. **Add all files**:
```bash
git add .
```

3. **Check for secrets one last time**:
```bash
./check-secrets.sh
```

4. **Create initial commit**:
```bash
git commit -m "Initial commit: Terminal chat app with rate limiting"
```

5. **Create GitHub repository** and push:
```bash
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

## Vercel Deployment

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**

2. **Click "Add New Project"**

3. **Import your GitHub repository**

4. **Configure environment variables**:
   - Go to Project Settings → Environment Variables
   - Add `AI_MODEL` (e.g., `openai/gpt-4o-mini`)
   - Optionally add `KV_REST_API_URL` and `KV_REST_API_TOKEN` for server-side rate limiting

5. **Deploy!**
   - Vercel will automatically detect Next.js
   - Build command: `npm run build`
   - Output directory: `.next`
   - Install command: `npm install`

## Environment Variables in Vercel

Required:
- `AI_MODEL`: The AI model to use (defaults to `openai/gpt-4o-mini`)

Optional (for server-side rate limiting):
- `KV_REST_API_URL`: Vercel KV REST API URL
- `KV_REST_API_TOKEN`: Vercel KV REST API token

## Project Structure

```
.
├── app/                    # Next.js app directory
│   ├── api/chat/          # Chat API endpoint
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── terminal-chat.tsx  # Main chat component
│   ├── terminal-input.tsx # Input component
│   └── terminal-output.tsx # Output component
├── lib/                   # Utilities
│   └── rate-limit.ts      # Rate limiting logic
├── scripts/               # Python scripts (legacy)
├── docs/                  # Documentation files
└── public/                # Static assets
```

## Post-Deployment

After deployment:
1. Test the app at your Vercel URL
2. Verify rate limiting works (try sending 11 messages)
3. Check that AI responses are streaming correctly
4. Monitor Vercel logs for any errors

## Troubleshooting

### Build fails
- Check that all dependencies are in `package.json`
- Verify Node.js version (should be 18+)
- Check build logs in Vercel dashboard

### Rate limiting not working
- Verify client-side rate limiting is enabled
- For server-side, ensure Vercel KV is configured

### AI responses not working
- Check `AI_MODEL` environment variable is set
- Verify AI SDK is properly configured
- Check API logs in Vercel dashboard

