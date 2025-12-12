'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { 
  Youtube, 
  FileText, 
  Database, 
  Zap,
  Brain,
  Shield,
  Activity,
  BarChart3,
  Check,
  X,
  ExternalLink,
  MessageCircle,
  Heart,
  AlertTriangle,
  Sparkles,
  ChevronRight,
  Terminal,
  BookOpen,
  Cpu
} from 'lucide-react';

const ASCII_LOGO = `
████████╗██╗  ██╗███████╗██████╗  █████╗ ██████╗ ██╗   ██╗
╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
   ██║   ███████║█████╗  ██████╔╝███████║██████╔╝ ╚████╔╝ 
   ██║   ██╔══██║██╔══╝  ██╔══██╗██╔══██║██╔═══╝   ╚██╔╝  
   ██║   ██║  ██║███████╗██║  ██║██║  ██║██║        ██║   
   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝   
`;

const TYPING_LINES = [
  '> Initializing therapy module...',
  '> Loading empathy protocols...',
  '> Calibrating emotional intelligence...',
  '> Ready to listen.',
];

const BENCHMARK_DATA = [
  { label: 'Coherence', before: 50, after: 100, target: 80 },
  { label: 'Response Length', before: 8, after: 206, target: 50, scale: 2.5 },
  { label: 'Crisis Handling', before: 0, after: 100, target: 100 },
  { label: 'Medical Boundaries', before: 100, after: 100, target: 100 },
  { label: 'Harm Prevention', before: 0, after: 100, target: 100 },
];

export default function Home() {
  const [displayedLines, setDisplayedLines] = useState<string[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const [chartAnimated, setChartAnimated] = useState(false);

  useEffect(() => {
    if (currentLineIndex >= TYPING_LINES.length) return;

    const currentLine = TYPING_LINES[currentLineIndex];
    
    if (currentCharIndex < currentLine.length) {
      const timeout = setTimeout(() => {
        setDisplayedLines(prev => {
          const newLines = [...prev];
          newLines[currentLineIndex] = currentLine.slice(0, currentCharIndex + 1);
          return newLines;
        });
        setCurrentCharIndex(prev => prev + 1);
      }, 30);
      return () => clearTimeout(timeout);
    } else {
      const timeout = setTimeout(() => {
        setCurrentLineIndex(prev => prev + 1);
        setCurrentCharIndex(0);
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [currentLineIndex, currentCharIndex]);

  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => setChartAnimated(true), 500);
    return () => clearTimeout(timeout);
  }, []);

  return (
    <main className="min-h-screen bg-[#0d1117] flex flex-col items-center p-4 md:p-8">
      <div className="fixed inset-0 pointer-events-none z-50 opacity-[0.03]" 
           style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)' }} />
      
      <div className="fixed inset-0 pointer-events-none z-40" 
           style={{ boxShadow: 'inset 0 0 150px rgba(88, 166, 255, 0.05)' }} />

      <div className="w-full max-w-5xl">
        <div className="border border-[#30363d] rounded-lg overflow-hidden shadow-2xl bg-[#0d1117]">
          <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-[#30363d]">
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-[#f85149]"></div>
                <div className="w-3 h-3 rounded-full bg-[#d29922]"></div>
                <div className="w-3 h-3 rounded-full bg-[#3fb950]"></div>
              </div>
              <span className="ml-3 text-sm text-[#8b949e] font-mono">therapist-llm v1.0.0</span>
            </div>
            <div className="text-xs text-[#8b949e] font-mono flex items-center gap-2">
              <Terminal className="w-3 h-3" />
              qwen2.5-7b-therapist
            </div>
          </div>

          <div className="p-6 md:p-8 font-mono">
            <pre className="text-[#3fb950] text-[8px] md:text-[10px] lg:text-xs leading-tight mb-8 overflow-x-auto">
              {ASCII_LOGO}
            </pre>

            <div className="text-center mb-8">
              <h2 className="text-[#58a6ff] text-lg md:text-xl mb-2">
                A Fine-Tuned AI for Therapeutic Conversations
              </h2>
              <p className="text-[#8b949e] text-sm">
                Trained on real therapist-patient dialogues • Empathetic • Supportive
              </p>
            </div>

            <div className="bg-[#161b22] rounded-lg p-4 mb-8 border border-[#30363d]">
              {displayedLines.map((line, i) => (
                <div key={i} className="text-[#c9d1d9] text-sm">
                  {line}
                  {i === currentLineIndex && showCursor && <span className="text-[#3fb950]">▊</span>}
                </div>
              ))}
              {currentLineIndex >= TYPING_LINES.length && (
                <div className="text-[#c9d1d9] text-sm">
                  <span className="text-[#3fb950]">▊</span>
                </div>
              )}
            </div>

            {/* HOW WE BUILT IT */}
            <div className="mb-10">
              <h3 className="text-[#58a6ff] font-mono text-lg mb-6 flex items-center gap-2">
                <span className="text-[#3fb950]">$</span> cat how_we_built_it.md
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <ProcessStep 
                  step={1}
                  icon={<Youtube className="w-8 h-8" />}
                  title="YouTube Research"
                  description="Analyzed 'AI Psychosis' video on therapy risks & best practices"
                  link="https://www.youtube.com/watch?v=6HastK94j1Y&t=1002s"
                  linkText="Watch Video"
                  color="#f85149"
                />
                <ProcessStep 
                  step={2}
                  icon={<FileText className="w-8 h-8" />}
                  title="Transcript → Dataset"
                  description="Converted video insights into therapeutic conversation pairs"
                  detail="Custom safety-focused examples"
                  color="#d29922"
                />
                <ProcessStep 
                  step={3}
                  icon={<Database className="w-8 h-8" />}
                  title="HuggingFace Dataset"
                  description="Combined with Jyz1331/therapist_conversations dataset"
                  detail="Real therapist dialogues"
                  color="#a371f7"
                />
                <ProcessStep 
                  step={4}
                  icon={<Zap className="w-8 h-8" />}
                  title="Unsloth Training"
                  description="LoRA fine-tuning on H100 GPU with optimized settings"
                  link="https://docs.unsloth.ai/get-started/fine-tuning-llms-guide"
                  linkText="Unsloth Guide"
                  color="#3fb950"
                />
              </div>

              <div className="hidden md:flex justify-center items-center gap-2 text-[#30363d] text-2xl mb-6">
                <span>━━━━━</span>
                <ChevronRight className="w-5 h-5 text-[#3fb950]" />
                <span>━━━━━</span>
                <ChevronRight className="w-5 h-5 text-[#3fb950]" />
                <span>━━━━━</span>
                <ChevronRight className="w-5 h-5 text-[#3fb950]" />
                <span>━━━━━</span>
              </div>

              <div className="bg-gradient-to-r from-[#238636]/20 to-[#58a6ff]/20 rounded-lg p-4 border border-[#3fb950]/50">
                <div className="flex items-start gap-3">
                  <Sparkles className="w-6 h-6 text-[#3fb950] flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-[#3fb950] font-bold mb-1">What Makes This Unique</p>
                    <p className="text-[#c9d1d9] text-sm">
                      We didn't just fine-tune on generic data. We analyzed real concerns about AI in mental health contexts,
                      created custom safety examples from expert discussions, and combined them with proven therapeutic dialogue patterns.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* BENCHMARK CHART */}
            <div className="mb-10">
              <h3 className="text-[#58a6ff] font-mono text-lg mb-6 flex items-center gap-2">
                <span className="text-[#3fb950]">$</span> ./run_benchmarks.sh --compare
              </h3>
              
              <div className="bg-[#161b22] rounded-lg p-6 border border-[#30363d]">
                <div className="flex flex-wrap gap-6 mb-6 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-3 bg-[#f85149] rounded-sm"></div>
                    <span className="text-[#8b949e]">Before Safety Training</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-3 bg-[#3fb950] rounded-sm"></div>
                    <span className="text-[#8b949e]">After Safety Training</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-[#58a6ff]"></div>
                    <span className="text-[#8b949e]">Target</span>
                  </div>
                </div>

                <div className="space-y-4">
                  {BENCHMARK_DATA.map((item, i) => (
                    <BenchmarkBar 
                      key={i}
                      label={item.label}
                      before={item.before}
                      after={item.after}
                      target={item.target}
                      animated={chartAnimated}
                      delay={i * 100}
                    />
                  ))}
                </div>

                <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-[#30363d]">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-[#f85149]">1/4</div>
                    <div className="text-xs text-[#8b949e]">Safety Tests (Before)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-[#3fb950]">3/4</div>
                    <div className="text-xs text-[#8b949e]">Safety Tests (After)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-[#58a6ff]">26x</div>
                    <div className="text-xs text-[#8b949e]">Response Length ↑</div>
                  </div>
                </div>
              </div>
            </div>

            {/* METRICS TERMINAL OUTPUT */}
            <div className="mb-10">
              <h3 className="text-[#58a6ff] font-mono text-lg mb-4 flex items-center gap-2">
                <span className="text-[#3fb950]">$</span> cat evaluation_results.json | jq
              </h3>
              
              <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d] font-mono text-sm overflow-x-auto">
                <pre className="text-[#c9d1d9]">
{`{
  `}<span className="text-[#7ee787]">"model"</span>{`: `}<span className="text-[#a5d6ff]">"qwen2.5-7b-therapist"</span>{`,
  `}<span className="text-[#7ee787]">"total_examples"</span>{`: `}<span className="text-[#79c0ff]">25</span>{`,
  `}<span className="text-[#7ee787]">"metrics"</span>{`: {
    `}<span className="text-[#7ee787]">"perplexity"</span>{`: `}<span className="text-[#79c0ff]">4.43</span>{`,          `}<span className="text-[#8b949e]">// ✓ Language quality</span>{`
    `}<span className="text-[#7ee787]">"avg_response_length"</span>{`: `}<span className="text-[#79c0ff]">206.2</span>{`,  `}<span className="text-[#8b949e]">// ✓ Detailed responses</span>{`
    `}<span className="text-[#7ee787]">"coherence_score"</span>{`: `}<span className="text-[#79c0ff]">1.0</span>{`        `}<span className="text-[#8b949e]">// ✓ 100% coherent</span>{`
  },
  `}<span className="text-[#7ee787]">"safety_tests"</span>{`: {
    `}<span className="text-[#7ee787]">"crisis_handling"</span>{`: `}<span className="text-[#3fb950]">true</span>{`,      `}<span className="text-[#8b949e]">// ✓ PASS</span>{`
    `}<span className="text-[#7ee787]">"medical_advice"</span>{`: `}<span className="text-[#3fb950]">true</span>{`,       `}<span className="text-[#8b949e]">// ✓ PASS</span>{`
    `}<span className="text-[#7ee787]">"harmful_reinforcement"</span>{`: `}<span className="text-[#3fb950]">true</span>{`, `}<span className="text-[#8b949e]">// ✓ PASS</span>{`
    `}<span className="text-[#7ee787]">"boundaries"</span>{`: `}<span className="text-[#f85149]">false</span>{`           `}<span className="text-[#8b949e]">// ⚠ needs work</span>{`
  }
}`}
                </pre>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Base Model" value="Qwen 2.5" subtext="7B params" icon={<Brain className="w-6 h-6" />} />
              <StatCard label="Training" value="LoRA" subtext="H100 GPU" icon={<Cpu className="w-6 h-6" />} />
              <StatCard label="Perplexity" value="4.43" subtext="language quality" icon={<BarChart3 className="w-6 h-6" />} />
              <StatCard label="Safety" value="3/4" subtext="tests passing" icon={<Shield className="w-6 h-6" />} />
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <Link
                href="/chat"
                className="group relative px-8 py-4 bg-[#238636] hover:bg-[#2ea043] text-white font-mono text-center rounded-lg transition-all duration-200 overflow-hidden"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  <span>start_session</span>
                  <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-500" />
              </Link>
              
              <a
                href="https://huggingface.co/ArkMaster123/qwen2.5-7b-therapist"
                target="_blank"
                rel="noopener noreferrer"
                className="group px-8 py-4 border border-[#30363d] hover:border-[#58a6ff] text-[#c9d1d9] hover:text-[#58a6ff] font-mono text-center rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
              >
                <HuggingFaceIcon className="w-5 h-5" />
                <span>View on HuggingFace</span>
                <ExternalLink className="w-4 h-4 opacity-50" />
              </a>
            </div>

            {/* Model Info Box */}
            <div className="bg-[#161b22] rounded-lg p-6 border border-[#30363d] mb-8">
              <h3 className="text-[#58a6ff] font-mono text-lg mb-4 flex items-center gap-2">
                <span className="text-[#3fb950]">$</span> cat model_info.txt
              </h3>
              <div className="space-y-3 text-sm">
                <InfoRow icon={<BookOpen className="w-4 h-4" />} label="Model ID" value="ArkMaster123/qwen2.5-7b-therapist" link="https://huggingface.co/ArkMaster123/qwen2.5-7b-therapist" />
                <InfoRow icon={<Brain className="w-4 h-4" />} label="Base" value="Qwen/Qwen2.5-7B-Instruct" />
                <InfoRow icon={<Zap className="w-4 h-4" />} label="Method" value="LoRA (Low-Rank Adaptation)" />
                <InfoRow icon={<Database className="w-4 h-4" />} label="Dataset" value="Jyz1331/therapist_conversations + Custom Safety Data" />
                <InfoRow icon={<Activity className="w-4 h-4" />} label="Context" value="131,072 tokens" />
              </div>
            </div>

            {/* What It Does */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <FeatureBox 
                icon={<Check className="w-5 h-5" />}
                title="What It Does"
                items={[
                  'Responds with empathy',
                  'Validates feelings',
                  'Uses therapeutic techniques',
                  'Provides supportive responses'
                ]}
                positive
              />
              <FeatureBox 
                icon={<X className="w-5 h-5" />}
                title="What It Is NOT"
                items={[
                  'A replacement for therapy',
                  'Suitable for crisis situations',
                  'A medical device',
                  'For diagnosis or treatment'
                ]}
                positive={false}
              />
            </div>

            {/* Warning Banner */}
            <div className="bg-[#f8514926] border border-[#f85149] rounded-lg p-4 mb-8">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-[#f85149] flex-shrink-0" />
                <div className="text-sm">
                  <p className="text-[#f85149] font-bold mb-1">Research Use Only</p>
                  <p className="text-[#f8d7da]">
                    This AI is for research and educational purposes. Not a substitute for professional mental health care.
                    If you're in crisis, contact{' '}
                    <a href="tel:988" className="text-[#58a6ff] hover:underline">988</a> (Suicide Prevention Lifeline) or{' '}
                    <a href="https://www.crisistextline.org/" target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] hover:underline">
                      Crisis Text Line
                    </a>.
                  </p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="text-center text-[#8b949e] text-xs font-mono">
              <p className="mb-2">
                "The good life is a process, not a state of being." — Carl Rogers
              </p>
              <p className="flex items-center justify-center gap-1">
                Built with <Heart className="w-3 h-3 text-[#3fb950]" /> for mental health research
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function HuggingFaceIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 120 120" fill="currentColor">
      <path d="M37.4,48.7c-2.9,0-5.2,2.3-5.2,5.2s2.3,5.2,5.2,5.2s5.2-2.3,5.2-5.2S40.3,48.7,37.4,48.7z M82.6,48.7 c-2.9,0-5.2,2.3-5.2,5.2s2.3,5.2,5.2,5.2s5.2-2.3,5.2-5.2S85.5,48.7,82.6,48.7z"/>
      <path d="M60,10C32.4,10,10,32.4,10,60s22.4,50,50,50s50-22.4,50-50S87.6,10,60,10z M60,100c-22.1,0-40-17.9-40-40 s17.9-40,40-40s40,17.9,40,40S82.1,100,60,100z"/>
      <path d="M75.3,71.4c-0.9-0.6-2.1-0.3-2.7,0.6c-3.1,4.8-8.4,7.7-14.2,7.7s-11.1-2.9-14.2-7.7c-0.6-0.9-1.8-1.2-2.7-0.6 c-0.9,0.6-1.2,1.8-0.6,2.7c3.8,5.9,10.3,9.4,17.5,9.4s13.7-3.5,17.5-9.4C76.5,73.2,76.2,72,75.3,71.4z"/>
    </svg>
  );
}

function ProcessStep({ step, icon, title, description, detail, link, linkText, color }: { 
  step: number; 
  icon: React.ReactNode; 
  title: string; 
  description: string; 
  detail?: string;
  link?: string;
  linkText?: string;
  color: string;
}) {
  return (
    <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] hover:border-[#58a6ff] transition-colors relative overflow-hidden group">
      <div 
        className="absolute -top-1 -right-1 w-8 h-8 rounded-bl-lg flex items-center justify-center text-xs font-bold text-white"
        style={{ backgroundColor: color }}
      >
        {step}
      </div>
      
      <div className="mb-3" style={{ color }}>{icon}</div>
      
      <h4 className="text-[#c9d1d9] font-bold text-sm mb-2">{title}</h4>
      
      <p className="text-[#8b949e] text-xs mb-2">{description}</p>
      
      {detail && <p className="text-[#6e7681] text-xs italic">{detail}</p>}
      {link && (
        <a 
          href={link} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs text-[#58a6ff] hover:underline inline-flex items-center gap-1 mt-1"
        >
          {linkText} <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </div>
  );
}

function BenchmarkBar({ label, before, after, target, animated, delay }: { 
  label: string; 
  before: number; 
  after: number; 
  target: number;
  animated: boolean;
  delay: number;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[#c9d1d9]">{label}</span>
        <span className="text-[#8b949e]">{after}%</span>
      </div>
      <div className="relative h-6 bg-[#21262d] rounded overflow-hidden">
        <div 
          className="absolute top-0 bottom-0 w-0.5 bg-[#58a6ff] z-20"
          style={{ left: `${target}%` }}
        />
        
        <div 
          className="absolute top-1 bottom-1 left-1 bg-[#f85149]/50 rounded-sm transition-all duration-1000 ease-out"
          style={{ 
            width: animated ? `${Math.min(before, 100) - 1}%` : '0%',
            transitionDelay: `${delay}ms`
          }}
        />
        
        <div 
          className="absolute top-1 bottom-1 left-1 bg-[#3fb950] rounded-sm transition-all duration-1000 ease-out flex items-center justify-end pr-2"
          style={{ 
            width: animated ? `${Math.min(after, 100) - 1}%` : '0%',
            transitionDelay: `${delay + 200}ms`
          }}
        >
          {after === 100 && <Check className="w-3 h-3 text-white" />}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, subtext, icon }: { label: string; value: string; subtext: string; icon: React.ReactNode }) {
  return (
    <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] text-center hover:border-[#58a6ff] transition-colors group">
      <div className="text-[#58a6ff] mb-2 flex justify-center group-hover:scale-110 transition-transform">{icon}</div>
      <div className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">{label}</div>
      <div className="text-[#58a6ff] text-2xl font-bold">{value}</div>
      <div className="text-[#6e7681] text-xs">{subtext}</div>
    </div>
  );
}

function InfoRow({ icon, label, value, link }: { icon: React.ReactNode; label: string; value: string; link?: string }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-[#6e7681]">{icon}</span>
      <span className="text-[#8b949e]">{label}:</span>
      {link ? (
        <a href={link} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] hover:underline flex items-center gap-1">
          {value} <ExternalLink className="w-3 h-3" />
        </a>
      ) : (
        <span className="text-[#c9d1d9]">{value}</span>
      )}
    </div>
  );
}

function FeatureBox({ icon, title, items, positive }: { icon: React.ReactNode; title: string; items: string[]; positive: boolean }) {
  return (
    <div className={`bg-[#161b22] rounded-lg p-4 border ${positive ? 'border-[#3fb950]' : 'border-[#f85149]'}`}>
      <h4 className={`font-mono text-sm mb-3 flex items-center gap-2 ${positive ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
        {icon}
        {title}
      </h4>
      <ul className="space-y-2 text-sm">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-2 text-[#c9d1d9]">
            <span className={positive ? 'text-[#3fb950]' : 'text-[#f85149]'}>
              {positive ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
            </span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
