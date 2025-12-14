'use client';

import { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  AlertCircle,
  Activity,
  Brain,
  MessageSquare,
  Target
} from 'lucide-react';
import Link from 'next/link';

interface EvaluationResults {
  model: string;
  vllm_url: string;
  n_interactions: number;
  n_turns: number;
  mean_scores: Record<string, number>;
  std_scores: Record<string, number>;
  min_scores: Record<string, number>;
  max_scores: Record<string, number>;
  all_scores: Array<Record<string, number>>;
}

interface ScoreCard {
  label: string;
  value: number;
  std?: number;
  min?: number;
  max?: number;
  format?: (val: number) => string;
}

export default function EvalsPage() {
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const fetchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/evals');
      if (!response.ok) {
        if (response.status === 404) {
          const data = await response.json();
          setError(data.message || 'No evaluation results found');
        } else {
          throw new Error('Failed to fetch results');
        }
        return;
      }
      const data = await response.json();
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
    // Trigger animations after component mounts
    setMounted(true);
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#58a6ff] animate-spin mx-auto mb-4" />
          <p className="text-[#8b949e] font-mono">Loading evaluation results...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#0d1117] flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-[#161b22] border border-[#30363d] rounded-lg p-8">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-[#f85149] flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h1 className="text-[#f85149] font-mono text-xl mb-2">No Results Found</h1>
              <p className="text-[#c9d1d9] mb-4">{error}</p>
              <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d] mb-4">
                <p className="text-[#8b949e] text-sm font-mono mb-2">To run the evaluation:</p>
                <code className="text-[#58a6ff] text-sm block">
                  python scripts/run_mind_eval.py --vllm-url YOUR_VLLM_URL
                </code>
              </div>
              <Link
                href="/"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white font-mono rounded-lg transition-colors"
              >
                ← Back to Home
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (!results) {
    return null;
  }

  // Format scores for display - filter out duplicate "Overall score" and "Average score"
  const scoreCards: ScoreCard[] = Object.entries(results.mean_scores)
    .filter(([key]) => key !== 'Overall score' && key !== 'Average score')
    .map(([key, value]) => ({
      label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: value,
      std: results.std_scores[key],
      min: results.min_scores[key],
      max: results.max_scores[key],
      format: (val: number) => val.toFixed(2),
    }));

  // Get overall score (use "Overall score" if available, otherwise calculate)
  const overallAvg = results.mean_scores['Overall score'] || results.mean_scores['Average score'] || 
    Object.values(results.mean_scores)
      .filter((_, idx, arr) => idx < arr.length - 2) // Exclude Overall/Average if they exist
      .reduce((a, b) => a + b, 0) / (Object.keys(results.mean_scores).length - 2);

  // Get grade based on score (1-5 scale)
  const getGrade = (score: number): { label: string; color: string; emoji: string } => {
    if (score >= 4.5) return { label: 'Excellent', color: 'text-[#3fb950]', emoji: '🌟' };
    if (score >= 4.0) return { label: 'Very Good', color: 'text-[#58a6ff]', emoji: '✨' };
    if (score >= 3.5) return { label: 'Good', color: 'text-[#79c0ff]', emoji: '👍' };
    if (score >= 3.0) return { label: 'Fair', color: 'text-[#d29922]', emoji: '⚡' };
    if (score >= 2.5) return { label: 'Needs Work', color: 'text-[#f85149]', emoji: '⚠️' };
    return { label: 'Poor', color: 'text-[#f85149]', emoji: '❌' };
  };

  const overallGrade = getGrade(overallAvg);
  
  // Find best and worst performing metrics
  const sortedScores = [...scoreCards].sort((a, b) => b.value - a.value);
  const bestMetric = sortedScores[0];
  const worstMetric = sortedScores[sortedScores.length - 1];

  return (
    <main className="min-h-screen bg-[#0d1117] p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-[#58a6ff] font-mono text-2xl md:text-3xl mb-2">
                MindEval Benchmark Results
              </h1>
              <p className="text-[#8b949e] text-sm">
                Multi-turn Mental Health Support Evaluation
              </p>
            </div>
            <button
              onClick={fetchResults}
              className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white font-mono rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
          
          <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Model</div>
                <div className="text-[#c9d1d9] font-mono">{results.model}</div>
              </div>
              <div>
                <div className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Interactions</div>
                <div className="text-[#c9d1d9] font-mono">{results.n_interactions}</div>
              </div>
              <div>
                <div className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">Turns per Interaction</div>
                <div className="text-[#c9d1d9] font-mono">{results.n_turns}</div>
              </div>
            </div>
          </div>
        </div>

        {/* TL;DR Section */}
        <div className={`bg-[#161b22] border border-[#58a6ff]/50 rounded-lg p-6 mb-8 transition-all duration-1000 delay-75 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="flex items-start gap-3">
            <div className="text-[#58a6ff] text-2xl font-bold font-mono flex-shrink-0">TL;DR</div>
            <div className="flex-1 space-y-3">
              <p className="text-[#c9d1d9] text-sm leading-relaxed">
                <strong className="text-[#58a6ff]">What is this?</strong> This page shows how well our AI therapist model performs in simulated therapy conversations. We tested it on <strong className="text-[#3fb950]">{results.n_interactions} multi-turn conversations</strong> with virtual patients.
              </p>
              <p className="text-[#c9d1d9] text-sm leading-relaxed">
                <strong className="text-[#58a6ff]">What does it measure?</strong> The evaluation scores the AI on 5 key areas: clinical accuracy, ethical conduct, assessment quality, therapeutic relationship, and communication quality. Each metric is rated on a <strong className="text-[#c9d1d9]">1-5 scale</strong> (5 = excellent, 3 = average, 1 = poor).
              </p>
              <p className="text-[#c9d1d9] text-sm leading-relaxed">
                <strong className="text-[#58a6ff]">What do the scores mean?</strong> Your model scored <strong className="text-[#3fb950]">{overallAvg.toFixed(2)}/5.0 ({(overallAvg / 5 * 100).toFixed(1)}%)</strong> overall, which is <strong className={overallGrade.color.replace('text-', 'text-')}>{overallGrade.label.toLowerCase()}</strong>. Scores above 4.0 are excellent, 3.5+ is good, and below 3.0 needs improvement.
              </p>
              <p className="text-[#8b949e] text-xs italic mt-4 pt-4 border-t border-[#30363d]">
                💡 <strong>Tip:</strong> Hover over the score cards below to see detailed statistics. The progress bars show how close each metric is to a perfect 5.0 score.
              </p>
            </div>
          </div>
        </div>

        {/* Overall Score */}
        <div className={`bg-gradient-to-r from-[#238636]/20 to-[#58a6ff]/20 border border-[#3fb950]/50 rounded-lg p-6 mb-8 transition-all duration-1000 delay-100 ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Target className="w-6 h-6 text-[#3fb950]" />
              <h2 className="text-[#3fb950] font-mono text-xl">Overall Score</h2>
            </div>
            <div className={`text-lg font-bold font-mono ${overallGrade.color}`}>
              {overallGrade.emoji} {overallGrade.label}
            </div>
          </div>
          <div className="flex items-baseline gap-3 mb-2">
            <div className="text-5xl font-bold text-[#3fb950] font-mono">
              {overallAvg.toFixed(2)}
            </div>
            <div className="text-2xl text-[#8b949e] font-mono">/ 5.0</div>
            <div className="ml-auto text-lg text-[#8b949e] font-mono">
              {(overallAvg / 5 * 100).toFixed(1)}%
            </div>
          </div>
          <div className="w-full bg-[#21262d] rounded-full h-3 mb-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-[#3fb950] to-[#58a6ff] h-3 rounded-full transition-all duration-1000 ease-out"
              style={{ 
                width: mounted ? `${(overallAvg / 5) * 100}%` : '0%',
                transitionDelay: '300ms'
              }}
            />
          </div>
          <p className="text-[#8b949e] text-sm">
            Average across {scoreCards.length} evaluation metrics • {results.n_interactions} interactions evaluated
          </p>
        </div>

        {/* Insights */}
        <div className={`grid md:grid-cols-2 gap-4 mb-8 transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="bg-[#161b22] border border-[#3fb950]/50 rounded-lg p-4 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-[#3fb950]" />
              <h3 className="text-[#3fb950] font-mono text-sm">Strongest Area</h3>
            </div>
            <div className="text-lg font-bold text-[#c9d1d9] mb-1">{bestMetric.label}</div>
            <div className="text-2xl font-mono text-[#3fb950]">{bestMetric.value.toFixed(2)}/5.0</div>
            <div className="text-xs text-[#8b949e] mt-1">
              {(bestMetric.value / 5 * 100).toFixed(1)}% of maximum
            </div>
          </div>
          <div className="bg-[#161b22] border border-[#f85149]/50 rounded-lg p-4 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-5 h-5 text-[#f85149]" />
              <h3 className="text-[#f85149] font-mono text-sm">Needs Improvement</h3>
            </div>
            <div className="text-lg font-bold text-[#c9d1d9] mb-1">{worstMetric.label}</div>
            <div className="text-2xl font-mono text-[#f85149]">{worstMetric.value.toFixed(2)}/5.0</div>
            <div className="text-xs text-[#8b949e] mt-1">
              {(worstMetric.value / 5 * 100).toFixed(1)}% of maximum
            </div>
          </div>
        </div>

        {/* Score Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {scoreCards.map((card, idx) => (
            <ScoreCardComponent key={idx} card={card} delay={idx * 100} mounted={mounted} />
          ))}
        </div>

        {/* Score Distribution Chart */}
        <div className={`bg-[#161b22] border border-[#30363d] rounded-lg p-6 mb-8 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-[#58a6ff] font-mono text-xl mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Score Distribution
          </h2>
          <div className="space-y-4">
            {scoreCards.map((card, idx) => (
              <ScoreBar key={idx} card={card} delay={idx * 50} mounted={mounted} />
            ))}
          </div>
        </div>

        {/* Statistics Table */}
        <div className={`bg-[#161b22] border border-[#30363d] rounded-lg p-6 mb-8 transition-all duration-1000 delay-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-[#58a6ff] font-mono text-xl mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Detailed Statistics
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-sm">
              <thead>
                <tr className="border-b border-[#30363d]">
                  <th className="text-left py-3 px-4 text-[#8b949e]">Metric</th>
                  <th className="text-right py-3 px-4 text-[#8b949e]">Mean</th>
                  <th className="text-right py-3 px-4 text-[#8b949e]">Std Dev</th>
                  <th className="text-right py-3 px-4 text-[#8b949e]">Min</th>
                  <th className="text-right py-3 px-4 text-[#8b949e]">Max</th>
                </tr>
              </thead>
              <tbody>
                {scoreCards.map((card, idx) => (
                  <tr 
                    key={idx} 
                    className="border-b border-[#21262d] hover:bg-[#0d1117] transition-all duration-300"
                    style={{
                      animation: mounted ? `fadeInRow 0.5s ease-out ${idx * 50}ms both` : 'none'
                    }}
                  >
                    <td className="py-3 px-4 text-[#c9d1d9]">{card.label}</td>
                    <td className="py-3 px-4 text-right text-[#3fb950] font-bold">
                      {card.format ? card.format(card.value) : card.value.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right text-[#8b949e]">
                      {card.std !== undefined ? (card.format ? card.format(card.std) : card.std.toFixed(2)) : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right text-[#8b949e]">
                      {card.min !== undefined ? (card.format ? card.format(card.min) : card.min.toFixed(2)) : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right text-[#8b949e]">
                      {card.max !== undefined ? (card.format ? card.format(card.max) : card.max.toFixed(2)) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Credits & Citation */}
        <div className={`bg-[#161b22] border border-[#30363d] rounded-lg p-6 mb-8 transition-all duration-1000 delay-900 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-[#58a6ff] font-mono text-xl mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Benchmark Information
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-[#c9d1d9] font-mono text-sm mb-2">Evaluation Framework</h3>
              <p className="text-[#8b949e] text-sm mb-2">
                This evaluation uses <strong className="text-[#c9d1d9]">MindEval</strong>, a benchmark for evaluating language models on multi-turn mental health support conversations.
              </p>
              <div className="bg-[#0d1117] rounded-lg p-4 border border-[#21262d] font-mono text-xs">
                <div className="text-[#8b949e] mb-2">Citation:</div>
                <div className="text-[#c9d1d9] leading-relaxed">
                  @misc{'{'}pombal2025mindevalbenchmarkinglanguagemodels,
                  <br />
                  {'  '}title={'{'}{'MindEval: Benchmarking Language Models on Multi-turn Mental Health Support}'},
                  <br />
                  {'  '}author={'{'}{'José Pombal and Maya D\'Eon and Nuno M. Guerreiro and Pedro Henrique Martins and António Farinhas and Ricardo Rei}'},
                  <br />
                  {'  '}year={'{'}{'2025}'},
                  <br />
                  {'  '}eprint={'{'}{'2511.18491}'},
                  <br />
                  {'  '}archivePrefix={'{'}{'arXiv}'},
                  <br />
                  {'  '}primaryClass={'{'}{'cs.CL}'},
                  <br />
                  {'  '}url={'{'}{'https://arxiv.org/abs/2511.18491}'},
                  <br />
                  {'}'}
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-[#c9d1d9] font-mono text-sm mb-2">Repository & Resources</h3>
              <div className="flex flex-wrap gap-2">
                <a
                  href="https://github.com/SWORDHealth/mind-eval"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white font-mono text-xs rounded transition-colors flex items-center gap-1"
                >
                  <span>GitHub Repository</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
                <a
                  href="https://arxiv.org/abs/2511.18491"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 border border-[#30363d] hover:border-[#58a6ff] text-[#c9d1d9] hover:text-[#58a6ff] font-mono text-xs rounded transition-colors flex items-center gap-1"
                >
                  <span>arXiv Paper</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h3 className="text-[#c9d1d9] font-mono text-sm mb-2">Authors</h3>
              <p className="text-[#8b949e] text-sm">
                José Pombal, Maya D'Eon, Nuno M. Guerreiro, Pedro Henrique Martins, António Farinhas, Ricardo Rei
              </p>
              <p className="text-[#6e7681] text-xs mt-1">
                AI Research team at SWORD Health
              </p>
            </div>
            <div className="pt-4 border-t border-[#30363d]">
              <p className="text-[#6e7681] text-xs">
                This evaluation framework is provided by the MindEval project. Please cite the paper if you use these results in your research.
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className={`flex justify-center gap-4 transition-all duration-1000 delay-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <Link
            href="/"
            className="px-6 py-3 bg-[#238636] hover:bg-[#2ea043] text-white font-mono rounded-lg transition-colors flex items-center gap-2"
          >
            ← Back to Home
          </Link>
          <Link
            href="/chat"
            className="px-6 py-3 border border-[#30363d] hover:border-[#58a6ff] text-[#c9d1d9] hover:text-[#58a6ff] font-mono rounded-lg transition-colors flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Try Chat
          </Link>
        </div>
      </div>
    </main>
  );
}

function ScoreCardComponent({ card, delay = 0, mounted = false }: { card: ScoreCard; delay?: number; mounted?: boolean }) {
  // On 1-5 scale: 4+ = excellent, 3.5+ = good, 3+ = fair, <3 = needs work
  const getScoreColor = (score: number) => {
    if (score >= 4.0) return 'text-[#3fb950] border-[#3fb950]/50';
    if (score >= 3.5) return 'text-[#58a6ff] border-[#58a6ff]/50';
    if (score >= 3.0) return 'text-[#d29922] border-[#d29922]/50';
    return 'text-[#f85149] border-[#f85149]/50';
  };
  
  const colorClass = getScoreColor(card.value);
  const percentage = (card.value / 5) * 100;
  
  return (
    <div 
      className={`bg-[#161b22] border ${colorClass} rounded-lg p-4 hover:border-opacity-100 hover:scale-105 transition-all duration-300 ${
        mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'
      }`}
      style={{
        transitionDelay: `${delay}ms`
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="text-[#8b949e] text-xs uppercase tracking-wider">{card.label}</div>
        {card.value >= 3.5 ? (
          <CheckCircle2 className="w-4 h-4 text-[#3fb950]" />
        ) : (
          <XCircle className="w-4 h-4 text-[#f85149]" />
        )}
      </div>
      <div className="flex items-baseline gap-2 mb-2">
        <div className={`text-2xl font-bold font-mono ${colorClass}`}>
          {card.format ? card.format(card.value) : card.value.toFixed(2)}
        </div>
        <div className="text-sm text-[#8b949e] font-mono">/ 5.0</div>
        <div className="ml-auto text-xs text-[#8b949e] font-mono">
          {percentage.toFixed(0)}%
        </div>
      </div>
      <div className="w-full bg-[#21262d] rounded-full h-2 mb-2">
        <div 
          className={`h-2 rounded-full transition-all duration-1000 ${
            card.value >= 4.0 ? 'bg-[#3fb950]' :
            card.value >= 3.5 ? 'bg-[#58a6ff]' :
            card.value >= 3.0 ? 'bg-[#d29922]' :
            'bg-[#f85149]'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {card.std !== undefined && (
        <div className="text-[#6e7681] text-xs font-mono">
          ±{card.format ? card.format(card.std) : card.std.toFixed(2)} • Range: {card.min?.toFixed(1)}-{card.max?.toFixed(1)}
        </div>
      )}
    </div>
  );
}

function ScoreBar({ card, delay = 0, mounted = false }: { card: ScoreCard; delay?: number; mounted?: boolean }) {
  // On 1-5 scale, convert to percentage of max (5.0)
  const percentage = (card.value / 5) * 100;
  
  const getBarColor = (score: number) => {
    if (score >= 4.0) return 'bg-[#3fb950]';
    if (score >= 3.5) return 'bg-[#58a6ff]';
    if (score >= 3.0) return 'bg-[#d29922]';
    return 'bg-[#f85149]';
  };
  
  return (
    <div 
      className={`space-y-2 transition-all duration-500 ${
        mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'
      }`}
      style={{
        transitionDelay: `${delay}ms`
      }}
    >
      <div className="flex justify-between items-center text-sm">
        <span className="text-[#c9d1d9] font-medium">{card.label}</span>
        <div className="flex items-center gap-3">
          <span className="text-[#8b949e] font-mono text-xs">
            {card.min?.toFixed(1)} - {card.max?.toFixed(1)}
          </span>
          <span className="text-[#c9d1d9] font-mono font-bold">
            {card.format ? card.format(card.value) : card.value.toFixed(2)}/5.0
          </span>
          <span className="text-[#8b949e] font-mono text-xs">
            ({percentage.toFixed(0)}%)
          </span>
        </div>
      </div>
      <div className="relative h-6 bg-[#21262d] rounded overflow-hidden">
        <div 
          className={`absolute top-0 bottom-0 left-0 rounded transition-all duration-1000 ${getBarColor(card.value)}`}
          style={{ 
            width: mounted ? `${percentage}%` : '0%',
            transitionDelay: `${delay + 200}ms`
          }}
        />
        <div className="absolute inset-0 flex items-center justify-end pr-2">
          <span className="text-xs text-white font-mono font-bold">{percentage.toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
