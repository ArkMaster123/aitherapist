import { streamText, convertToModelMessages, type UIMessage, tool } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';
import { z } from 'zod';

// Note: Client-side rate limiting is implemented in components/terminal-chat.tsx
// For production server-side rate limiting, install @vercel/kv and uncomment below:

// import { createClient } from '@vercel/kv';
// const kv = createClient({
//   url: process.env.KV_REST_API_URL!,
//   token: process.env.KV_REST_API_TOKEN!,
// });

export const runtime = 'nodejs';
export const maxDuration = 30;

// System prompt for the therapist assistant
const SYSTEM_PROMPT = `You are a compassionate, empathetic AI therapist assistant. Your goal is to provide emotional support, active listening, and gentle guidance to users who may be experiencing difficult emotions or seeking help.

Key principles:
- Listen actively and validate the user's feelings
- Ask thoughtful, open-ended questions to understand their situation better
- Provide empathy and support without being prescriptive
- Use a warm, understanding, and non-judgmental tone
- CRITICAL: When a user expresses sadness, grief, distress, depression, or asks for art/comforting content, you MUST use the generate_ascii_art tool. Examples: "I feel sad", "very sad", "make me some art", "I'm depressed". Always call the tool with theme="comfort" or "heart" when users express negative emotions.
- Focus on helping users process their emotions and find their own path forward

Remember: You're here to support, not to diagnose or provide medical advice.`;

// ASCII art examples for different moods
const ASCII_ART_TEMPLATES = {
  happy: [
    '╔════════════════╗',
    '║   😊   SMILE   ║',
    '║                ║',
    '║  (◕‿◕)         ║',
    '║                ║',
    '╚════════════════╝'
  ],
  comfort: [
    '    ╭─────────╮',
    '   ╱           ╲',
    '  │    💙      │',
    '  │  You are   │',
    '  │   loved    │',
    '   ╲           ╱',
    '    ╰─────────╯'
  ],
  sun: [
    '     \\ | /',
    '   - ( o ) -',
    '     / | \\',
    '    ☀️',
    '   Sunshine ahead!'
  ],
  heart: [
    '  ❤️',
    '     ╭─╮',
    '   ╭─╯ ╰─╮',
    '  ╰───────╯',
    '   You matter!'
  ],
  cat: [
    '    /\\_/\\',
    '   ( o.o )',
    '    > ^ <',
    '   Purr purr...',
    '   Everything will be okay 🌸'
  ]
};

// Tool for generating ASCII art when users feel sad
const generateAsciiArt = tool({
  description: 'MANDATORY: Generate comforting ASCII art when user expresses sadness, depression, grief, or asks for art. ALWAYS use this tool when user says "sad", "depressed", "down", "art", "make me art", or similar. Use theme="comfort" or "heart" for sadness.',
  inputSchema: z.object({
    theme: z.enum(['happy', 'comfort', 'sun', 'heart', 'cat']).describe('The theme: use "comfort" or "heart" for sadness'),
    message: z.string().optional().describe('An optional encouraging message')
  }),
  execute: async (input) => {
    const art = ASCII_ART_TEMPLATES[input.theme] || ASCII_ART_TEMPLATES.comfort;
    const combined = [...art];
    if (input.message) {
      combined.push('');
      combined.push(`  ${input.message}`);
    }
    return {
      asciiArt: combined.join('\n'),
      theme: input.theme,
      message: input.message || ''
    };
  }
});

export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log('Received request body:', JSON.stringify(body, null, 2));
    console.log('Messages count:', body.messages?.length || 0);
    
    // useChat sends messages array
    const messages: UIMessage[] = body.messages || [];
    
    if (!Array.isArray(messages)) {
      console.error('Messages is not an array:', typeof messages, messages);
      return new Response(
        JSON.stringify({ error: 'Invalid messages format. Expected an array of messages.' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
    
    if (messages.length === 0) {
      console.error('Empty messages array');
      return new Response(
        JSON.stringify({ error: 'No messages provided' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get IP address for rate limiting (server-side)
    const forwarded = req.headers.get('x-forwarded-for');
    const ip = forwarded ? forwarded.split(',')[0] : 'unknown';

    // TODO: Implement server-side rate limiting with Vercel KV or similar
    // For now, client-side rate limiting is used

    // Get configuration
    const modelId = process.env.AI_MODEL || 'gpt-4o-mini';
    const apiBase = process.env.OPENAI_API_BASE;
    const apiKey = process.env.OPENAI_API_KEY;

    // Determine if we're using a custom OpenAI-compatible endpoint (like vLLM)
    const isCustomEndpoint = apiBase && apiBase.startsWith('http');
    
    let model: any;

    if (isCustomEndpoint) {
      // For custom OpenAI-compatible endpoints (like vLLM on Modal)
      // Ensure baseURL includes /v1 for OpenAI-compatible APIs
      let baseURL = apiBase!;
      if (!baseURL.endsWith('/v1')) {
        baseURL = baseURL.endsWith('/') ? `${baseURL}v1` : `${baseURL}/v1`;
      }
      
      // Use createOpenAICompatible for v1-compatible APIs
      const provider = createOpenAICompatible({
        name: 'vllm',
        baseURL: baseURL,
        apiKey: apiKey || 'not-needed',
      });
      
      // Use the model name from environment (e.g., 'qwen-therapist' or 'llm')
      model = provider.chatModel(modelId);
    } else {
      // Standard OpenAI model via Vercel AI Gateway or direct OpenAI
      const openai = createOpenAI({
        apiKey: apiKey,
      });
      model = openai(modelId);
    }

    // Convert messages to model format
    // Check if any messages have parts (indicating tool call history from AI SDK v5)
    const hasComplexMessages = messages.some((msg: any) =>
      msg.parts && Array.isArray(msg.parts) && msg.parts.length > 0
    );

    let modelMessages: any[];

    if (hasComplexMessages) {
      // Manually convert messages with tool call history
      // AI SDK's convertToModelMessages doesn't handle tool results properly for vLLM
      console.log('Manually converting messages with tool call history');
      modelMessages = messages.map((msg: any) => {
        if (msg.role === 'user') {
          return {
            role: 'user',
            content: typeof msg.content === 'string' ? msg.content :
                     msg.parts?.filter((p: any) => p.type === 'text').map((p: any) => p.text).join('') || ''
          };
        } else if (msg.role === 'assistant') {
          // For assistant messages, only extract text content
          // Skip tool calls and tool results - we don't need them in the history for vLLM
          let content = '';

          if (typeof msg.content === 'string') {
            content = msg.content;
          } else if (msg.parts) {
            const textParts = msg.parts.filter((p: any) => p.type === 'text').map((p: any) => p.text);
            content = textParts.join('');
          }

          // Only return message if it has content
          if (content && content.trim()) {
            return {
              role: 'assistant',
              content: content
            };
          }
          return null; // Will be filtered out
        }
        return msg;
      }).filter((msg: any) => msg !== null && msg.role && msg.content);
    } else {
      // Use standard converter for simple messages
      try {
        modelMessages = convertToModelMessages(messages);
        console.log('Converted messages using standard converter:', modelMessages.length);
      } catch (conversionError: any) {
        console.error('Error converting messages:', conversionError);
        // Fallback to manual conversion
        modelMessages = messages.map((msg: any) => ({
          role: msg.role,
          content: typeof msg.content === 'string' ? msg.content : ''
        })).filter((msg: any) => msg.role && msg.content);
      }
    }

    // Add system prompt at the beginning if not already present
    const hasSystemMessage = modelMessages.some((msg: any) => msg.role === 'system');
    if (!hasSystemMessage) {
      modelMessages = [{ role: 'system' as const, content: SYSTEM_PROMPT }, ...modelMessages];
    }
    
    // For v1-compatible APIs (like vLLM), convert content array to string
    if (isCustomEndpoint) {
      modelMessages = modelMessages.map((msg: any) => {
        // Handle tool messages - they need proper string content for vLLM
        if (msg.role === 'tool') {
          const content = typeof msg.content === 'string' 
            ? msg.content 
            : JSON.stringify(msg.content || {});
          return {
            ...msg,
            content: content || '{}', // vLLM needs non-empty content
          };
        }
        
        // Convert content array to string for vLLM
        if (Array.isArray(msg.content)) {
          const textParts = msg.content
            .filter((part: any) => part.type === 'text' && part.text)
            .map((part: any) => part.text)
            .join('');
          return {
            ...msg,
            content: textParts || '',
          };
        }
        
        // Ensure content is never null/undefined
        if (msg.content === null || msg.content === undefined) {
          return {
            ...msg,
            content: '',
          };
        }
        
        return msg;
      });
      
      // Remove completely empty assistant messages (but keep ones with tool calls)
      modelMessages = modelMessages.filter((msg: any) => {
        if (msg.role === 'assistant') {
          const hasContent = msg.content && String(msg.content).trim().length > 0;
          const hasToolCalls = msg.toolCalls && Array.isArray(msg.toolCalls) && msg.toolCalls.length > 0;
          return hasContent || hasToolCalls;
        }
        // Keep all other messages (user, system, tool)
        return true;
      });
    }
    
    console.log('Final modelMessages count:', modelMessages.length);
    console.log('Final modelMessages summary:', modelMessages.map((m: any) => ({
      role: m.role,
      contentPreview: m.content ? String(m.content).substring(0, 50) : 'none',
      hasToolCalls: !!(m.toolCalls && Array.isArray(m.toolCalls) && m.toolCalls.length > 0)
    })));
    
    // Use AI SDK with streaming
    // Note: Tool calling is only enabled for standard OpenAI endpoints
    // For vLLM servers, ensure --enable-auto-tool-choice and --tool-call-parser are set
    const streamOptions: any = {
      model,
      messages: modelMessages,
      maxTokens: 4000, // Increased for tool calling (tool call + result + response)
      temperature: 0.7,
      maxSteps: 5, // Allow multiple tool call rounds
    };

    // Enable tools for all endpoints (vLLM server now has tool calling enabled)
    // Can be disabled by setting ENABLE_TOOLS=false if needed
    const enableTools = process.env.ENABLE_TOOLS !== 'false';

    // Check if user message indicates sadness/distress to force tool usage
    const lastUserMessage: any = messages[messages.length - 1];
    let userText = '';
    if (lastUserMessage?.role === 'user') {
      if (typeof lastUserMessage.content === 'string') {
        userText = lastUserMessage.content.toLowerCase();
      } else if (Array.isArray(lastUserMessage.parts)) {
        userText = lastUserMessage.parts
          .filter((p: any) => p.type === 'text')
          .map((p: any) => p.text)
          .join(' ')
          .toLowerCase();
      }
    }

    const sadnessKeywords = /\b(sad|depressed|down|upset|cry|crying|hurt|pain|anxious|worried|lonely|art|make me art|comfort)\b/i;
    const hasSadness = sadnessKeywords.test(userText);

    if (enableTools) {
      streamOptions.tools = {
        generate_ascii_art: generateAsciiArt,
      };

      // Force tool choice when sadness is detected
      if (hasSadness && isCustomEndpoint) {
        // For vLLM, we'll force the tool to be called
        streamOptions.toolChoice = 'required';
        console.log('🎯 Sadness detected, forcing tool call');
      } else {
        streamOptions.toolChoice = 'auto';
      }
    }

    console.log('StreamText options:', JSON.stringify({
      model: streamOptions.model?.modelId || 'unknown',
      hasTools: !!streamOptions.tools,
      toolNames: streamOptions.tools ? Object.keys(streamOptions.tools) : [],
      toolChoice: streamOptions.toolChoice,
      messageCount: streamOptions.messages?.length || 0,
      lastMessage: streamOptions.messages?.[streamOptions.messages.length - 1] ? {
        role: streamOptions.messages[streamOptions.messages.length - 1].role,
        contentPreview: String(streamOptions.messages[streamOptions.messages.length - 1].content || '').substring(0, 100)
      } : null
    }, null, 2));

    try {
      const result = streamText(streamOptions);
      
      console.log('StreamText result created successfully');
      
      // For debugging, we can try to inspect the result
      // Note: result is a stream, so we can't easily inspect it
      
      const response = result.toUIMessageStreamResponse();
      console.log('Response created, returning to client');
      
      return response;
    } catch (streamError: any) {
      console.error('Error in streamText:', streamError);
      console.error('Stream error details:', JSON.stringify({
        message: streamError.message,
        name: streamError.name,
        cause: streamError.cause
      }, null, 2));
      throw streamError;
    }
  } catch (error: any) {
    console.error('Chat API error:', error);
    console.error('Error stack:', error.stack);
    return new Response(
      JSON.stringify({ error: error.message || 'An error occurred', details: error.toString() }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

