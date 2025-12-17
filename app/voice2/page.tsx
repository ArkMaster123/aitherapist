"use client";

import { useRef, useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import { VoicePoweredOrb } from "@/components/ui/voice-powered-orb";
import { 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  ArrowLeft,
  AlertTriangle,
  Activity,
  Loader2,
  Timer,
  Zap,
  Trophy
} from 'lucide-react';

declare global {
  interface Window {
    Recorder: any;
    'ogg-opus-decoder': any;
  }
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';
type PipelineType = 'moshi' | 'groq-ultra-fast';
type TTSService = 'kokoro' | 'chatterbox' | 'vibevoice';
type LLMService = 'groq' | 'therapist';

interface PipelineMetrics {
  sttLatency: number;
  llmLatency: number;
  ttsLatency: number;
  totalLatency: number;
  transcript: string;
  response: string;
}

export default function Voice2Page() {
  // Pipeline selection
  const [selectedPipeline, setSelectedPipeline] = useState<PipelineType>('groq-ultra-fast');
  const [selectedTTS, setSelectedTTS] = useState<TTSService>('kokoro');
  const [kokoroVoice, setKokoroVoice] = useState<string>('');
  const [kokoroVoices, setKokoroVoices] = useState<string[]>([]);
  const [selectedLLM, setSelectedLLM] = useState<LLMService>('groq');
  const [groqModel, setGroqModel] = useState<string>('llama-3.3-70b-versatile');
  const [groqModels, setGroqModels] = useState<Array<{id: string, created: number}>>([]);
  const [therapistAvailable, setTherapistAvailable] = useState<boolean>(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string, content: string}>>([]);
  
  // Recording state
  const [recorder, setRecorder] = useState<any>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [scriptsLoaded, setScriptsLoaded] = useState(false);
  const [modelWarmingUp, setModelWarmingUp] = useState(false);
  const [voiceDetected, setVoiceDetected] = useState(false);
  const [amplitude, setAmplitude] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  
  // Metrics tracking
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [completedSentences, setCompletedSentences] = useState<string[]>([]);
  const [pendingSentence, setPendingSentence] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  
  // Audio refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const scheduledEndTimeRef = useRef(0);
  const decoderRef = useRef<any>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  const [llmTtsUrl, setLlmTtsUrl] = useState<string | null>(null);
  const [kokoroTtsUrl, setKokoroTtsUrl] = useState<string | null>(null);
  const [kokoroTtsHttpUrl, setKokoroTtsHttpUrl] = useState<string | null>(null);
  const [chatterboxTtsUrl, setChatterboxTtsUrl] = useState<string | null>(null);
  const [vibevoiceTtsUrl, setVibevoiceTtsUrl] = useState<string | null>(null);

  // Fetch WebSocket URLs
  useEffect(() => {
    // Moshi pipeline URL
    fetch('/api/voice/ws-url')
      .then(res => res.json())
      .then(data => {
        if (data.wsUrl) setWsUrl(data.wsUrl);
      })
      .catch(err => console.error('Failed to fetch Moshi URL:', err));
    
    // LLM+TTS pipeline URL (for Groq pipeline)
    fetch('/api/voice2/llm-tts-url')
      .then(res => res.json())
      .then(data => {
        if (data.wsUrl) setLlmTtsUrl(data.wsUrl);
      })
      .catch(err => console.error('Failed to fetch LLM+TTS URL:', err));
    
    // TTS service URLs
    fetch('/api/voice2/kokoro-tts-url')
      .then(res => res.json())
      .then(data => {
        if (data.wsUrl) setKokoroTtsUrl(data.wsUrl);
        if (data.httpUrl) setKokoroTtsHttpUrl(data.httpUrl);
      })
      .catch(err => console.error('Failed to fetch Kokoro URL:', err));
    
    fetch('/api/voice2/chatterbox-tts-url')
      .then(res => res.json())
      .then(data => {
        if (data.wsUrl) setChatterboxTtsUrl(data.wsUrl);
      })
      .catch(err => console.error('Failed to fetch Chatterbox URL:', err));
    
    fetch('/api/voice2/tts-url')
      .then(res => res.json())
      .then(data => {
        if (data.wsUrl) setVibevoiceTtsUrl(data.wsUrl);
      })
      .catch(err => console.error('Failed to fetch VibeVoice URL:', err));
    
    // Fetch available Groq models
    fetch('/api/groq-llm')
      .then(res => res.json())
      .then(data => {
        if (data.models && Array.isArray(data.models)) {
          setGroqModels(data.models);
          // Set default to fastest model if available
          const fastModel = data.models.find((m: any) => 
            m.id.includes('llama-3.3-70b') || 
            m.id.includes('llama-3.1-8b') ||
            m.id.includes('mixtral-8x7b')
          );
          if (fastModel) {
            setGroqModel(fastModel.id);
          }
        }
      })
      .catch(err => console.error('Failed to fetch Groq models:', err));
    
    // Check if therapist model is available
    fetch('/api/therapist-llm')
      .then(res => res.json())
      .then(data => {
        setTherapistAvailable(data.available || false);
      })
      .catch(err => console.error('Failed to check therapist model:', err));
  }, []);

  // Fetch Kokoro voices
  useEffect(() => {
    if (kokoroTtsHttpUrl) {
      fetch(kokoroTtsHttpUrl.replace('/tts', '/voices'))
        .then(res => res.json())
        .then(data => {
          if (data.voices && Array.isArray(data.voices)) {
            setKokoroVoices(data.voices);
            if (data.voices.length > 0 && !kokoroVoice) {
              setKokoroVoice(data.voices[0]);
            }
          }
        })
        .catch(err => console.error('Failed to fetch Kokoro voices:', err));
    }
  }, [kokoroTtsHttpUrl, kokoroVoice]);

  const scheduleAudioPlayback = useCallback((newAudioData: Float32Array) => {
    if (!audioContextRef.current) return;
    const audioContext = audioContextRef.current;
    const sampleRate = audioContext.sampleRate;
    const numberOfChannels = 1;
    const nowTime = audioContext.currentTime;

    const newBuffer = audioContext.createBuffer(numberOfChannels, newAudioData.length, sampleRate);
    newBuffer.copyToChannel(new Float32Array(newAudioData), 0);
    const sourceNode = audioContext.createBufferSource();
    sourceNode.buffer = newBuffer;
    sourceNode.connect(audioContext.destination);

    const startTime = Math.max(scheduledEndTimeRef.current, nowTime);
    sourceNode.start(startTime);
    scheduledEndTimeRef.current = startTime + newBuffer.duration;
    (sourceNode as any).startTime = startTime;

    if (sourceNodeRef.current && sourceNodeRef.current.buffer) {
      const currentEndTime = (sourceNodeRef.current as any).startTime + sourceNodeRef.current.buffer.duration;
      if (currentEndTime <= nowTime) {
        sourceNodeRef.current.disconnect();
      }
    }
    sourceNodeRef.current = sourceNode;
  }, []);

  // Groq STT + Selected TTS Pipeline
  const processGroqPipeline = async (audioBlob: Blob) => {
    const metricsStart = performance.now();
    
    try {
      // 1. STT: Groq API
      const sttStart = performance.now();
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');
      
      const sttResponse = await fetch('/api/groq-stt', {
        method: 'POST',
        body: formData,
      });
      
      if (!sttResponse.ok) {
        const errorData = await sttResponse.json().catch(() => ({}));
        throw new Error(errorData.error || 'Groq STT failed');
      }
      
      const sttData = await sttResponse.json();
      const sttLatency = performance.now() - sttStart;
      const transcript = sttData.text;
      
      if (!transcript || transcript.trim().length === 0) {
        setErrorMessage('No speech detected. Please try again.');
        return;
      }
      
      // Update transcript immediately
      setCompletedSentences([transcript]);
      setPendingSentence('Thinking...');
      
      // 2. LLM: Selected LLM Service (Groq or Fine-tuned Therapist)
      const llmStart = performance.now();
      const llmMessages = [
        ...conversationHistory,
        { role: 'user', content: transcript }
      ];
      
      let llmResponse;
      if (selectedLLM === 'therapist') {
        // Use fine-tuned therapist model
        llmResponse = await fetch('/api/therapist-llm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: llmMessages,
            temperature: 0.7,
            max_tokens: 1024,
          }),
        });
      } else {
        // Use Groq LLM
        llmResponse = await fetch('/api/groq-llm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: llmMessages,
            model: groqModel,
            temperature: 0.7,
            max_tokens: 1024,
          }),
        });
      }
      
      if (!llmResponse.ok) {
        const errorData = await llmResponse.json().catch(() => ({}));
        throw new Error(errorData.error || `${selectedLLM} LLM failed`);
      }
      
      const llmData = await llmResponse.json();
      const llmLatency = performance.now() - llmStart;
      const responseText = llmData.text;
      
      // Update conversation history
      setConversationHistory([
        ...llmMessages,
        { role: 'assistant', content: responseText }
      ]);
      
      // Update UI with response
      setCompletedSentences([transcript, responseText]);
      setPendingSentence('Generating speech...');
      
      // 3. TTS: Selected TTS Service
      const ttsStart = performance.now();
      let audioData: ArrayBuffer | null = null;
      let sampleRate = 24000;
      
      const ttsUrl = selectedTTS === 'kokoro' ? kokoroTtsUrl :
                     selectedTTS === 'chatterbox' ? chatterboxTtsUrl :
                     vibevoiceTtsUrl;
      
      if (!ttsUrl) {
        throw new Error(`${selectedTTS} TTS URL not available`);
      }
      
      console.log(`[TTS ${selectedTTS}] Connecting to WebSocket: ${ttsUrl}`);
      
      // Validate URL format
      if (!ttsUrl.startsWith('wss://')) {
        throw new Error(`Invalid WebSocket URL format for ${selectedTTS}: ${ttsUrl}. Must start with wss://`);
      }
      
      const ws = new WebSocket(ttsUrl);
      
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          ws.close();
          reject(new Error(`TTS timeout after 30s for ${selectedTTS}`));
        }, 30000);
        
        ws.onopen = () => {
          console.log(`[TTS ${selectedTTS}] ✅ WebSocket opened successfully`);
          // Send LLM response text to TTS service
          const messageToSend = selectedTTS === 'kokoro' 
            ? JSON.stringify({ text: responseText, voice: kokoroVoice || undefined })
            : JSON.stringify({ text: responseText });
          
          console.log(`[TTS ${selectedTTS}] 📤 Sending message (${messageToSend.length} chars):`, messageToSend.substring(0, 100));
          try {
            ws.send(messageToSend);
            console.log(`[TTS ${selectedTTS}] ✅ Message sent successfully`);
          } catch (sendError) {
            console.error(`[TTS ${selectedTTS}] ❌ Error sending message:`, sendError);
            clearTimeout(timeout);
            reject(new Error(`Failed to send message to ${selectedTTS}: ${sendError}`));
          }
        };
        
        ws.onmessage = (event) => {
          console.log(`Received message from ${selectedTTS}, type:`, event.data instanceof ArrayBuffer ? 'ArrayBuffer' : typeof event.data);
          const data = event.data;
          if (data instanceof ArrayBuffer) {
            const view = new Uint8Array(data);
            const tag = view[0];
            const payload = data.slice(1);
            
            console.log(`Message tag: 0x${tag.toString(16)}, payload size: ${payload.byteLength}`);
            
            if (tag === 0x01) {
              // Audio data
              if (selectedTTS === 'kokoro' && payload.byteLength >= 6) {
                // Kokoro format: [tag][sample_rate:4][voice_len:2][voice][audio]
                const srBytes = new Uint8Array(payload.slice(0, 4));
                sampleRate = new DataView(srBytes.buffer).getUint32(0, false);
                const voiceLen = new DataView(payload.buffer, 4, 2).getUint16(0, false);
                audioData = payload.slice(6 + voiceLen);
                console.log(`Kokoro: sample_rate=${sampleRate}, audio_size=${audioData.byteLength}`);
              } else if ((selectedTTS === 'vibevoice' || selectedTTS === 'chatterbox') && payload.byteLength >= 4) {
                // VibeVoice and Chatterbox format: [tag][sample_rate:4][audio]
                // Create a new ArrayBuffer view for the sample rate bytes
                const srArrayBuffer = payload.slice(0, 4);
                sampleRate = new DataView(srArrayBuffer).getUint32(0, false);
                audioData = payload.slice(4);
                console.log(`${selectedTTS}: sample_rate=${sampleRate}, audio_size=${audioData.byteLength}`);
              } else {
                // Fallback
                console.warn(`Fallback parsing for ${selectedTTS}, payload size: ${payload.byteLength}`);
                audioData = payload;
              }
              
              if (audioData && audioData.byteLength > 0) {
                clearTimeout(timeout);
                resolve();
              } else {
                console.error(`No audio data extracted for ${selectedTTS}`);
              }
            } else if (tag === 0x03) {
              // Error
              const error = new TextDecoder().decode(payload);
              console.error(`TTS error from ${selectedTTS}:`, error);
              clearTimeout(timeout);
              reject(new Error(error));
            } else {
              console.warn(`Unknown message tag: 0x${tag.toString(16)} from ${selectedTTS}`);
            }
          } else {
            console.warn(`Received non-ArrayBuffer message from ${selectedTTS}:`, typeof data);
          }
        };
        
        let hasError = false;
        let errorDetails: any = null;
        
        ws.onerror = (error) => {
          // WebSocket error events don't have much detail, but we can check readyState
          const state = ws.readyState;
          const stateNames = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
          errorDetails = {
            error,
            readyState: stateNames[state] || state,
            readyStateCode: state,
            url: ttsUrl,
            timestamp: new Date().toISOString()
          };
          console.error(`[TTS ${selectedTTS}] ❌ WebSocket error:`, errorDetails);
          hasError = true;
          // Don't reject immediately - wait for onclose which has more info
        };
        
        ws.onclose = (event) => {
          const closeInfo = {
            code: event.code,
            reason: event.reason || 'none',
            wasClean: event.wasClean,
            url: ttsUrl,
            hasError,
            errorDetails,
            audioReceived: audioData ? audioData.byteLength : 0
          };
          console.log(`[TTS ${selectedTTS}] 🔌 WebSocket closed:`, closeInfo);
          
          if (audioData && audioData.byteLength > 0) {
            console.log(`[TTS ${selectedTTS}] ✅ Audio received (${audioData.byteLength} bytes), resolving`);
            clearTimeout(timeout);
            resolve();
          } else {
            clearTimeout(timeout);
            // Provide more helpful error messages based on close code
            let errorMsg = `TTS connection closed without audio`;
            if (event.code === 1006 || hasError) {
              errorMsg = `TTS connection failed (abnormal closure, code ${event.code}). The service at ${ttsUrl} may not be running or the URL is incorrect. ${errorDetails ? `State: ${errorDetails.readyState}` : ''}`;
            } else if (event.code === 1002) {
              errorMsg = `TTS protocol error (code ${event.code}). The URL format might be incorrect: ${ttsUrl}`;
            } else if (event.code === 1003) {
              errorMsg = `TTS unsupported data type (code ${event.code}). Check message format.`;
            } else if (event.code === 1000) {
              errorMsg = `TTS connection closed normally (code ${event.code}) but no audio received. The service may have rejected the request or failed silently.`;
            } else if (event.reason) {
              errorMsg = `TTS connection closed (code ${event.code}): ${event.reason}`;
            } else {
              errorMsg = `TTS connection closed with code ${event.code} without audio. URL: ${ttsUrl}`;
            }
            console.error(`[TTS ${selectedTTS}] ❌ ${errorMsg}`);
            reject(new Error(errorMsg));
          }
        };
      });
      
      const ttsLatency = performance.now() - ttsStart;
      const totalLatency = performance.now() - metricsStart;
      
      // Play audio
      if (audioData && audioContextRef.current) {
        try {
          const audioContext = audioContextRef.current;
          // Convert int16 bytes to Float32Array
          const int16Array = new Int16Array(audioData);
          const float32Array = new Float32Array(int16Array.length);
          for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
          }
          scheduleAudioPlayback(float32Array);
        } catch (e) {
          console.error('Audio playback error:', e);
        }
      }
      
      // Update metrics
      setMetrics({
        sttLatency,
        llmLatency,
        ttsLatency,
        totalLatency,
        transcript,
        response: responseText,
      });
      
      setPendingSentence('');
      
      ws.close();
      
    } catch (error) {
      console.error('Groq pipeline error:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Pipeline failed');
      disconnect();
    }
  };

  // Moshi Pipeline (existing)
  const connectMoshi = async () => {
    if (!scriptsLoaded || !wsUrl) {
      setErrorMessage('Not ready. Please wait...');
      return;
    }

    setConnectionStatus('connecting');
    setErrorMessage('');

    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 48000 });

      const OggOpusDecoder = window['ogg-opus-decoder']?.OggOpusDecoder;
      if (!OggOpusDecoder) {
        throw new Error('Opus decoder not loaded');
      }
      const decoder = new OggOpusDecoder();
      await decoder.ready;
      decoderRef.current = decoder;

      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('connected');
        setModelWarmingUp(true);
        startRecording();
        setTimeout(() => setModelWarmingUp(false), 60000);
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
          if (modelWarmingUp) setModelWarmingUp(false);
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
        setErrorMessage('Failed to connect to voice server.');
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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      if (selectedPipeline === 'groq-ultra-fast') {
        // Use MediaRecorder for Groq pipeline
        const mimeTypes = [
          'audio/webm;codecs=opus',
          'audio/webm',
          'audio/ogg;codecs=opus',
          'audio/mp4'
        ];
        
        let selectedMimeType = '';
        for (const mimeType of mimeTypes) {
          if (MediaRecorder.isTypeSupported(mimeType)) {
            selectedMimeType = mimeType;
            break;
          }
        }
        
        if (!selectedMimeType) {
          throw new Error('No supported audio format found');
        }
        
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: selectedMimeType
        });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          if (audioChunksRef.current.length > 0) {
            const audioBlob = new Blob(audioChunksRef.current, { type: selectedMimeType });
            await processGroqPipeline(audioBlob);
          }
          audioChunksRef.current = [];
        };

        mediaRecorder.start();
        setIsRecording(true);
        
        // Auto-stop after 5 seconds
        setTimeout(() => {
          if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
          }
        }, 5000);
      } else {
        // Use Opus recorder for Moshi
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
      }

      // Audio analysis for orb
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
        setVoiceDetected(average > 10);
        animationFrameRef.current = requestAnimationFrame(processAudio);
      };
      processAudio();

    } catch (error) {
      console.error('Failed to start recording:', error);
      setErrorMessage('Microphone access denied. Please allow microphone access.');
    }
  };

  const stopRecording = () => {
    if (selectedPipeline === 'groq-ultra-fast' && mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
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

    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
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
    setAmplitude(0);
    setVoiceDetected(false);
    setCompletedSentences([]);
    setPendingSentence('');
    setModelWarmingUp(false);
    setMetrics(null);
    setIsRecording(false);
    // Don't clear conversation history on disconnect - keep context
  };

  const startTest = async () => {
    setMetrics(null);
    setCompletedSentences([]);
    setPendingSentence('');
    setErrorMessage('');
    
    if (selectedPipeline === 'groq-ultra-fast') {
      setConnectionStatus('connected');
      await startRecording();
    } else {
      await connectMoshi();
    }
  };

  useEffect(() => {
    if (window.Recorder && window['ogg-opus-decoder']) {
      setScriptsLoaded(true);
    }
    
    return () => {
      disconnect();
    };
  }, []);

  const amplitudePercent = amplitude / 255;

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/npm/opus-recorder@latest/dist/recorder.min.js"
        onLoad={() => {
          if (window.Recorder && window['ogg-opus-decoder']) {
            setScriptsLoaded(true);
          }
        }}
      />
      <Script
        src="https://cdn.jsdelivr.net/npm/ogg-opus-decoder/dist/ogg-opus-decoder.min.js"
        onLoad={() => {
          if (window.Recorder && window['ogg-opus-decoder']) {
            setScriptsLoaded(true);
          }
        }}
      />

      <main className="min-h-screen bg-[#0d1117] flex flex-col items-center p-4 md:p-8">
        <div className="fixed inset-0 pointer-events-none z-50 opacity-[0.03]" 
             style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)' }} />
        
        <div className="w-full max-w-6xl">
          <div className="border border-[#30363d] rounded-lg overflow-hidden shadow-2xl bg-[#0d1117]">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-[#30363d]">
              <div className="flex items-center gap-3">
                <Link 
                  href="/"
                  className="text-[#8b949e] hover:text-[#c9d1d9] transition-colors"
                >
                  <ArrowLeft className="w-5 h-5" />
                </Link>
                <span className="text-sm text-[#8b949e] font-mono">voice-pipeline-benchmark</span>
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
              {/* Title */}
              <div className="text-center mb-8">
                <h1 className="text-[#58a6ff] text-xl md:text-2xl mb-2 flex items-center justify-center gap-2">
                  <Activity className="w-6 h-6" />
                  Voice Pipeline Benchmark
                </h1>
                <p className="text-[#8b949e] text-sm">
                  Compare Moshi vs Groq+LLM+TTS pipelines
                </p>
              </div>

              {/* Pipeline Selection */}
              <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] mb-6">
                <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                  <span className="text-[#3fb950]">$</span> select_pipeline
                </div>
                <div className="flex gap-4 mb-4">
                  <button
                    onClick={() => {
                      setSelectedPipeline('moshi');
                      disconnect();
                    }}
                    className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
                      selectedPipeline === 'moshi'
                        ? 'border-[#58a6ff] bg-[#58a6ff]/10 text-[#58a6ff]'
                        : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                    }`}
                  >
                    <div className="text-sm font-bold mb-1">Moshi Pipeline</div>
                    <div className="text-xs opacity-75">Speech-to-Speech (All-in-One)</div>
                  </button>
                  <button
                    onClick={() => {
                      setSelectedPipeline('groq-ultra-fast');
                      disconnect();
                    }}
                    className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
                      selectedPipeline === 'groq-ultra-fast'
                        ? 'border-[#3fb950] bg-[#3fb950]/10 text-[#3fb950]'
                        : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                    }`}
                  >
                    <div className="text-sm font-bold mb-1">Groq Pipeline</div>
                    <div className="text-xs opacity-75">Groq STT → LLM → TTS</div>
                  </button>
                </div>
                
                {/* TTS Service Selection (only show for Groq pipeline) */}
                {selectedPipeline === 'groq-ultra-fast' && (
                  <div className="mt-4 pt-4 border-t border-[#30363d]">
                    <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                      <span className="text-[#3fb950]">$</span> select_tts_service
                    </div>
                    <div className="grid grid-cols-3 gap-2 mb-4">
                      <button
                        onClick={() => {
                          setSelectedTTS('kokoro');
                          disconnect();
                        }}
                        className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                          selectedTTS === 'kokoro'
                            ? 'border-[#3fb950] bg-[#3fb950]/10 text-[#3fb950]'
                            : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                        }`}
                      >
                        Kokoro
                      </button>
                      <button
                        onClick={() => {
                          setSelectedTTS('chatterbox');
                          disconnect();
                        }}
                        className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                          selectedTTS === 'chatterbox'
                            ? 'border-[#3fb950] bg-[#3fb950]/10 text-[#3fb950]'
                            : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                        }`}
                      >
                        Chatterbox
                      </button>
                      <button
                        onClick={() => {
                          setSelectedTTS('vibevoice');
                          disconnect();
                        }}
                        className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                          selectedTTS === 'vibevoice'
                            ? 'border-[#3fb950] bg-[#3fb950]/10 text-[#3fb950]'
                            : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                        }`}
                      >
                        VibeVoice
                      </button>
                    </div>
                    
                    {/* Kokoro Voice Selection */}
                    {selectedTTS === 'kokoro' && kokoroVoices.length > 0 && (
                      <div className="mt-3">
                        <label className="text-xs text-[#6e7681] mb-2 block">
                          Voice:
                        </label>
                        <select
                          value={kokoroVoice}
                          onChange={(e) => setKokoroVoice(e.target.value)}
                          className="w-full px-3 py-2 bg-[#21262d] border border-[#30363d] rounded-lg text-sm text-[#c9d1d9] focus:outline-none focus:border-[#58a6ff]"
                        >
                          {kokoroVoices.map((voice) => (
                            <option key={voice} value={voice}>
                              {voice}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                    
                    {/* LLM Service Selection */}
                    <div className="mt-3">
                      <label className="text-xs text-[#6e7681] mb-2 block">
                        LLM Service:
                      </label>
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        <button
                          onClick={() => {
                            setSelectedLLM('groq');
                            disconnect();
                          }}
                          className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                            selectedLLM === 'groq'
                              ? 'border-[#3fb950] bg-[#3fb950]/10 text-[#3fb950]'
                              : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                          }`}
                        >
                          Groq
                        </button>
                        <button
                          onClick={() => {
                            setSelectedLLM('therapist');
                            disconnect();
                          }}
                          disabled={!therapistAvailable}
                          className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                            selectedLLM === 'therapist'
                              ? 'border-[#58a6ff] bg-[#58a6ff]/10 text-[#58a6ff]'
                              : 'border-[#30363d] bg-[#21262d] text-[#8b949e] hover:border-[#484f58]'
                          } ${!therapistAvailable ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          Therapist
                          {!therapistAvailable && ' (N/A)'}
                        </button>
                      </div>
                    </div>
                    
                    {/* Groq Model Selection (only show when Groq is selected) */}
                    {selectedLLM === 'groq' && groqModels.length > 0 && (
                      <div className="mt-3">
                        <label className="text-xs text-[#6e7681] mb-2 block">
                          Groq Model:
                        </label>
                        <select
                          value={groqModel}
                          onChange={(e) => {
                            setGroqModel(e.target.value);
                            setConversationHistory([]); // Reset conversation on model change
                          }}
                          className="w-full px-3 py-2 bg-[#21262d] border border-[#30363d] rounded-lg text-sm text-[#c9d1d9] focus:outline-none focus:border-[#58a6ff]"
                        >
                          {groqModels.map((model) => (
                            <option key={model.id} value={model.id}>
                              {model.id}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Orb */}
              <div className="flex justify-center mb-6">
                <div className="w-64 h-64 relative">
                  <VoicePoweredOrb
                    enableVoiceControl={connectionStatus === 'connected' || isRecording}
                    className="rounded-xl overflow-hidden shadow-2xl"
                    onVoiceDetected={setVoiceDetected}
                    voiceSensitivity={1.5 + amplitudePercent * 2}
                  />
                </div>
              </div>

              {/* Controls */}
              <div className="flex justify-center gap-4 mb-6">
                {connectionStatus === 'disconnected' || connectionStatus === 'error' ? (
                  <>
                    <button
                      onClick={startTest}
                      disabled={!scriptsLoaded && selectedPipeline === 'moshi'}
                      className="flex items-center gap-2 px-6 py-3 bg-[#238636] hover:bg-[#2ea043] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Phone className="w-5 h-5" />
                      <span>Start Test</span>
                    </button>
                    {selectedPipeline === 'groq-ultra-fast' && conversationHistory.length > 0 && (
                      <button
                        onClick={() => {
                          setConversationHistory([]);
                          setCompletedSentences([]);
                          setPendingSentence('');
                        }}
                        className="flex items-center gap-2 px-4 py-3 bg-[#21262d] hover:bg-[#30363d] text-[#8b949e] border border-[#30363d] rounded-lg transition-colors"
                      >
                        <span>Clear History</span>
                      </button>
                    )}
                  </>
                ) : (
                  <button
                    onClick={disconnect}
                    className="flex items-center gap-2 px-6 py-3 bg-[#f85149] hover:bg-[#da3633] text-white rounded-lg transition-colors"
                  >
                    <PhoneOff className="w-5 h-5" />
                    <span>Stop Test</span>
                  </button>
                )}
              </div>

              {/* Metrics Display */}
              {metrics && (
                <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] mb-6">
                  <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                    <span className="text-[#3fb950]">$</span> latency_metrics
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard 
                      label="STT" 
                      value={`${metrics.sttLatency.toFixed(0)}ms`}
                      icon={<Mic className="w-4 h-4" />}
                    />
                    <MetricCard 
                      label="LLM" 
                      value={`${metrics.llmLatency.toFixed(0)}ms`}
                      icon={<Activity className="w-4 h-4" />}
                    />
                    <MetricCard 
                      label="TTS" 
                      value={`${metrics.ttsLatency.toFixed(0)}ms`}
                      icon={<Zap className="w-4 h-4" />}
                    />
                    <MetricCard 
                      label="Total" 
                      value={`${metrics.totalLatency.toFixed(0)}ms`}
                      icon={<Timer className="w-4 h-4" />}
                      highlight
                    />
                  </div>
                </div>
              )}

              {/* Transcript Display */}
              <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] min-h-[200px] max-h-[300px] overflow-y-auto mb-6">
                <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                  <span className="text-[#3fb950]">$</span> transcript
                </div>
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
                    {connectionStatus === 'connected' || isRecording
                      ? 'Listening... Start speaking.' 
                      : 'Select a pipeline and start a test.'}
                  </p>
                )}
              </div>

              {/* Pipeline Info */}
              <div className="bg-[#161b22] rounded-lg p-4 border border-[#30363d] mb-6">
                <div className="text-xs text-[#6e7681] mb-3 flex items-center gap-2">
                  <span className="text-[#3fb950]">$</span> pipeline_info
                </div>
                {selectedPipeline === 'moshi' ? (
                  <div className="text-sm text-[#c9d1d9] space-y-2">
                    <p><span className="text-[#58a6ff]">STT:</span> Moshi (integrated)</p>
                    <p><span className="text-[#58a6ff]">LLM:</span> Moshi (integrated)</p>
                    <p><span className="text-[#58a6ff]">TTS:</span> Moshi (integrated)</p>
                    <p className="text-[#8b949e] text-xs mt-2">All-in-one speech-to-speech model</p>
                  </div>
                ) : (
                  <div className="text-sm text-[#c9d1d9] space-y-2">
                    <p><span className="text-[#3fb950]">STT:</span> Groq Whisper Large v3 Turbo (216x real-time)</p>
                    <p><span className="text-[#3fb950]">LLM:</span> {
                      selectedLLM === 'therapist' 
                        ? 'Fine-tuned Therapist Model (Qwen)' 
                        : `Groq ${groqModel}`
                    }</p>
                    <p><span className="text-[#3fb950]">TTS:</span> {
                      selectedTTS === 'kokoro' ? `Kokoro-82m (${kokoroVoice || 'default voice'})` :
                      selectedTTS === 'chatterbox' ? 'ResembleAI/Chatterbox-Turbo' :
                      'Microsoft VibeVoice-Realtime-0.5B'
                    }</p>
                    <p className="text-[#8b949e] text-xs mt-2">
                      {selectedLLM === 'therapist' && 'Compassionate AI therapist with emotional support'}
                      {selectedLLM === 'groq' && 'Ultra-fast Groq inference'}
                      {selectedTTS === 'kokoro' && ' • Fast open-source TTS with voice selection'}
                      {selectedTTS === 'chatterbox' && ' • High-quality TTS with voice cloning support'}
                      {selectedTTS === 'vibevoice' && ' • Realtime streaming TTS (~300ms first audible)'}
                    </p>
                  </div>
                )}
              </div>

              {/* Error Messages */}
              {errorMessage && (
                <div className="bg-[#f8514926] border border-[#f85149] rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-[#f85149] flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-[#f8d7da]">{errorMessage}</p>
                  </div>
                </div>
              )}

              {modelWarmingUp && connectionStatus === 'connected' && (
                <div className="bg-[#d2992226] border border-[#d29922] rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <Loader2 className="w-5 h-5 text-[#d29922] flex-shrink-0 mt-0.5 animate-spin" />
                    <p className="text-sm text-[#f8d7da]">
                      Model is warming up... This typically takes 50-60 seconds.
                    </p>
                  </div>
                </div>
              )}

              {/* Instructions */}
              <div className="bg-[#f8514926] border border-[#f85149] rounded-lg p-4">
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

function MetricCard({ label, value, icon, highlight }: { 
  label: string; 
  value: string; 
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-lg p-3 border ${
      highlight 
        ? 'border-[#3fb950] bg-[#3fb950]/10' 
        : 'border-[#30363d] bg-[#21262d]'
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <span className={highlight ? 'text-[#3fb950]' : 'text-[#8b949e]'}>
          {icon}
        </span>
        <span className="text-xs text-[#8b949e] uppercase">{label}</span>
      </div>
      <div className={`text-lg font-bold ${highlight ? 'text-[#3fb950]' : 'text-[#c9d1d9]'}`}>
        {value}
      </div>
    </div>
  );
}
