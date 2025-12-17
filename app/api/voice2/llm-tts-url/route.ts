import { NextResponse } from 'next/server';

export async function GET() {
  // Get Modal config for LLM+TTS agent
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
  
  // LLM+TTS agent WebSocket URL
  const wsUrl = `wss://${modalUsername}--${modalAppName}-llm-tts-agent-web.modal.run/ws`;
  
  return NextResponse.json({ wsUrl });
}
