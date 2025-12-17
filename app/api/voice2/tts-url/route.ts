import { NextResponse } from 'next/server';

export async function GET() {
  // Get Modal config for VibeVoice TTS
  const modalAppName = process.env.MODAL_APP_NAME || process.env.NEXT_PUBLIC_MODAL_APP_NAME || 'therapist-voice-chat';
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
  
  // Class name is VibeVoiceTTS, Modal converts it to vibevoicetts (lowercase, no dashes)
  const wsUrl = `wss://${modalUsername}--${modalAppName}-vibevoicetts-web.modal.run/ws`;
  const httpUrl = `https://${modalUsername}--${modalAppName}-vibevoicetts-web.modal.run/tts`;
  
  return NextResponse.json({ wsUrl, httpUrl });
}
