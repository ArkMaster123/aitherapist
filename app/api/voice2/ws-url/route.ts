import { NextResponse } from 'next/server';

export async function GET() {
  // Get Modal config from server-side env vars (prefer MODAL_* over NEXT_PUBLIC_* for security)
  const modalAppName = process.env.MODAL_CHATTERBOX_APP_NAME || process.env.NEXT_PUBLIC_MODAL_CHATTERBOX_APP_NAME || 'chatterbox-tts';
  const modalUsername = process.env.MODAL_USERNAME || process.env.NEXT_PUBLIC_MODAL_USERNAME;
  
  if (!modalUsername) {
    return NextResponse.json(
      { 
        error: 'Modal username not configured',
        message: 'Please set MODAL_USERNAME (or NEXT_PUBLIC_MODAL_USERNAME) in your environment variables'
      },
      { status: 500 }
    );
  }
  
  const wsUrl = `wss://${modalUsername}--${modalAppName}-chatterbox-tts-web.modal.run/ws`;
  
  return NextResponse.json({ wsUrl });
}
