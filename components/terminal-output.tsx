'use client';

interface TerminalOutputProps {
  content: string;
  type?: 'user' | 'assistant' | 'system' | 'info' | 'error' | 'success' | 'ascii-art';
}

export function TerminalOutput({ content, type = 'assistant' }: TerminalOutputProps) {
  const getStyle = () => {
    switch (type) {
      case 'user':
        return 'text-[#58a6ff]';
      case 'assistant':
        return 'text-[#c9d1d9]';
      case 'system':
        return 'text-[#8b949e] font-bold';
      case 'info':
        return 'text-[#58a6ff]';
      case 'error':
        return 'text-[#f85149]';
      case 'success':
        return 'text-[#3fb950]';
      case 'ascii-art':
        return 'text-[#58a6ff] font-mono leading-tight';
      default:
        return 'text-[#c9d1d9]';
    }
  };

  const getPrefix = () => {
    switch (type) {
      case 'user':
        return '';
      case 'system':
        return '> ';
      case 'info':
        return 'ℹ ';
      case 'error':
        return '✗ ';
      case 'success':
        return '✓ ';
      case 'ascii-art':
        return '';
      default:
        return '';
    }
  };

  return (
    <div className={`${getStyle()} whitespace-pre-wrap break-words`}>
      <span>{getPrefix()}</span>
      <span>{content}</span>
    </div>
  );
}

