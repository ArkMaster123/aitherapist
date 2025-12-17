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

    const body = await request.json();
    const { messages, model = 'llama-3.3-70b-versatile', temperature = 0.7, max_tokens = 1024 } = body;

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages array is required' },
        { status: 400 }
      );
    }

    // Call Groq LLM API
    const completion = await groq.chat.completions.create({
      model,
      messages,
      temperature,
      max_tokens,
      stream: false,
    });

    const responseText = completion.choices[0]?.message?.content || '';

    return NextResponse.json({
      text: responseText,
      model: completion.model,
      usage: completion.usage,
    });

  } catch (error: any) {
    console.error('Groq LLM error:', error);
    
    let errorMessage = 'Failed to generate response';
    if (error.message) {
      errorMessage = error.message;
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}

// GET endpoint to list available models
export async function GET() {
  try {
    if (!process.env.GROQ_API_KEY && !process.env.NEXT_PUBLIC_GROQ_API_KEY) {
      return NextResponse.json(
        { error: 'GROQ_API_KEY not configured' },
        { status: 500 }
      );
    }

    const models = await groq.models.list();
    
    // Filter to only show chat completion models
    const chatModels = models.data
      .filter(model => model.id.includes('llama') || model.id.includes('mixtral') || model.id.includes('gemma'))
      .map(model => ({
        id: model.id,
        created: model.created,
        owned_by: model.owned_by,
      }));

    return NextResponse.json({
      models: chatModels,
    });

  } catch (error: any) {
    console.error('Groq models list error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch models' },
      { status: 500 }
    );
  }
}

