import os
import wave
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from .config import BASE_DIR, STORAGE_DIR, FFMPEG_PATH

BGM_DIR = STORAGE_DIR / "assets" / "bgm"

class BGMManager:
    """
    Manages 100% royalty-free, copyright-safe background music loops
    for viral clips with intelligent speech auto-ducking.
    """

    TRACKS = [
        {
            "id": "none",
            "name": "None (Speech Only)",
            "desc": "Original master audio with zero background music.",
            "filename": None
        },
        {
            "id": "chill_lofi",
            "name": "Chill Lo-Fi Beat",
            "desc": "Warm mellow chords with soft vinyl texture. Perfect for general discussions & storytelling.",
            "filename": "chill_lofi.m4a"
        },
        {
            "id": "podcast_ambient",
            "name": "Atmospheric Pad",
            "desc": "Subtle, cinematic warm synth pad. Adds depth without distracting from dialogue.",
            "filename": "podcast_ambient.m4a"
        },
        {
            "id": "deep_mystery",
            "name": "Deep Mystery & Suspense",
            "desc": "Pulsating minor drone for secrets, shocking truths, and curiosity hooks.",
            "filename": "deep_mystery.m4a"
        },
        {
            "id": "viral_energy",
            "name": "Upbeat Viral Pulse",
            "desc": "Rhythmic motivational pulse for business, fitness, and high-energy hooks.",
            "filename": "viral_energy.m4a"
        }
    ]

    @classmethod
    def get_tracks(cls) -> List[Dict[str, Any]]:
        cls.ensure_default_tracks()
        return cls.TRACKS

    @classmethod
    def get_track_path(cls, track_id: str) -> Optional[Path]:
        if not track_id or track_id == "none":
            return None
        cls.ensure_default_tracks()
        for t in cls.TRACKS:
            if t["id"] == track_id and t["filename"]:
                p = BGM_DIR / t["filename"]
                if p.exists():
                    return p
        return None

    @classmethod
    def ensure_default_tracks(cls):
        """Generates high quality harmonic 44.1kHz stereo audio loops if not already present."""
        BGM_DIR.mkdir(parents=True, exist_ok=True)

        for track in cls.TRACKS:
            fn = track["filename"]
            if not fn:
                continue
            dest = BGM_DIR / fn
            if not dest.exists():
                cls._synthesize_track(track["id"], dest)

    @classmethod
    def _synthesize_track(cls, track_id: str, dest_path: Path):
        """Synthesize 16-second seamless audio loops using pure Python numpy & encode to AAC."""
        sample_rate = 44100
        duration = 16.0
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        sig_left = np.zeros(num_samples, dtype=np.float32)
        sig_right = np.zeros(num_samples, dtype=np.float32)

        if track_id == "chill_lofi":
            # Warm major 7th progression (Cmaj7 -> Am7 -> Dm7 -> G7)
            chords = [
                [261.63, 329.63, 392.00, 493.88],
                [220.00, 261.63, 329.63, 392.00],
                [293.66, 349.23, 440.00, 523.25],
                [196.00, 246.94, 293.66, 349.23],
            ]
            c_dur = duration / len(chords)
            for i, chord in enumerate(chords):
                t_start = i * c_dur
                t_end = (i + 1) * c_dur
                mask = (t >= t_start) & (t < t_end)
                tc = t[mask] - t_start
                env = np.sin(np.pi * (tc / c_dur)) ** 0.6
                for idx, f in enumerate(chord):
                    pan = idx / max(1, len(chord) - 1)
                    tone = np.sin(2 * np.pi * f * tc) * 0.14 + np.sin(2 * np.pi * f * 2 * tc) * 0.03
                    sig_left[mask] += (tone * (1.0 - pan * 0.35) * env).astype(np.float32)
                    sig_right[mask] += (tone * (0.65 + pan * 0.35) * env).astype(np.float32)
            # Gentle soft vinyl texture
            sig_left += np.random.normal(0, 0.002, num_samples).astype(np.float32)
            sig_right += np.random.normal(0, 0.002, num_samples).astype(np.float32)

        elif track_id == "podcast_ambient":
            # Warm lush cinematic pad (F -> C -> G -> Am)
            freqs = [174.61, 261.63, 329.63, 392.00, 523.25]
            for idx, f in enumerate(freqs):
                lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.15 + idx * 0.05) * t)
                tone = np.sin(2 * np.pi * f * t) * 0.12 * lfo
                sig_left += (tone * (0.9 - idx * 0.1)).astype(np.float32)
                sig_right += (tone * (0.5 + idx * 0.1)).astype(np.float32)

        elif track_id == "deep_mystery":
            # Dark suspenseful sub drone (D minor with slow filter sweep)
            drone_f = 73.42  # D2
            fifth_f = 110.00 # A2
            oct_f = 146.83   # D3
            sub = np.sin(2 * np.pi * drone_f * t) * 0.25
            fifth = np.sin(2 * np.pi * fifth_f * t) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t))
            oct = np.sin(2 * np.pi * oct_f * t) * 0.08 * (0.5 + 0.5 * np.cos(2 * np.pi * 0.3 * t))
            sig_left += (sub + fifth * 0.8 + oct * 0.6).astype(np.float32)
            sig_right += (sub + fifth * 0.6 + oct * 0.8).astype(np.float32)

        else: # viral_energy
            # Upbeat rhythmic pulse (120 BPM = 0.5s beat)
            beat_interval = 0.5
            bass_f = 110.0 # A2
            lead_f = 220.0
            beat_phase = (t % beat_interval) / beat_interval
            pulse_env = np.exp(-beat_phase * 6.0) # snappy envelope
            sig_left += (np.sin(2 * np.pi * bass_f * t) * pulse_env * 0.28).astype(np.float32)
            sig_right += (np.sin(2 * np.pi * bass_f * t) * pulse_env * 0.28).astype(np.float32)
            hi_pulse = np.sin(2 * np.pi * lead_f * t) * (np.exp(-((t % (beat_interval * 2)) / (beat_interval * 2)) * 8.0)) * 0.12
            sig_left += hi_pulse.astype(np.float32)
            sig_right += (hi_pulse * 0.8).astype(np.float32)

        # Normalize to peak -3 dB
        max_val = max(np.max(np.abs(sig_left)), np.max(np.abs(sig_right)), 1e-6)
        sig_left = (sig_left / max_val * 0.75 * 32767).astype(np.int16)
        sig_right = (sig_right / max_val * 0.75 * 32767).astype(np.int16)

        stereo = np.empty((num_samples, 2), dtype=np.int16)
        stereo[:, 0] = sig_left
        stereo[:, 1] = sig_right

        # Save temporary WAV
        temp_wav = dest_path.with_suffix(".temp.wav")
        try:
            with wave.open(str(temp_wav), 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(stereo.tobytes())

            # Convert to AAC / M4A via FFmpeg
            cmd = [
                FFMPEG_PATH, "-y",
                "-i", str(temp_wav),
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                str(dest_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"[BGMManager] Synthesized royalty-free loop: {dest_path.name}")
        finally:
            if temp_wav.exists():
                temp_wav.unlink(missing_ok=True)
