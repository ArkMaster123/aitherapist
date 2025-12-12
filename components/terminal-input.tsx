'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface TerminalInputProps {
  onSubmit: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function TerminalInput({ onSubmit, disabled, placeholder }: TerminalInputProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !disabled && input.trim()) {
      e.preventDefault();
      const value = input.trim();
      setInput('');
      onSubmit(value);
    }
  };

  return (
    <div className="flex items-center px-4 py-3 gap-2">
      <span className="text-[#58a6ff] select-none">$</span>
      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleSubmit}
        disabled={disabled}
        placeholder={placeholder || 'Type your message...'}
        className="flex-1 bg-transparent border-none outline-none text-[#c9d1d9] placeholder:text-[#6e7681] font-mono text-sm"
      />
      {disabled && (
        <span className="text-xs text-[#8b949e]">⏳</span>
      )}
    </div>
  );
}

