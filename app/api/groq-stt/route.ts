import { NextRequest, NextResponse } from 'next/server';
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY || process.env.NEXT_PUBLIC_GROQ_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    if (!process.env.GROQ_API_KEY && !process.env.NEXT_PUBLIC_GROQ_API_KEY) {
      return NextResponse.json(
        { error: 'GROQ_API_KEY not configured' },
        { status: 500 }
      );
    }

    const formData = await request.formData();
    const audioFile = formData.get('audio') as File;
    
    if (!audioFile) {
      return NextResponse.json(
        { error: 'No audio file provided' },
        { status: 400 }
      );
    }

    // Check file size (25MB free tier, 100MB dev tier)
    const fileSizeMB = audioFile.size / (1024 * 1024);
    if (fileSizeMB > 100) {
      return NextResponse.json(
        { error: 'Audio file too large. Maximum size is 100MB for dev tier.' },
        { status: 400 }
      );
    }

    // Groq SDK accepts File, Blob, or Buffer
    // Use the File object directly from FormData - it should work in Node.js 18+
    // If that doesn't work, we'll use a Buffer with proper form-data formatting
    const transcription = await groq.audio.transcriptions.create({
      file: audioFile,
      model: 'whisper-large-v3-turbo', // Fastest model for transcription
      temperature: 0, // Recommended for transcriptions (default, improves accuracy)
      response_format: 'verbose_json', // Get timestamps and metadata (avg_logprob, no_speech_prob, etc.)
      // language: 'en', // Optional: specify language (ISO-639-1) to improve accuracy and latency
      //                     If omitted, Groq will auto-detect the language
      // prompt: '...', // Optional: context/spelling guidance (max 224 tokens)
    });

    return NextResponse.json({
      text: transcription.text,
      language: transcription.language || 'en',
      // Include additional metadata if available
      ...(transcription.segments && { segments: transcription.segments }),
    });

  } catch (error: any) {
    console.error('Groq STT error:', error);
    
    // Provide more helpful error messages
    let errorMessage = 'Failed to transcribe audio';
    if (error.message?.includes('file')) {
      errorMessage = 'Invalid audio file format. Supported: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm';
    } else if (error.message?.includes('size') || error.message?.includes('large')) {
      errorMessage = 'Audio file too large. Maximum size is 100MB for dev tier.';
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}
