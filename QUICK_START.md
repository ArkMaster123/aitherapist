# Quick Start Guide

## Local Development

1. **Run setup**:
```bash
./setup.sh
```

2. **Configure environment**:
   - Edit `.env.local`
   - Set `AI_MODEL=openai/gpt-4o-mini` (or your preferred model)

3. **Start development server**:
```bash
npm run dev
```

4. **Open browser**:
   - Navigate to `http://localhost:3000`

## Before Committing to GitHub

1. **Check for secrets**:
```bash
./check-secrets.sh
```

2. **Verify no sensitive files**:
```bash
git status
# Ensure .env.local is NOT staged
```

3. **Commit and push**:
```bash
git add .
git commit -m "Your commit message"
git push
```

## Deploy to Vercel

1. **Push to GitHub** (see above)

2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repo

3. **Add environment variables** in Vercel dashboard:
   - `AI_MODEL`: `openai/gpt-4o-mini` (or your preferred model)

4. **Deploy!** Vercel will automatically build and deploy.

## Rate Limiting

- **Client-side**: 10 messages per 24 hours (uses localStorage)
- **Server-side**: Ready for Vercel KV (optional, see `app/api/chat/route.ts`)

## Project Structure

- `app/` - Next.js app directory
- `components/` - React components
- `lib/` - Utilities (rate limiting, etc.)
- `scripts/` - Python scripts (legacy, not used in web app)
- `docs/` - Documentation files

## Troubleshooting

**Build fails?**
- Run `npm install` again
- Check Node.js version (need 18+)

**Rate limiting not working?**
- Check browser console for errors
- Verify localStorage is enabled

**AI not responding?**
- Check `AI_MODEL` environment variable
- Verify AI SDK is properly configured
- Check Vercel function logs

