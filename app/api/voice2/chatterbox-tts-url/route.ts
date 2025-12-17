import { NextResponse } from 'next/server';

export async function GET() {
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
  
  // Class name is ChatterboxTTS, Modal converts it to chatterboxtts (lowercase, no dashes)
  const wsUrl = `wss://${modalUsername}--${modalAppName}-chatterboxtts-web.modal.run/ws`;
  const httpUrl = `https://${modalUsername}--${modalAppName}-chatterboxtts-web.modal.run/tts`;
  
  return NextResponse.json({ wsUrl, httpUrl });
}

