/**
 * Web Audio API Industrial SCADA Alarm Synthesizer
 * Zero-dependency client-side audio generator emulating industrial control room buzzers.
 */

class SCADAAudioAlarm {
  constructor() {
    this.audioCtx = null;
    this.enabled = localStorage.getItem('iot_audio_enabled') === 'true'; // Default muted until operator enables
  }

  initContext() {
    if (!this.audioCtx && (window.AudioContext || window.webkitAudioContext)) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioCtxClass();
    }
  }

  isEnabled() {
    return this.enabled;
  }

  toggleSound() {
    this.enabled = !this.enabled;
    localStorage.setItem('iot_audio_enabled', String(this.enabled));
    if (this.enabled) {
      this.initContext();
      this.playBeep(660, 0.1, 0.15); // Confirmation chirp
    }
    return this.enabled;
  }

  playBeep(frequency = 520, duration = 0.18, volume = 0.25) {
    try {
      this.initContext();
      if (!this.audioCtx || this.audioCtx.state === 'suspended') {
        this.audioCtx?.resume();
      }

      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.type = 'sawtooth'; // Industrial buzzer timbre
      osc.frequency.setValueAtTime(frequency, this.audioCtx.currentTime);

      // Volume envelope (attack / decay)
      gain.gain.setValueAtTime(0.01, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(volume, this.audioCtx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {
      console.warn('[AudioAlarm] Play error:', e);
    }
  }

  triggerCriticalAlarm() {
    if (!this.enabled) return;

    // Dual-tone industrial emergency pulse: High-Low-High
    this.playBeep(880, 0.14, 0.3);
    setTimeout(() => this.playBeep(587, 0.18, 0.35), 180);
    setTimeout(() => this.playBeep(880, 0.2, 0.3), 420);
  }
}

export const scadaAudio = new SCADAAudioAlarm();
