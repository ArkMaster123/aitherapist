import { NextRequest, NextResponse } from 'next/server';
import { generateText } from 'ai';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';

// System prompt for the therapist assistant
const SYSTEM_PROMPT = `You are a compassionate, empathetic AI therapist assistant. Your goal is to provide emotional support, active listening, and gentle guidance to users who may be experiencing difficult emotions or seeking help.

Key principles:
- Listen actively and validate the user's feelings
- Ask thoughtful, open-ended questions to understand their situation better
- Provide empathy and support without being prescriptive
- Use a warm, understanding, and non-judgmental tone
- Focus on helping users process their emotions and find their own path forward

Remember: You're here to support, not to diagnose or provide medical advice.`;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messages, temperature = 0.7, max_tokens = 1024 } = body;

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages array is required' },
        { status: 400 }
      );
    }

    // Get configuration for fine-tuned therapist model
    const apiBase = process.env.OPENAI_API_BASE;
    const apiKey = process.env.OPENAI_API_KEY || 'not-needed';
    const modelId = process.env.AI_MODEL || 'qwen-therapist';

    if (!apiBase) {
      return NextResponse.json(
        { error: 'OPENAI_API_BASE not configured. Fine-tuned therapist model requires vLLM server URL.' },
        { status: 500 }
      );
    }

    // Ensure baseURL includes /v1 for OpenAI-compatible APIs
    let baseURL = apiBase;
    if (!baseURL.endsWith('/v1')) {
      baseURL = baseURL.endsWith('/') ? `${baseURL}v1` : `${baseURL}/v1`;
    }

    // Create OpenAI-compatible client for vLLM
    const provider = createOpenAICompatible({
      name: 'therapist-vllm',
      baseURL: baseURL,
      apiKey: apiKey,
    });

    const model = provider.chatModel(modelId);

    // Prepare messages with system prompt
    const hasSystemMessage = messages.some((msg: any) => msg.role === 'system');
    const modelMessages = hasSystemMessage 
      ? messages.map((msg: any) => ({
          role: msg.role,
          content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content),
        }))
      : [
          { role: 'system' as const, content: SYSTEM_PROMPT },
          ...messages.map((msg: any) => ({
            role: msg.role,
            content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content),
          })),
        ];

    // Call the model using AI SDK generateText
    const startTime = Date.now();
    const result = await generateText({
      model,
      messages: modelMessages,
      temperature,
      maxTokens: max_tokens,
    });

    const responseText = result.text || '';
    const latency = Date.now() - startTime;

    return NextResponse.json({
      text: responseText,
      model: modelId,
      latency,
      usage: result.usage,
    });

  } catch (error: any) {
    console.error('Therapist LLM error:', error);
    
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

// GET endpoint to check if therapist model is available
export async function GET() {
  const apiBase = process.env.OPENAI_API_BASE;
  const modelId = process.env.AI_MODEL || 'qwen-therapist';
  
  return NextResponse.json({
    available: !!apiBase,
    model: modelId,
    endpoint: apiBase || 'not configured',
  });
}

