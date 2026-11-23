import os
import subprocess
import wave
import ctypes
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Global PyAV 19.x metadata_errors patch
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

from .config import FFMPEG_PATH, TEMP_DIR

class AudioTranscriber:
    """
    High-performance audio extractor and speech-to-text transcriber
    powered by faster-whisper with word-level timestamps.
    Uses direct FFmpeg PCM extraction + NumPy decoding for maximum stability.
    Features bulletproof hardware detection and automatic CPU fallback if CUDA libraries are missing.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default"
    ):
        """
        model_size: 'tiny', 'base', 'small', 'medium', 'large-v3-turbo'
        device: 'cuda', 'cpu', or 'auto'
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    @staticmethod
    def _is_cuda_ready() -> bool:
        """
        Checks whether NVIDIA CUDA drivers AND required runtime DLLs (cublas64_12.dll / 11.dll)
        are genuinely present and loadable on the system.
        """
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() == 0:
                return False

            # Test loading cublas dynamic library via ctypes
            for dll in ["cublas64_12.dll", "cublas64_11.dll"]:
                try:
                    ctypes.cdll.LoadLibrary(dll)
                    return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

    def _get_model(self):
        """Lazy load the Whisper model with hardware auto-detection."""
        if self._model is None:
            from faster_whisper import WhisperModel

            target_device = self.device
            if target_device == "auto":
                target_device = "cuda" if self._is_cuda_ready() else "cpu"

            comp_type = self.compute_type
            if comp_type == "default":
                comp_type = "float16" if target_device == "cuda" else "int8"

            print(f"[Transcriber] Loading faster-whisper '{self.model_size}' on {target_device} ({comp_type})...")
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=target_device,
                    compute_type=comp_type,
                    download_root=str(TEMP_DIR / "whisper_cache")
                )
            except Exception as e:
                print(f"[Transcriber Warning] Initialization on {target_device} failed ({e}). Falling back to CPU int8...")
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(TEMP_DIR / "whisper_cache")
                )
        return self._model

    def extract_audio(self, video_path: str, output_audio_path: Optional[str] = None) -> Path:
        """Extract 16kHz mono 16-bit PCM WAV audio from video using FFmpeg."""
        video_p = Path(video_path)
        if output_audio_path is None:
            out_p = TEMP_DIR / f"{video_p.stem}_audio.wav"
        else:
            out_p = Path(output_audio_path)

        out_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-i", str(video_p),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(out_p)
        ]

        print(f"[Transcriber] Extracting audio with FFmpeg: {' '.join(cmd[:6])}...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

        return out_p

    def load_audio_numpy(self, wav_path: Path) -> np.ndarray:
        """
        Loads 16kHz mono WAV file directly into a float32 NumPy array.
        Bypasses PyAV to prevent 'metadata_errors' and decoding bugs.
        """
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            return audio_data

    def transcribe(self, video_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes the video audio and returns structured segments
        with full word-level timestamps.
        Includes automatic CPU recovery if GPU DLLs are missing during runtime.
        """
        audio_path = self.extract_audio(video_path)
        model = self._get_model()

        # Load audio directly into NumPy float32
        try:
            audio_input = self.load_audio_numpy(audio_path)
        except Exception as e:
            print(f"[Transcriber] NumPy audio load failed ({e}), using file path fallback.")
            audio_input = str(audio_path)

        all_segments = []
        all_words = []

        try:
            segments_gen, info = model.transcribe(
                audio_input,
                language=language,
                beam_size=1,
                condition_on_previous_text=False,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            for seg in segments_gen:
                words_data = []
                if seg.words:
                    for w in seg.words:
                        word_item = {
                            "word": w.word,
                            "start": round(w.start, 3),
                            "end": round(w.end, 3),
                            "probability": round(w.probability, 3)
                        }
                        words_data.append(word_item)
                        all_words.append(word_item)

                all_segments.append({
                    "id": seg.id,
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text.strip(),
                    "words": words_data
                })

        except RuntimeError as run_err:
            # If cublas or CUDA runtime DLL error occurs during generator evaluation
            err_msg = str(run_err).lower()
            if "cublas" in err_msg or "cudnn" in err_msg or "cannot be loaded" in err_msg:
                print(f"[Transcriber Warning] CUDA runtime exception ({run_err}). Automatically recovering on CPU (int8)...")
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(TEMP_DIR / "whisper_cache")
                )
                segments_gen, info = self._model.transcribe(
                    audio_input,
                    language=language,
                    beam_size=1,
                    condition_on_previous_text=False,
                    word_timestamps=True,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=400)
                )
                all_segments = []
                all_words = []
                for seg in segments_gen:
                    words_data = []
                    if seg.words:
                        for w in seg.words:
                            word_item = {
                                "word": w.word,
                                "start": round(w.start, 3),
                                "end": round(w.end, 3),
                                "probability": round(w.probability, 3)
                            }
                            words_data.append(word_item)
                            all_words.append(word_item)
                    all_segments.append({
                        "id": seg.id,
                        "start": round(seg.start, 3),
                        "end": round(seg.end, 3),
                        "text": seg.text.strip(),
                        "words": words_data
                    })
            else:
                raise run_err

        # Cleanup temporary audio
        try:
            if audio_path.exists():
                audio_path.unlink()
        except Exception:
            pass

        return {
            "language": info.language if 'info' in locals() else "en",
            "duration": round(info.duration, 2) if 'info' in locals() else 0.0,
            "segments": all_segments,
            "words": all_words
        }

    def transcribe_segment(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fast transcription of an isolated segment (used for fine-nudge trim).
        Extracts only that audio chunk and transcribes it in <1 second.
        """
        out_wav = TEMP_DIR / f"seg_{int(start_sec)}_{int(start_sec + duration)}.wav"
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", f"{start_sec:.3f}",
            "-t", f"{duration:.3f}",
            "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            str(out_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        model = self._get_model()
        try:
            audio_input = self.load_audio_numpy(out_wav)
        except Exception:
            audio_input = str(out_wav)

        words_data = []
        try:
            segments_gen, _ = model.transcribe(
                audio_input,
                language=language,
                word_timestamps=True,
                vad_filter=True
            )
            for seg in segments_gen:
                if seg.words:
                    for w in seg.words:
                        words_data.append({
                            "word": w.word,
                            "start": round(start_sec + w.start, 3),
                            "end": round(start_sec + w.end, 3),
                            "probability": round(w.probability, 3)
                        })
        except Exception as e:
            print(f"[Transcriber Segment Error] {e}")

        try:
            out_wav.unlink(missing_ok=True)
        except Exception:
            pass

        return words_data

