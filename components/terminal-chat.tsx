'use client';

import { useState, useEffect, useRef } from 'react';
import { TerminalInput } from './terminal-input';
import { TerminalOutput } from './terminal-output';
import { useChat } from '@ai-sdk/react';

export function TerminalChat() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const chat = useChat({
    onError: (error) => {
      console.error('useChat error:', error);
      setError(error.message || 'An error occurred');
      setIsLoading(false);
    },
    onFinish: (message) => {
      console.log('Chat finished:', message);
      setIsLoading(false);
    },
  });

  const { messages: aiMessages } = chat;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [aiMessages]);

  const handleSubmit = async (input: string) => {
    if (!input.trim()) return;

    setError(null);
    setIsLoading(true);

    // Send to AI using sendMessage - v5 format
    await chat.sendMessage({ text: input });
  };

  return (
    <div className="w-full max-w-4xl h-[90vh] flex flex-col bg-[#0d1117] border border-[#30363d] rounded-lg overflow-hidden shadow-2xl">
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-[#30363d]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#f85149]"></div>
            <div className="w-3 h-3 rounded-full bg-[#d29922]"></div>
            <div className="w-3 h-3 rounded-full bg-[#3fb950]"></div>
          </div>
          <span className="ml-3 text-sm text-[#8b949e]">terminal-chat</span>
        </div>
        <div className="text-xs text-[#8b949e]">
          {/* Rate limiting disabled */}
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono">
        <TerminalOutput
          content="Welcome to Terminal Chat"
          type="system"
        />
        <TerminalOutput
          content="Type your message below and press Enter to chat with AI."
          type="info"
        />
        
        {error && (
          <TerminalOutput
            content={error}
            type="error"
          />
        )}

        {aiMessages.map((message: any, index) => {
          // Extract text content and tool results from AI SDK v5 message format
          let messageText = '';
          let toolResults: Array<{ toolCallId: string; toolName: string; result: any }> = [];
          let toolCalls: any[] = [];

          if (typeof message.content === 'string') {
            messageText = message.content;
          } else if (Array.isArray(message.parts)) {
            // AI SDK v5 format uses parts array
            const textParts: string[] = [];

            message.parts.forEach((part: any) => {
              if (part.type === 'text' && part.text) {
                textParts.push(part.text);
              } else if (part.type === 'tool-call') {
                toolCalls.push(part);
              } else if (part.type === 'tool-result') {
                toolResults.push({
                  toolCallId: part.toolCallId,
                  toolName: part.toolName,
                  result: part.result
                });
              } else if (part.type && part.type.startsWith('tool-')) {
                // Handle tool results in v5 format: type is "tool-{toolName}"
                const toolName = part.type.replace('tool-', '');
                if (part.output) {
                  toolResults.push({
                    toolCallId: part.toolCallId || '',
                    toolName: toolName,
                    result: part.output
                  });
                }
              }
            });

            messageText = textParts.join('');
          }
          
          // Debug logging (remove in production)
          console.log('Processing message:', {
            role: message.role,
            hasParts: Array.isArray(message.parts),
            partsCount: message.parts?.length || 0,
            toolCallsFound: toolCalls.length,
            toolResultsFound: toolResults.length,
            messageText: messageText.substring(0, 50),
            allParts: message.parts?.map((p: any) => ({ type: p.type, hasOutput: !!p.output }))
          });

          if (toolResults.length > 0) {
            console.log('Tool results to display:', toolResults);
          }
          
          return (
            <div key={index} className="space-y-2">
              {message.role === 'user' ? (
                <TerminalOutput
                  content={`$ ${messageText || message.content || ''}`}
                  type="user"
                />
              ) : (
                <>
                  {messageText && (
                    <TerminalOutput
                      content={messageText}
                      type="assistant"
                    />
                  )}
                  {/* Show tool calls being made */}
                  {toolCalls.length > 0 && (
                    <TerminalOutput
                      content={`🔧 Calling tool: ${toolCalls.map((tc: any) => tc.toolName || 'unknown').join(', ')}`}
                      type="info"
                    />
                  )}
                  {/* Show tool results */}
                  {toolResults.map((toolResult, toolIndex) => {
                    if (toolResult.toolName === 'generate_ascii_art') {
                      // Handle ASCII art result
                      const asciiArt = toolResult.result?.asciiArt || toolResult.result?.result?.asciiArt || toolResult.result;
                      if (asciiArt) {
                        return (
                          <div key={toolIndex} className="my-4 p-2 bg-[#161b22] rounded border border-[#30363d]">
                            <TerminalOutput
                              content={typeof asciiArt === 'string' ? asciiArt : JSON.stringify(asciiArt, null, 2)}
                              type="ascii-art"
                            />
                            {toolResult.result?.message && (
                              <div className="mt-2">
                                <TerminalOutput
                                  content={toolResult.result.message}
                                  type="info"
                                />
                              </div>
                            )}
                          </div>
                        );
                      }
                    }
                    // Fallback: show any tool result
                    return (
                      <div key={toolIndex} className="my-2 p-2 bg-[#161b22] rounded border border-[#30363d]">
                        <TerminalOutput
                          content={`Tool result: ${JSON.stringify(toolResult.result, null, 2)}`}
                          type="info"
                        />
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          );
        })}

        {isLoading && (
          <TerminalOutput
            content="Thinking..."
            type="info"
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Terminal Input */}
      <div className="border-t border-[#30363d] bg-[#161b22]">
        <TerminalInput
          onSubmit={handleSubmit}
          disabled={isLoading}
          placeholder="Type your message and press Enter..."
        />
      </div>
    </div>
  );
}

