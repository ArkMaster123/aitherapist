'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import { 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  ArrowLeft,
  AlertTriangle,
  Activity,
  Volume2,
  VolumeX,
  Loader2
} from 'lucide-react';

declare global {
  interface Window {
    Recorder: any;
    'ogg-opus-decoder': any;
  }
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export default function VoiceChatPage() {
  const [recorder, setRecorder] = useState<any>(null);
  const [amplitude, setAmplitude] = useState(0);
  const [muted, setMuted] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [completedSentences, setCompletedSentences] = useState<string[]>([]);
  const [pendingSentence, setPendingSentence] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [scriptsLoaded, setScriptsLoaded] = useState(false);
  const [modelWarmingUp, setModelWarmingUp] = useState(false);
  const [connectionStartTime, setConnectionStartTime] = useState<number | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const scheduledEndTimeRef = useRef(0);
  const decoderRef = useRef<any>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const getWebSocketURL = () => {
    const modalAppName = process.env.NEXT_PUBLIC_MODAL_APP_NAME || 'therapist-voice-chat';
    const modalUsername = process.env.NEXT_PUBLIC_MODAL_USERNAME || 'your-username';
    return `wss://${modalUsername}--${modalAppName}-moshi-web.modal.run/ws`;
  };

  const scheduleAudioPlayback = useCallback((newAudioData: Float32Array) => {
    if (!audioContextRef.current) return;

    const audioContext = audioContextRef.current;
    const sampleRate = audioContext.sampleRate;
    const nowTime = audioContext.currentTime;

    const newBuffer = audioContext.createBuffer(1, newAudioData.length, sampleRate);
    newBuffer.copyToChannel(new Float32Array(newAudioData), 0);
    const sourceNode = audioContext.createBufferSource();
    sourceNode.buffer = newBuffer;
    sourceNode.connect(audioContext.destination);

    const startTime = Math.max(scheduledEndTimeRef.current, nowTime);
    sourceNode.start(startTime);
    scheduledEndTimeRef.current = startTime + newBuffer.duration;

    if (sourceNodeRef.current && sourceNodeRef.current.buffer) {
      const currentEndTime = scheduledEndTimeRef.current;
      if (currentEndTime <= nowTime) {
        sourceNodeRef.current.disconnect();
      }
    }
    sourceNodeRef.current = sourceNode;
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const RecorderClass = window.Recorder;
      if (!RecorderClass) {
        throw new Error('Opus recorder not loaded');
      }

      const newRecorder = new RecorderClass({
        encoderPath: "https://cdn.jsdelivr.net/npm/opus-recorder@latest/dist/encoderWorker.min.js",
        streamPages: true,
        encoderApplication: 2049,
        encoderFrameSize: 80,
        encoderSampleRate: 24000,
        maxFramesPerPage: 1,
        numberOfChannels: 1,
      });

      newRecorder.ondataavailable = async (arrayBuffer: ArrayBuffer) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          await socketRef.current.send(arrayBuffer);
        }
      };

      await newRecorder.start();
      setRecorder(newRecorder);
      setMuted(false);
      newRecorder.setRecordingGain(1);

      const analyzerContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyzer = analyzerContext.createAnalyser();
      analyzer.fftSize = 256;
      analyzerRef.current = analyzer;
      const sourceNode = analyzerContext.createMediaStreamSource(stream);
      sourceNode.connect(analyzer);

      const processAudio = () => {
        if (!analyzerRef.current) return;
        const dataArray = new Uint8Array(analyzer.frequencyBinCount);
        analyzer.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        setAmplitude(average);
        animationFrameRef.current = requestAnimationFrame(processAudio);
      };
      processAudio();

    } catch (error) {
      console.error('Failed to start recording:', error);
      setErrorMessage('Microphone access denied. Please allow microphone access.');
    }
  };

  const connect = async () => {
    if (!scriptsLoaded) {
      setErrorMessage('Audio libraries are still loading. Please wait...');
      return;
    }

    setConnectionStatus('connecting');
    setErrorMessage('');

    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 48000 });

      const OggOpusDecoder = window['ogg-opus-decoder']?.OggOpusDecoder;
      if (!OggOpusDecoder) {
        throw new Error('Opus decoder not loaded. Please refresh the page.');
      }
      const decoder = new OggOpusDecoder();
      await decoder.ready;
      decoderRef.current = decoder;

      const wsUrl = getWebSocketURL();
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('connected');
        setModelWarmingUp(true);
        setConnectionStartTime(Date.now());
        startRecording();
        
        // Clear warming up message after 60 seconds or first response
        setTimeout(() => {
          setModelWarmingUp(false);
        }, 60000);
      };

      socket.onmessage = async (event) => {
        const arrayBuffer = await event.data.arrayBuffer();
        const view = new Uint8Array(arrayBuffer);
        const tag = view[0];
        const payload = arrayBuffer.slice(1);

        if (tag === 1 && decoderRef.current) {
          try {
            const { channelData, samplesDecoded } = await decoderRef.current.decode(new Uint8Array(payload));
            if (samplesDecoded > 0) {
              scheduleAudioPlayback(channelData[0]);
            }
          } catch (e) {
            console.error('Decode error:', e);
          }
        }

        if (tag === 2) {
          const decoder = new TextDecoder();
          const text = decoder.decode(payload);

          // Clear warming up message on first response
          if (modelWarmingUp) {
            setModelWarmingUp(false);
          }

          setPendingSentence(prevPending => {
            const updatedPending = prevPending + text;
            if (updatedPending.endsWith('.') || updatedPending.endsWith('!') || updatedPending.endsWith('?')) {
              setCompletedSentences(prevCompleted => [...prevCompleted, updatedPending]);
              return '';
            }
            return updatedPending;
          });
        }
      };

      socket.onerror = () => {
        setConnectionStatus('error');
        setErrorMessage('Failed to connect to voice server. Make sure the Modal backend is running.');
      };

      socket.onclose = () => {
        setConnectionStatus('disconnected');
      };

    } catch (error) {
      console.error('Connection error:', error);
      setConnectionStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to connect');
    }
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    if (recorder) {
      recorder.stop();
      setRecorder(null);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    if (decoderRef.current) {
      decoderRef.current.free();
      decoderRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setConnectionStatus('disconnected');
    setMuted(true);
    setAmplitude(0);
    setCompletedSentences([]);
    setPendingSentence('');
    setModelWarmingUp(false);
    setConnectionStartTime(null);
  };

  const toggleMute = () => {
    if (!recorder) return;
    const newMuted = !muted;
    setMuted(newMuted);
    recorder.setRecordingGain(newMuted ? 0 : 1);
  };

  useEffect(() => {
    // Check if scripts are already loaded (e.g., on page refresh)
    if (window.Recorder && window['ogg-opus-decoder']) {
      setScriptsLoaded(true);
    }
    
    return () => {
      disconnect();
    };
  }, []);

  const amplitudePercent = amplitude / 255;
  const pulseSize = 1 + amplitudePercent * 0.5;

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/npm/opus-recorder@latest/dist/recorder.min.js"
        onLoad={() => {
          console.log('[v0] Opus recorder loaded');
          // Check if both scripts are loaded
          if (window.Recorder && window['ogg-opus-decoder']) {
            setScriptsLoaded(true);
          }
        }}
        onError={(e) => {
          console.error('[v0] Failed to load opus recorder:', e);
          setErrorMessage('Failed to load audio recorder. Please refresh the page.');
        }}
      />
      <Script
        src="https://cdn.jsdelivr.net/npm/ogg-opus-decoder/dist/ogg-opus-decoder.min.js"
        onLoad={() => {
          console.log('[v0] Opus decoder loaded');
          // Check if both scripts are loaded
          if (window.Recorder && window['ogg-opus-decoder']) {
            setScriptsLoaded(true);
          }
        }}
        onError={(e) => {
          console.error('[v0] Failed to load opus decoder:', e);
          setErrorMessage('Failed to load audio decoder. Please refresh the page.');
        }}
      />

      <main className="min-h-screen bg-[#0d1117] flex flex-col items-center p-4 md:p-8">
        <div className="fixed inset-0 pointer-events-none z-50 opacity-[0.03]" 
             style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)' }} />
        
        <div className="w-full max-w-2xl">
          <div className="border border-[#30363d] rounded-lg overflow-hidden shadow-2xl bg-[#0d1117]">
            <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-[#30363d]">
              <div className="flex items-center gap-3">
                <Link 
                  href="/"
                  className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <span className="text-sm text-[#8b949e] font-mono">voice-session</span>
              </div>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-[#3fb950]' :
                  connectionStatus === 'connecting' ? 'bg-[#d29922] animate-pulse' :
                  connectionStatus === 'error' ? 'bg-[#f85149]' :
                  'bg-[#8b949e]'
                }`} />
                <span className="text-xs text-[#8b949e] font-mono">
                  {connectionStatus === 'connected' ? 'LIVE' :
                   connectionStatus === 'connecting' ? 'CONNECTING...' :
                   connectionStatus === 'error' ? 'ERROR' :
                   'OFFLINE'}
                </span>
              </div>
            </div>

            <div className="p-6 md:p-8 font-mono">
              <div className="text-center mb-8">
                <h1 className="text-[#58a6ff] text-xl md:text-2xl mb-2 flex items-center justify-center gap-2">
                  <Activity className="w-6 h-6" />
                  Voice Therapy Session
                </h1>
                <p className="text-[#8b949e] text-sm">
                  Speak naturally • AI responds in real-time
                </p>
              </div>

              <div className="flex flex-col items-center mb-8">
                <div 
                  className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-150 ${
                    connectionStatus === 'connected' 
                      ? muted ? 'bg-[#21262d]' : 'bg-[#238636]'
                      : 'bg-[#21262d]'
                  }`}
                  style={{
                    transform: connectionStatus === 'connected' && !muted ? `scale(${pulseSize})` : 'scale(1)',
                    boxShadow: connectionStatus === 'connected' && !muted 
                      ? `0 0 ${60 * amplitudePercent}px rgba(63, 185, 80, 0.5)` 
                      : 'none'
                  }}
                >
                  {connectionStatus === 'connected' ? (
                    muted ? (
                      <MicOff className="w-12 h-12 text-[#8b949e]" />
                    ) : (
                      <Mic className="w-12 h-12 text-white" />
                    )
                  ) : connectionStatus === 'connecting' ? (
                    <Loader2 className="w-12 h-12 text-[#d29922] animate-spin" />
                  ) : (
                    <Mic className="w-12 h-12 text-[#8b949e]" />
                  )}
                </div>

                <div className="flex gap-4 mt-6">
                  {!scriptsLoaded ? (
                    <button
                      disabled
                      className="flex items-center gap-2 px-6 py-3 bg-[#21262d] text-[#8b949e] rounded-lg cursor-not-allowed"
                    >
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Loading audio libraries...</span>
                    </button>
                  ) : connectionStatus === 'disconnected' || connectionStatus === 'error' ? (
                    <button
                      onClick={connect}
                      className="flex items-center gap-2 px-6 py-3 bg-[#238636] hover:bg-[#2ea043] text-white rounded-lg transition-colors"
                    >
                      <Phone className="w-5 h-5" />
                      <span>Start Session</span>
                    </button>
                  ) : connectionStatus === 'connecting' ? (
                    <button
                      disabled
                      className="flex items-center gap-2 px-6 py-3 bg-[#21262d] text-[#8b949e] rounded-lg cursor-not-allowed"
                    >
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Connecting...</span>
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={toggleMute}
                        className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-colors ${
                          muted 
                            ? 'bg-[#f85149] hover:bg-[#da3633] text-white' 
                            : 'bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9]'
                        }`}
                      >
                        {muted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                        <span>{muted ? 'Unmute' : 'Mute'}</span>
                      </button>
                      <button
                        onClick={disconnect}
                        className="flex items-center gap-2 px-4 py-3 bg-[#f85149] hover:bg-[#da3633] text-white rounded-lg transition-colors"
                      >
                        <PhoneOff className="w-5 h-5" />
                        <span>End</span>
                      </button>
                    </>
                  )}
                </div>
              </div>

              {modelWarmingUp && connectionStatus === 'connected' && (
                <div className="bg-[#d2992226] border border-[#d29922] rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <Loader2 className="w-5 h-5 text-[#d29922] flex-shrink-0 mt-0.5 animate-spin" />
                    <div className="text-sm">
                      <p className="text-[#d29922] font-bold mb-1">Model is warming up...</p>
                      <p className="text-[#f8d7da]">
                        The AI model is loading. This typically takes 50-60 seconds. Please wait - you'll hear a response soon.
                        {connectionStartTime && (
                          <span className="block mt-1 text-xs text-[#8b949e]">
                            Connected {Math.floor((Date.now() - connectionStartTime) / 1000)}s ago
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {errorMessage && (
                <div className="bg-[#f8514926] border border-[#f85149] rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-[#f85149] flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-[#f8d7da]">{errorMessage}</p>
                  </div>
                </div>
              )}

              <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] min-h-[200px] max-h-[300px] overflow-y-auto">
                <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                  <span className="text-[#3fb950]">$</span> transcript
                </div>
                {modelWarmingUp && connectionStatus === 'connected' && completedSentences.length === 0 && !pendingSentence && (
                  <p className="text-[#6e7681] text-sm italic mb-2">
                    Waiting for model to respond... This may take 50-60 seconds on first connection.
                  </p>
                )}
                {(completedSentences.length > 0 || pendingSentence) ? (
                  <div className="space-y-2 flex flex-col-reverse">
                    {[...completedSentences, pendingSentence].filter(s => s).map((sentence, index) => (
                      <p 
                        key={index} 
                        className={`text-sm ${
                          index === 0 && pendingSentence 
                            ? 'text-[#8b949e]' 
                            : 'text-[#c9d1d9]'
                        }`}
                      >
                        {sentence}
                        {index === 0 && pendingSentence && (
                          <span className="inline-block w-2 h-4 bg-[#3fb950] ml-1 animate-pulse" />
                        )}
                      </p>
                    )).reverse()}
                  </div>
                ) : (
                  <p className="text-[#6e7681] text-sm italic">
                    {connectionStatus === 'connected' 
                      ? 'Listening... Start speaking.' 
                      : 'Start a session to begin.'}
                  </p>
                )}
              </div>

              <div className="bg-[#f8514926] border border-[#f85149] rounded-lg p-4 mt-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[#f85149] flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-[#f85149] font-bold mb-1">Research Use Only</p>
                    <p className="text-[#f8d7da]">
                      This is an experimental AI. Not a substitute for professional mental health care.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
