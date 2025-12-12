'use client';

import { TerminalChat } from '@/components/terminal-chat';
import Link from 'next/link';

export default function ChatPage() {
  return (
    <main className="min-h-screen bg-[#0d1117] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl mb-4">
        <Link 
          href="/"
          className="inline-flex items-center gap-2 text-[#8b949e] hover:text-[#58a6ff] transition-colors font-mono text-sm"
        >
          <span>←</span>
          <span>back to home</span>
        </Link>
      </div>
      <TerminalChat />
    </main>
  );
}
