/**
 * Speech Recognition and Synthesis Service
 * 
 * Provides a clean interface for Web Speech API with:
 * - Speech-to-Text (Speech Recognition)
 * - Text-to-Speech (Speech Synthesis)
 * - Error handling and browser compatibility checks
 * - Event-driven architecture
 */

// ============================================================
// TYPE DEFINITIONS
// ============================================================

export interface SpeechRecognitionConfig {
  continuous?: boolean;
  interimResults?: boolean;
  lang?: string;
  maxAlternatives?: number;
  silenceTimeout?: number; // Auto-stop after X ms of silence
  autoSubmit?: boolean; // Auto-submit when silence detected
}

export interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

export interface SpeechSynthesisConfig {
  lang?: string;
  pitch?: number;
  rate?: number;
  volume?: number;
  voice?: SpeechSynthesisVoice;
}

export interface SpeechRecognitionCallbacks {
  onStart?: () => void;
  onEnd?: () => void;
  onResult?: (result: SpeechRecognitionResult) => void;
  onError?: (error: SpeechRecognitionError) => void;
  onNoMatch?: () => void;
  onSilenceDetected?: (transcript: string) => void; // Called when silence detected with final transcript
}

export interface SpeechRecognitionError {
  error: string;
  message: string;
}

// ============================================================
// BROWSER COMPATIBILITY
// ============================================================

export function isSpeechRecognitionSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)
  );
}

export function isSpeechSynthesisSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    window.speechSynthesis
  );
}

// ============================================================
// SPEECH RECOGNITION SERVICE
// ============================================================

class SpeechRecognitionService {
  private recognition: any = null;
  private isListening = false;
  private callbacks: SpeechRecognitionCallbacks = {};
  private finalTranscript = '';
  private interimTranscript = '';
  private silenceTimer: NodeJS.Timeout | null = null;
  private config: SpeechRecognitionConfig = {};
  private lastSpeechTime = 0;

  constructor() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.setupEventHandlers();
      }
    }
  }

  /**
   * Initialize speech recognition with configuration
   */
  initialize(config: SpeechRecognitionConfig = {}): void {
    if (!this.recognition) {
      throw new Error('Speech recognition not supported in this browser');
    }

    // Store config
    this.config = {
      continuous: config.continuous ?? true, // Changed to true for silence detection
      interimResults: config.interimResults ?? true,
      lang: config.lang ?? 'en-US',
      maxAlternatives: config.maxAlternatives ?? 1,
      silenceTimeout: config.silenceTimeout ?? 2000, // 2 seconds default
      autoSubmit: config.autoSubmit ?? false,
    };

    // Configure recognition
    this.recognition.continuous = this.config.continuous;
    this.recognition.interimResults = this.config.interimResults;
    this.recognition.lang = this.config.lang;
    this.recognition.maxAlternatives = this.config.maxAlternatives;
  }

  /**
   * Start silence detection timer
   */
  private startSilenceDetection(): void {
    if (!this.config.autoSubmit) return;
    
    this.clearSilenceTimer();
    
    const timeout = this.config.silenceTimeout ?? 2000;
    
    this.silenceTimer = setTimeout(() => {
      const silenceDuration = Date.now() - this.lastSpeechTime;
      const hasMinimumContent = this.finalTranscript.trim().split(' ').length >= 3; // At least 3 words
      
      // Only auto-submit if:
      // 1. Silence duration exceeds threshold
      // 2. We have meaningful content (at least 3 words)
      // 3. Still listening (not manually stopped)
      if (silenceDuration >= timeout && hasMinimumContent && this.isListening) {
        console.log('🔇 Silence detected - auto-submitting answer');
        
        // Call silence callback with final transcript
        this.callbacks.onSilenceDetected?.(this.finalTranscript.trim());
        
        // Stop listening
        this.stop();
      } else if (this.isListening) {
        // If still listening but conditions not met, restart timer
        this.startSilenceDetection();
      }
    }, timeout);
  }

  /**
   * Clear silence detection timer
   */
  private clearSilenceTimer(): void {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }

  /**
   * Setup event handlers for speech recognition
   */
  private setupEventHandlers(): void {
    if (!this.recognition) return;

    this.recognition.onstart = () => {
      this.isListening = true;
      this.finalTranscript = '';
      this.interimTranscript = '';
      this.lastSpeechTime = Date.now();
      console.log('🎤 Speech recognition started');
      this.callbacks.onStart?.();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.clearSilenceTimer();
      console.log('🎤 Speech recognition ended');
      this.callbacks.onEnd?.();
    };

    this.recognition.onresult = (event: any) => {
      this.interimTranscript = '';
      this.lastSpeechTime = Date.now();
      
      // Clear existing silence timer
      this.clearSilenceTimer();
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        
        if (result.isFinal) {
          this.finalTranscript += transcript + ' ';
          
          // Emit final result
          this.callbacks.onResult?.({
            transcript: this.finalTranscript.trim(),
            confidence: result[0].confidence,
            isFinal: true,
          });
          
          // Start silence detection timer after final result
          this.startSilenceDetection();
        } else {
          this.interimTranscript += transcript;
          
          // Emit interim result
          this.callbacks.onResult?.({
            transcript: this.interimTranscript,
            confidence: result[0].confidence,
            isFinal: false,
          });
        }
      }
    };

    this.recognition.onerror = (event: any) => {
      // Don't auto-restart - let the user control it
      // Auto-restart was causing interruptions mid-speech
      
      const errorMessages: Record<string, string> = {
        'no-speech': 'No speech detected. Please try speaking again.',
        'audio-capture': 'Microphone not accessible. Please check permissions.',
        'not-allowed': 'Microphone permission denied.',
        'network': 'Network error. Please check your connection.',
        'aborted': 'Speech recognition stopped.',
      };

      // Only emit error for critical issues, not transient ones
      const criticalErrors = ['audio-capture', 'not-allowed', 'aborted'];
      const transientErrors = ['no-speech', 'network'];
      
      if (criticalErrors.includes(event.error)) {
        console.error('🎤 Speech recognition error:', event.error);
        this.callbacks.onError?.({
          error: event.error,
          message: errorMessages[event.error] || 'Speech recognition failed.',
        });
        this.isListening = false;
      } else if (transientErrors.includes(event.error)) {
        // For transient errors (no-speech, network), just log as warning and continue
        console.warn(`⚠️ Transient speech error: ${event.error} - continuing...`);
        // Don't stop listening, don't emit error callback
      } else {
        // Unknown error - log and emit
        console.error('🎤 Speech recognition error:', event.error);
        this.callbacks.onError?.({
          error: event.error,
          message: errorMessages[event.error] || 'Speech recognition failed.',
        });
        this.isListening = false;
      }
    };

    this.recognition.onnomatch = () => {
      console.warn('🎤 No speech match found');
      this.callbacks.onNoMatch?.();
    };
  }

  /**
   * Start listening for speech
   */
  start(callbacks: SpeechRecognitionCallbacks = {}): void {
    if (!this.recognition) {
      throw new Error('Speech recognition not initialized');
    }

    if (this.isListening) {
      console.warn('Speech recognition already active');
      return;
    }

    this.callbacks = callbacks;
    this.finalTranscript = '';
    this.interimTranscript = '';

    try {
      this.recognition.start();
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      this.callbacks.onError?.({
        error: 'start-failed',
        message: 'Failed to start speech recognition. Please try again.',
      });
    }
  }

  /**
   * Stop listening for speech
   */
  stop(): void {
    if (!this.recognition) return;

    this.clearSilenceTimer();
    
    if (this.isListening) {
      this.recognition.stop();
    }
  }

  /**
   * Abort speech recognition immediately
   */
  abort(): void {
    if (!this.recognition) return;

    if (this.isListening) {
      this.recognition.abort();
    }
  }

  /**
   * Check if currently listening
   */
  getIsListening(): boolean {
    return this.isListening;
  }

  /**
   * Get current transcript
   */
  getTranscript(): string {
    return this.finalTranscript.trim();
  }

  /**
   * Get interim transcript
   */
  getInterimTranscript(): string {
    return this.interimTranscript;
  }

  /**
   * Reset transcript
   */
  reset(): void {
    this.finalTranscript = '';
    this.interimTranscript = '';
  }
}

// ============================================================
// SPEECH SYNTHESIS SERVICE
// ============================================================

class SpeechSynthesisService {
  private synth: SpeechSynthesis | null = null;
  private voices: SpeechSynthesisVoice[] = [];
  private isSpeaking = false;
  private currentUtterance: SpeechSynthesisUtterance | null = null;

  constructor() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      this.synth = window.speechSynthesis;
      this.loadVoices();
      
      // Load voices when they change (some browsers load them asynchronously)
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  /**
   * Load available voices
   */
  private loadVoices(): void {
    if (!this.synth) return;
    this.voices = this.synth.getVoices();
    console.log(`🔊 Loaded ${this.voices.length} voices`);
  }

  /**
   * Get available voices
   */
  getVoices(): SpeechSynthesisVoice[] {
    return this.voices;
  }

  /**
   * Get voices filtered by language
   */
  getVoicesByLang(lang: string): SpeechSynthesisVoice[] {
    return this.voices.filter(voice => voice.lang.startsWith(lang));
  }

  /**
   * Get default voice for language
   */
  getDefaultVoice(lang: string = 'en-US'): SpeechSynthesisVoice | undefined {
    // Try to find default voice for language
    const langVoices = this.getVoicesByLang(lang);
    
    // Prefer Google voices for quality
    const googleVoice = langVoices.find(v => v.name.includes('Google'));
    if (googleVoice) return googleVoice;
    
    // Prefer default voice
    const defaultVoice = langVoices.find(v => v.default);
    if (defaultVoice) return defaultVoice;
    
    // Return first available voice
    return langVoices[0];
  }

  /**
   * Speak text with configuration
   */
  speak(
    text: string,
    config: SpeechSynthesisConfig = {},
    callbacks?: {
      onStart?: () => void;
      onEnd?: () => void;
      onError?: (error: any) => void;
      onPause?: () => void;
      onResume?: () => void;
    }
  ): void {
    if (!this.synth) {
      throw new Error('Speech synthesis not supported in this browser');
    }

    // Cancel any ongoing speech
    this.cancel();

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure utterance
    utterance.lang = config.lang ?? 'en-US';
    utterance.pitch = config.pitch ?? 1.0;
    utterance.rate = config.rate ?? 1.0;
    utterance.volume = config.volume ?? 1.0;
    
    // Set voice
    if (config.voice) {
      utterance.voice = config.voice;
    } else {
      const defaultVoice = this.getDefaultVoice(utterance.lang);
      if (defaultVoice) {
        utterance.voice = defaultVoice;
      }
    }

    // Setup event handlers
    utterance.onstart = () => {
      this.isSpeaking = true;
      console.log('🔊 Speech synthesis started');
      callbacks?.onStart?.();
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.currentUtterance = null;
      console.log('🔊 Speech synthesis ended');
      callbacks?.onEnd?.();
    };

    utterance.onerror = (event) => {
      this.isSpeaking = false;
      this.currentUtterance = null;
      console.error('🔊 Speech synthesis error:', event);
      callbacks?.onError?.(event);
    };

    utterance.onpause = () => {
      console.log('🔊 Speech synthesis paused');
      callbacks?.onPause?.();
    };

    utterance.onresume = () => {
      console.log('🔊 Speech synthesis resumed');
      callbacks?.onResume?.();
    };

    // Store current utterance
    this.currentUtterance = utterance;

    // Speak
    this.synth.speak(utterance);
  }

  /**
   * Pause speech synthesis
   */
  pause(): void {
    if (!this.synth) return;
    if (this.isSpeaking) {
      this.synth.pause();
    }
  }

  /**
   * Resume speech synthesis
   */
  resume(): void {
    if (!this.synth) return;
    if (this.synth.paused) {
      this.synth.resume();
    }
  }

  /**
   * Cancel speech synthesis
   */
  cancel(): void {
    if (!this.synth) return;
    this.synth.cancel();
    this.isSpeaking = false;
    this.currentUtterance = null;
  }

  /**
   * Check if currently speaking
   */
  getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * Check if paused
   */
  getIsPaused(): boolean {
    return this.synth?.paused ?? false;
  }
}

// ============================================================
// SINGLETON INSTANCES
// ============================================================

export const speechRecognition = new SpeechRecognitionService();
export const speechSynthesis = new SpeechSynthesisService();

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

/**
 * Request microphone permission
 */
export async function requestMicrophonePermission(): Promise<boolean> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch (error) {
    console.error('Microphone permission denied:', error);
    return false;
  }
}

/**
 * Check microphone permission status
 */
export async function checkMicrophonePermission(): Promise<PermissionState | null> {
  try {
    if (!navigator.permissions) return null;
    const result = await navigator.permissions.query({ name: 'microphone' as PermissionName });
    return result.state;
  } catch (error) {
    console.error('Failed to check microphone permission:', error);
    return null;
  }
}

/**
 * Get browser speech capabilities
 */
export function getSpeechCapabilities() {
  return {
    recognition: isSpeechRecognitionSupported(),
    synthesis: isSpeechSynthesisSupported(),
    mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
  };
}
