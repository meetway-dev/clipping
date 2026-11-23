import os
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np

from .config import BASE_DIR

class SmartFaceTracker:
    """
    Intelligent 16:9 to 9:16 Auto-Reframe Engine with Active Speaker Tracking.
    Powered by OpenCV YuNet Deep Neural Network Face Detector.
    Features High-Performance Trajectory Caching and Selective Subframe Decoding.
    """

    _trajectory_cache: Dict[Tuple, List[Dict[str, Any]]] = {}
    _shared_detector: Optional[Any] = None
    _detector_initialized: bool = False

    def __init__(self, smooth_factor: float = 0.10, model_path: Optional[str] = None):
        self.smooth_factor = smooth_factor
        
        # Locate YuNet model
        if model_path is None:
            default_model = BASE_DIR / "storage" / "models" / "face_detection_yunet.onnx"
            self.model_path = str(default_model) if default_model.exists() else None
        else:
            self.model_path = model_path

        self._detector = None
        self._input_size = (320, 180)
        self._init_detector()

    def _init_detector(self):
        """Initialize YuNet DNN detector as a shared high-performance singleton."""
        if SmartFaceTracker._detector_initialized and SmartFaceTracker._shared_detector is not None:
            self._detector = SmartFaceTracker._shared_detector
            return

        if self.model_path and os.path.exists(self.model_path) and hasattr(cv2, "FaceDetectorYN_create"):
            try:
                SmartFaceTracker._shared_detector = cv2.FaceDetectorYN_create(
                    self.model_path,
                    "",
                    self._input_size,
                    score_threshold=0.55,
                    nms_threshold=0.3,
                    top_k=6
                )
                SmartFaceTracker._detector_initialized = True
                self._detector = SmartFaceTracker._shared_detector
            except Exception as e:
                print(f"[FaceTracker] Warning: Could not initialize YuNet: {e}")
                SmartFaceTracker._shared_detector = None
                SmartFaceTracker._detector_initialized = True
                self._detector = None
        else:
            self._detector = None

    def detect_faces(self, frame_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects all faces in a frame using YuNet and projects to native coordinates.
        Returns list of face dicts: {x, y, w, h, cx, cy, score}.
        """
        if self._detector is None:
            return []

        h, w = frame_bgr.shape[:2]
        small_frame = cv2.resize(frame_bgr, self._input_size)
        retval, faces = self._detector.detect(small_frame)

        if retval is None or faces is None or len(faces) == 0:
            return []

        scale_x = w / float(self._input_size[0])
        scale_y = h / float(self._input_size[1])

        parsed = []
        for f in faces:
            fx = int(f[0] * scale_x)
            fy = int(f[1] * scale_y)
            fw = int(f[2] * scale_x)
            fh = int(f[3] * scale_y)
            score = float(f[14])
            parsed.append({
                "x": fx, "y": fy, "w": fw, "h": fh,
                "cx": fx + (fw / 2.0),
                "cy": fy + (fh / 2.0),
                "score": score
            })
        return parsed

    def detect_face_center(self, frame_bgr: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """Backward-compatible helper returning prominent face center (center_x, center_y, score)."""
        faces = self.detect_faces(frame_bgr)
        if not faces:
            return None
        best = max(faces, key=lambda f: f["w"] * f["h"])
        return (best["cx"], best["cy"], best["score"])

    def compute_mouth_activity(self, frames: List[np.ndarray], face: Dict[str, Any]) -> float:
        """
        Measures temporal pixel variance in the lower face / mouth area across consecutive frames.
        The speaking person exhibits 2x to 8x higher variance due to opening/closing of lips.
        """
        if len(frames) < 2:
            return 0.0

        fx, fy, fw, fh = face["x"], face["y"], face["w"], face["h"]
        h_frame, w_frame = frames[0].shape[:2]

        my1 = max(0, fy + int(fh * 0.62))
        my2 = min(h_frame, fy + int(fh * 0.98))
        mx1 = max(0, fx + int(fw * 0.20))
        mx2 = min(w_frame, fx + int(fw * 0.80))

        if my2 <= my1 or mx2 <= mx1:
            return 0.0

        diffs = []
        for k in range(len(frames) - 1):
            m1 = frames[k][my1:my2, mx1:mx2]
            m2 = frames[k + 1][my1:my2, mx1:mx2]
            if m1.shape == m2.shape and m1.size > 0:
                g1 = cv2.cvtColor(m1, cv2.COLOR_BGR2GRAY)
                g2 = cv2.cvtColor(m2, cv2.COLOR_BGR2GRAY)
                diff = float(np.mean(np.abs(g1.astype(float) - g2.astype(float))))
                diffs.append(diff)

        return float(np.mean(diffs)) if diffs else 0.0

    def compute_crop_trajectory(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        sample_fps: float = 1.0,
        layout_mode: str = "speaker_focus",
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        target_w: int = 1080,
        target_h: int = 1920
    ) -> List[Dict[str, Any]]:
        """
        Analyzes video frames from start_sec for duration.
        Tracks single or multi-speaker scenes, resolves active speaker by mouth dynamics,
        and computes professional vertical crop boxes constrained to custom top and bottom padding.
        """
        # Check memory cache first
        cache_key = (
            str(video_path),
            round(float(start_sec), 2),
            round(float(duration), 2),
            str(layout_mode),
            round(float(sample_fps), 1),
            round(float(top_padding), 1),
            round(float(bottom_padding), 1)
        )
        if cache_key in self._trajectory_cache:
            return [dict(s) for s in self._trajectory_cache[cache_key]]

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        # Safe area padding math
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad

        top_pad_px = int(round(target_h * top_pct))
        bottom_pad_px = int(round(target_h * bottom_pct))
        available_h = max(100, target_h - top_pad_px - bottom_pad_px)

        center_ar = target_w / float(available_h)
        if (orig_w / float(orig_h)) >= center_ar:
            default_crop_h = orig_h if orig_h % 2 == 0 else orig_h - 1
            default_crop_w = int(round(default_crop_h * center_ar))
            if default_crop_w % 2 != 0: default_crop_w -= 1
            if default_crop_w > orig_w: default_crop_w = orig_w if orig_w % 2 == 0 else orig_w - 1
        else:
            default_crop_w = orig_w if orig_w % 2 == 0 else orig_w - 1
            default_crop_h = int(round(default_crop_w / center_ar))
            if default_crop_h % 2 != 0: default_crop_h -= 1
            if default_crop_h > orig_h: default_crop_h = orig_h if orig_h % 2 == 0 else orig_h - 1

        default_center_x = orig_w / 2.0
        default_center_y = orig_h / 2.0

        start_frame = int(start_sec * native_fps)
        total_frames = int(duration * native_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        step_frames = max(1, int(round(native_fps / sample_fps)))
        samples = []

        curr_frame_idx = 0
        last_speaker = None
        candidate_speaker = None
        candidate_count = 0

        while curr_frame_idx < total_frames:
            ret, frame = cap.read()
            if not ret:
                break

            t = start_sec + (curr_frame_idx / native_fps)
            curr_frame_idx += 1

            # High performance face check on key sample frame first
            faces = self.detect_faces(frame)
            active_face = None

            if len(faces) == 1:
                # 90%+ cases: Single person in shot, no burst subframe reading needed!
                active_face = faces[0]
                candidate_speaker = None
                candidate_count = 0
            elif len(faces) >= 2:
                # Multi-person wide shot (e.g. host & guest): Resolve active speaker via temporal lip motion
                burst = [frame]
                for _ in range(2):
                    r_sub, f_sub = cap.read()
                    if r_sub:
                        burst.append(f_sub)
                        curr_frame_idx += 1

                scored = []
                for face in faces:
                    act = self.compute_mouth_activity(burst, face)
                    scored.append((act, face))
                scored.sort(key=lambda s: s[0], reverse=True)

                top_act, top_face = scored[0]
                sec_act, sec_face = scored[1]

                if last_speaker is None:
                    active_face = top_face
                    candidate_speaker = None
                    candidate_count = 0
                else:
                    # Find face closest to last_speaker
                    current_face = min(faces, key=lambda f: abs(f["cx"] - last_speaker["cx"]))
                    current_act = next((act for act, f in scored if abs(f["cx"] - current_face["cx"]) < 60), 0.0)

                    # Check if another speaker is actively speaking
                    if abs(top_face["cx"] - current_face["cx"]) > 100 and top_act > 2.5 and top_act > 1.6 * max(1.0, current_act):
                        if candidate_speaker and abs(top_face["cx"] - candidate_speaker["cx"]) < 80:
                            candidate_count += 1
                        else:
                            candidate_speaker = top_face
                            candidate_count = 1

                        if candidate_count >= 3:
                            active_face = candidate_speaker
                            candidate_speaker = None
                            candidate_count = 0
                        else:
                            active_face = current_face
                    else:
                        active_face = current_face
                        candidate_speaker = None
                        candidate_count = 0

            if active_face:
                last_speaker = active_face

            # Calculate proportional crop box constrained by active safe area padding
            if last_speaker:
                sf = last_speaker
                if (orig_w / float(orig_h)) >= center_ar:
                    opt_h = orig_h if orig_h % 2 == 0 else orig_h - 1
                    opt_w = int(round(opt_h * center_ar))
                    if opt_w % 2 != 0: opt_w -= 1
                    if opt_w > orig_w: opt_w = orig_w if orig_w % 2 == 0 else orig_w - 1
                else:
                    opt_w = orig_w if orig_w % 2 == 0 else orig_w - 1
                    opt_h = int(round(opt_w / center_ar))
                    if opt_h % 2 != 0: opt_h -= 1
                    if opt_h > orig_h: opt_h = orig_h if orig_h % 2 == 0 else orig_h - 1

                opt_x = int(sf["cx"] - opt_w / 2.0)
                opt_x = max(0, min(orig_w - opt_w, opt_x))
                if opt_x % 2 != 0:
                    opt_x -= 1

                if opt_h < orig_h:
                    if layout_mode == "face_center":
                        opt_y = int(sf["cy"] - 0.38 * opt_h)
                    else:
                        opt_y = int(sf["cy"] - 0.40 * opt_h)
                    opt_y = max(0, min(orig_h - opt_h, opt_y))
                    if opt_y % 2 != 0:
                        opt_y -= 1
                else:
                    opt_y = 0

                samples.append({
                    "time": t,
                    "rel_t": t - start_sec,
                    "cx": sf["cx"],
                    "cy": sf["cy"],
                    "crop_x": opt_x,
                    "crop_y": opt_y,
                    "crop_w": opt_w,
                    "crop_h": opt_h,
                    "orig_w": orig_w,
                    "orig_h": orig_h
                })
            else:
                cx = max(0, min(orig_w - default_crop_w, int(default_center_x - default_crop_w / 2)))
                if cx % 2 != 0:
                    cx -= 1
                samples.append({
                    "time": t,
                    "rel_t": t - start_sec,
                    "cx": default_center_x,
                    "cy": default_center_y,
                    "crop_x": cx,
                    "crop_y": 0,
                    "crop_w": default_crop_w,
                    "crop_h": default_crop_h,
                    "orig_w": orig_w,
                    "orig_h": orig_h
                })

            # Fast-forward to next sample point using lightweight packet grab
            skip_frames = max(0, step_frames - 1)
            for _ in range(skip_frames):
                if curr_frame_idx >= total_frames:
                    break
                cap.grab()
                curr_frame_idx += 1

        cap.release()

        # In face_center mode, apply exponential moving average (EMA) damping
        # to ensure rock-steady dead-center framing without micro-jittering
        if layout_mode == "face_center" and len(samples) > 1:
            alpha = 0.25
            curr_x = float(samples[0]["crop_x"])
            for s in samples:
                curr_x = alpha * float(s["crop_x"]) + (1.0 - alpha) * curr_x
                smoothed_x = int(round(curr_x))
                if smoothed_x % 2 != 0:
                    smoothed_x -= 1
                s["crop_x"] = max(0, min(orig_w - s["crop_w"], smoothed_x))

        # Cache trajectory in memory
        self._trajectory_cache[cache_key] = samples
        return samples

    def compute_face_center_crop(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        sample_fps: float = 1.0,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        target_w: int = 1080,
        target_h: int = 1920
    ) -> List[Dict[str, Any]]:
        """Convenience method for exact face-centering trajectory."""
        return self.compute_crop_trajectory(
            video_path=video_path,
            start_sec=start_sec,
            duration=duration,
            sample_fps=sample_fps,
            layout_mode="face_center",
            top_padding=top_padding,
            bottom_padding=bottom_padding,
            target_w=target_w,
            target_h=target_h
        )

    def get_ffmpeg_crop_filter(
        self,
        trajectory: List[Dict[str, Any]],
        target_w: int = 1080,
        target_h: int = 1920,
        enable_hook_zoom: bool = True,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        canvas_bg: str = "solid_black"
    ) -> str:
        """
        Converts the trajectory into an efficient, production FFmpeg video filter expression.
        Applies:
        - Active speaker framing with dynamic close-up zoom.
        - Smooth 0.25s cosine whip-pan / ease transitions between speaker changes.
        - Subtle 1.05x hook zoom during the first 3 seconds for viral retention.
        - Guaranteed vertical output scaling with Lanczos/bicubic interpolation.
        - Safe Area & Spacing: Automatically fits into available center area (target_h * (1 - top% - bottom%)).
        """
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad
        top_pad_px = int(round(target_h * top_pct))
        bottom_pad_px = int(round(target_h * bottom_pct))
        available_h = max(100, target_h - top_pad_px - bottom_pad_px)
        has_padding = (top_pad_px > 0 or bottom_pad_px > 0)

        if not trajectory:
            if has_padding:
                if canvas_bg in ["heavy_blur", "blur"]:
                    return (
                        f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                        f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                        f"[0:v]crop='min(iw,ih*({target_w}/{available_h}))':'min(ih,iw*({available_h}/{target_w}))':(iw-ow)/2:(ih-oh)/2,"
                        f"scale={target_w}:{available_h}:flags=bicubic[fg];"
                        f"[bg][fg]overlay=0:{top_pad_px}[outv]"
                    )
                return (
                    f"crop='min(iw,ih*({target_w}/{available_h}))':'min(ih,iw*({available_h}/{target_w}))':(iw-ow)/2:(ih-oh)/2,"
                    f"scale={target_w}:{available_h}:flags=bicubic,"
                    f"pad={target_w}:{target_h}:0:{top_pad_px}:color=#0E0C0A"
                )
            return f"crop=ih*(9/16):ih:(iw-ow)/2:0,scale={target_w}:{target_h}:flags=bicubic"

        total_dur = trajectory[-1]["rel_t"] + 1.0

        # Segment trajectory into contiguous shots (based on speaker changes / cuts)
        raw_shots = []
        current_shot = [trajectory[0]]

        for s in trajectory[1:]:
            prev = current_shot[-1]
            dist = math.hypot(s["cx"] - prev["cx"], s["cy"] - prev["cy"])
            # If distance > 180px, it's a potential speaker switch
            if dist > 180:
                raw_shots.append(current_shot)
                current_shot = [s]
            else:
                current_shot.append(s)
        if current_shot:
            raw_shots.append(current_shot)

        # Enforce minimum hold duration (3.0s):
        # Brief 1-2s reactions, nods, or coughs must not cause jittery camera cuts.
        # Merge any shot shorter than 3.0s into the preceding stable shot.
        shots = []
        for shot in raw_shots:
            shot_dur = shot[-1]["rel_t"] - shot[0]["rel_t"] + 0.5
            if not shots:
                shots.append(shot)
            elif shot_dur < 3.0:
                shots[-1].extend(shot)
            else:
                shots.append(shot)

        # If rapid back-and-forth ping-ponging still detected (3+ switches in short duration),
        # center between both speakers to prevent camera whipping
        if len(shots) >= 3:
            total_span = shots[-1][-1]["rel_t"] - shots[0][0]["rel_t"]
            if total_span / len(shots) < 4.0:
                # Rapid banter: use a single steady shot centered between both speakers
                all_cx = [s["cx"] for s in trajectory]
                min_c = min(all_cx)
                max_c = max(all_cx)
                mid_c = (min_c + max_c) / 2.0
                opt_w = trajectory[0]["crop_w"]
                orig_w = trajectory[0]["orig_w"]
                steady_x = int(max(0, min(orig_w - opt_w, mid_c - opt_w / 2.0)))
                if steady_x % 2 != 0: steady_x -= 1
                for s in trajectory:
                    s["crop_x"] = steady_x
                shots = [trajectory]

        # For each shot, compute steady median framing
        shot_params = []
        for shot_idx, shot in enumerate(shots):
            t_start = shot[0]["rel_t"]
            t_end = shot[-1]["rel_t"] + 0.5
            if shot_idx == len(shots) - 1:
                t_end = max(t_end, total_dur)

            med_x = int(round(np.median([s["crop_x"] for s in shot])))
            med_y = int(round(np.median([s["crop_y"] for s in shot])))
            med_w = int(round(np.median([s["crop_w"] for s in shot])))
            med_h = int(round(np.median([s["crop_h"] for s in shot])))

            if med_w % 2 != 0: med_w -= 1
            if med_h % 2 != 0: med_h -= 1
            if med_x % 2 != 0: med_x -= 1
            if med_y % 2 != 0: med_y -= 1

            shot_params.append({
                "t_start": t_start,
                "t_end": t_end,
                "x": med_x,
                "y": med_y,
                "w": med_w,
                "h": med_h
            })

        # Single shot: simple steady crop
        if len(shot_params) == 1:
            sp = shot_params[0]
            w_val = sp["w"]
            h_val = sp["h"]
            x_val = sp["x"]
            y_val = sp["y"]

            if enable_hook_zoom:
                hook_expr = "if(lt(t,3.0),0.96,1.0)"
                w_str = f"({w_val}*{hook_expr})"
                h_str = f"({h_val}*{hook_expr})"
                x_str = f"({x_val}+({w_val}-{w_str})/2)"
                y_str = f"({y_val}+({h_val}-{h_str})/2)"
                crop_cmd = f"crop=w='{w_str}':h='{h_str}':x='{x_str}':y='{y_str}'"
            else:
                crop_cmd = f"crop={w_val}:{h_val}:{x_val}:{y_val}"

            if has_padding:
                if canvas_bg in ["heavy_blur", "blur"]:
                    return (
                        f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                        f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                        f"[0:v]{crop_cmd},scale={target_w}:{available_h}:flags=bicubic[fg];"
                        f"[bg][fg]overlay=0:{top_pad_px}[outv]"
                    )
                return f"{crop_cmd},scale={target_w}:{available_h}:flags=bicubic,pad={target_w}:{target_h}:0:{top_pad_px}:color=#0E0C0A"
            return f"{crop_cmd},scale={target_w}:{target_h}:flags=bicubic"

        # Multi-shot: build piecewise expressions with 0.25s smooth whip-pan / ease transitions
        x_expr = f"{shot_params[-1]['x']}"
        y_expr = f"{shot_params[-1]['y']}"
        w_expr = f"{shot_params[-1]['w']}"
        h_expr = f"{shot_params[-1]['h']}"

        for i in range(len(shot_params) - 2, -1, -1):
            curr = shot_params[i]
            nxt = shot_params[i + 1]
            t_switch = nxt["t_start"]
            trans_dur = 0.25

            ease_term = f"(0.5-0.5*cos(3.14159*(t-{t_switch:.2f})/{trans_dur:.2f}))"
            pan_x = f"({curr['x']}+({nxt['x']}-{curr['x']})*{ease_term})"
            pan_y = f"({curr['y']}+({nxt['y']}-{curr['y']})*{ease_term})"
            pan_w = f"({curr['w']}+({nxt['w']}-{curr['w']})*{ease_term})"
            pan_h = f"({curr['h']}+({nxt['h']}-{curr['h']})*{ease_term})"

            x_expr = f"if(lt(t,{t_switch:.2f}),{curr['x']},if(lt(t,{t_switch + trans_dur:.2f}),{pan_x},{x_expr}))"
            y_expr = f"if(lt(t,{t_switch:.2f}),{curr['y']},if(lt(t,{t_switch + trans_dur:.2f}),{pan_y},{y_expr}))"
            w_expr = f"if(lt(t,{t_switch:.2f}),{curr['w']},if(lt(t,{t_switch + trans_dur:.2f}),{pan_w},{w_expr}))"
            h_expr = f"if(lt(t,{t_switch:.2f}),{curr['h']},if(lt(t,{t_switch + trans_dur:.2f}),{pan_h},{h_expr}))"

        if enable_hook_zoom:
            hook_factor = "if(lt(t,3.0),0.96,1.0)"
            w_expr = f"({w_expr}*{hook_factor})"
            h_expr = f"({h_expr}*{hook_factor})"

        crop_cmd = f"crop=w='{w_expr}':h='{h_expr}':x='{x_expr}':y='{y_expr}'"
        if has_padding:
            if canvas_bg in ["heavy_blur", "blur"]:
                return (
                    f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                    f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                    f"[0:v]{crop_cmd},scale={target_w}:{available_h}:flags=bicubic[fg];"
                    f"[bg][fg]overlay=0:{top_pad_px}[outv]"
                )
            return f"{crop_cmd},scale={target_w}:{available_h}:flags=bicubic,pad={target_w}:{target_h}:0:{top_pad_px}:color=#0E0C0A"
        return f"{crop_cmd},scale={target_w}:{target_h}:flags=bicubic"

    def detect_dual_speakers(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        sample_fps: float = 1.5,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        target_w: int = 1080,
        target_h: int = 1920
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Detects if a scene features two distinct conversation participants (e.g. host & guest).
        Uses spatial clustering along the X-axis to verify that TWO genuinely distinct
        individuals exist (separated by >= 250px).
        
        If only 1 person or cluster is detected, returns None so the pipeline
        cleanly and automatically renders 9:16 Speaker Focus instead of duplicating
        the same person across both split screens!
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        start_frame = int(start_sec * native_fps)
        total_frames = int(duration * native_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        step_frames = max(1, int(native_fps / sample_fps))
        curr_frame_idx = 0

        detected_faces = []
        while curr_frame_idx < total_frames and len(detected_faces) < 60:
            ret, frame = cap.read()
            if not ret:
                break

            if curr_frame_idx % step_frames == 0:
                faces = self.detect_faces(frame)
                for f in faces:
                    detected_faces.append(f)

            curr_frame_idx += 1

        cap.release()

        # Need at least 4 detections across the clip
        if len(detected_faces) < 4:
            return None

        all_cx = [f["cx"] for f in detected_faces]
        median_x = float(np.median(all_cx))

        left_faces = [f for f in detected_faces if f["cx"] < median_x - 30]
        right_faces = [f for f in detected_faces if f["cx"] > median_x + 30]

        # Both left and right groups must have at least 3 distinct detections
        if len(left_faces) < 3 or len(right_faces) < 3:
            # Single person or solo shot: return None to trigger clean Speaker Focus fallback!
            return None

        left_cx = float(np.median([f["cx"] for f in left_faces]))
        right_cx = float(np.median([f["cx"] for f in right_faces]))

        # Must have at least 250px separation between speaker centers
        min_separation = max(250.0, orig_w * 0.18)
        if abs(right_cx - left_cx) < min_separation:
            # Same person shifting positions; not two distinct speakers
            return None

        # Two distinct speakers confirmed! Build proportional framing boxes respecting safe area padding.
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad
        top_pad_px = int(round(target_h * top_pct))
        bottom_pad_px = int(round(target_h * bottom_pct))
        available_h = max(100, target_h - top_pad_px - bottom_pad_px)
        split_h = available_h // 2
        if split_h % 2 != 0: split_h -= 1
        split_ar = target_w / float(split_h)

        if (orig_w / float(orig_h)) >= split_ar:
            box_h = orig_h if orig_h % 2 == 0 else orig_h - 1
            box_w = int(round(box_h * split_ar))
            if box_w % 2 != 0: box_w -= 1
            if box_w > orig_w: box_w = orig_w if orig_w % 2 == 0 else orig_w - 1
        else:
            box_w = orig_w if orig_w % 2 == 0 else orig_w - 1
            box_h = int(round(box_w / split_ar))
            if box_h % 2 != 0: box_h -= 1
            if box_h > orig_h: box_h = orig_h if orig_h % 2 == 0 else orig_h - 1

        top_x = int(round(left_cx - box_w / 2.0))
        top_x = max(0, min(orig_w - box_w, top_x))
        if top_x % 2 != 0: top_x -= 1

        bottom_x = int(round(right_cx - box_w / 2.0))
        bottom_x = max(0, min(orig_w - box_w, bottom_x))
        if bottom_x % 2 != 0: bottom_x -= 1

        top_y = (orig_h - box_h) // 2
        if top_y % 2 != 0: top_y -= 1
        bottom_y = (orig_h - box_h) // 2
        if bottom_y % 2 != 0: bottom_y -= 1

        top_box = {"x": top_x, "y": top_y, "w": box_w, "h": box_h}
        bottom_box = {"x": bottom_x, "y": bottom_y, "w": box_w, "h": box_h}
        return (top_box, bottom_box)

    def get_split_screen_filter(
        self,
        top_box: Dict[str, Any],
        bottom_box: Dict[str, Any],
        target_w: int = 1080,
        target_h: int = 1920,
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        canvas_bg: str = "solid_black"
    ) -> str:
        """
        Builds FFmpeg filter complex for dual-stack split screen with universal padding support:
        Host cropped on top, Guest cropped on bottom, stacked and padded onto 1080x1920 canvas.
        """
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad
        top_pad_px = int(round(target_h * top_pct))
        bottom_pad_px = int(round(target_h * bottom_pct))
        available_h = max(100, target_h - top_pad_px - bottom_pad_px)
        split_h = available_h // 2
        if split_h % 2 != 0: split_h -= 1
        has_padding = (top_pad_px > 0 or bottom_pad_px > 0)

        if has_padding:
            if canvas_bg in ["heavy_blur", "blur"]:
                return (
                    f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                    f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                    f"[0:v]crop={top_box['w']}:{top_box['h']}:{top_box['x']}:{top_box['y']},"
                    f"scale={target_w}:{split_h}:flags=bicubic[top];"
                    f"[0:v]crop={bottom_box['w']}:{bottom_box['h']}:{bottom_box['x']}:{bottom_box['y']},"
                    f"scale={target_w}:{split_h}:flags=bicubic[bottom];"
                    f"[top][bottom]vstack[stacked];"
                    f"[bg][stacked]overlay=0:{top_pad_px}[outv]"
                )
            return (
                f"[0:v]crop={top_box['w']}:{top_box['h']}:{top_box['x']}:{top_box['y']},"
                f"scale={target_w}:{split_h}:flags=bicubic[top];"
                f"[0:v]crop={bottom_box['w']}:{bottom_box['h']}:{bottom_box['x']}:{bottom_box['y']},"
                f"scale={target_w}:{split_h}:flags=bicubic[bottom];"
                f"[top][bottom]vstack,pad={target_w}:{target_h}:0:{top_pad_px}:color=#0E0C0A[outv]"
            )
        return (
            f"[0:v]crop={top_box['w']}:{top_box['h']}:{top_box['x']}:{top_box['y']},"
            f"scale={target_w}:{split_h}:flags=bicubic[top];"
            f"[0:v]crop={bottom_box['w']}:{bottom_box['h']}:{bottom_box['x']}:{bottom_box['y']},"
            f"scale={target_w}:{split_h}:flags=bicubic[bottom];"
            f"[top][bottom]vstack[vstacked]"
        )

    def build_layout_filter(
        self,
        video_path: str,
        start_sec: float,
        duration: float,
        layout_mode: str = "speaker_focus",
        top_padding: float = 0.0,
        bottom_padding: float = 0.0,
        canvas_bg: str = "solid_black",
        target_w: int = 1080,
        target_h: int = 1920,
        enable_hook_zoom: bool = False,
        canvas_top_space: int = 450
    ) -> Tuple[str, str]:
        """
        Universal, unified framing filter generator for ALL camera layout modes:
        - fit_canvas (Uncropped widescreen fit)
        - face_center (Smart Face Center)
        - speaker_focus / gameplay (Active speaker tracking)
        - split_screen (Dual stack Host/Guest)
        - blur (Blurred vertical fill)
        - center_crop (Center vertical crop)
        Returns: (ffmpeg_filter_string, actual_layout_mode)
        """
        top_pct = max(0.0, min(45.0, float(top_padding))) / 100.0
        bottom_pct = max(0.0, min(45.0, float(bottom_padding))) / 100.0
        if top_pct + bottom_pct > 0.80:
            scale_pad = 0.80 / (top_pct + bottom_pct)
            top_pct *= scale_pad
            bottom_pct *= scale_pad

        top_pad_px = int(round(target_h * top_pct))
        bottom_pad_px = int(round(target_h * bottom_pct))
        available_h = max(100, target_h - top_pad_px - bottom_pad_px)
        has_padding = (top_pad_px > 0 or bottom_pad_px > 0)

        actual_layout = layout_mode

        if layout_mode in ["fit_canvas", "fit", "letterbox"]:
            actual_layout = "fit_canvas"
            if canvas_bg in ["heavy_blur", "blur"]:
                crop_filter = (
                    f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                    f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                    f"[0:v]scale={target_w}:{available_h}:force_original_aspect_ratio=decrease[fg];"
                    f"[bg][fg]overlay=0:{top_pad_px}+(({available_h}-h)/2)[outv]"
                )
            else:
                crop_filter = (
                    f"scale={target_w}:{available_h}:force_original_aspect_ratio=decrease,"
                    f"pad={target_w}:{target_h}:(ow-iw)/2:{top_pad_px}+(({available_h}-ih)/2):color=#0E0C0A"
                )

        elif layout_mode in ["face_center", "face_focus"]:
            actual_layout = "face_center"
            trajectory = self.compute_crop_trajectory(
                video_path=video_path,
                start_sec=start_sec,
                duration=duration,
                sample_fps=1.0,
                layout_mode="face_center",
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                target_w=target_w,
                target_h=target_h
            )
            crop_filter = self.get_ffmpeg_crop_filter(
                trajectory=trajectory,
                target_w=target_w,
                target_h=target_h,
                enable_hook_zoom=False,
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                canvas_bg=canvas_bg
            )

        elif layout_mode in ["blur", "blurred_fill"]:
            actual_layout = "blur"
            if has_padding:
                crop_filter = (
                    f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                    f"scale={target_w}:{target_h}:flags=fast_bilinear[bg];"
                    f"[0:v]scale={target_w}:{available_h}:force_original_aspect_ratio=decrease[fg];"
                    f"[bg][fg]overlay=(W-w)/2:{top_pad_px}+(({available_h}-h)/2)[outv]"
                )
            else:
                crop_filter = (
                    f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                    f"scale={target_w}:{target_h}:flags=fast_bilinear[bg];"
                    f"[0:v]scale={target_w}:-1[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
                )

        elif layout_mode in ["center_crop", "crop"]:
            actual_layout = "center_crop"
            if has_padding:
                if canvas_bg in ["heavy_blur", "blur"]:
                    crop_filter = (
                        f"[0:v]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,"
                        f"scale={target_w}:{target_h}:flags=fast_bilinear,eq=brightness=-0.12[bg];"
                        f"[0:v]crop='min(iw,ih*({target_w}/{available_h}))':'min(ih,iw*({available_h}/{target_w}))':(iw-ow)/2:(ih-oh)/2,"
                        f"scale={target_w}:{available_h}:flags=bicubic[fg];"
                        f"[bg][fg]overlay=0:{top_pad_px}[outv]"
                    )
                else:
                    crop_filter = (
                        f"crop='min(iw,ih*({target_w}/{available_h}))':'min(ih,iw*({available_h}/{target_w}))':(iw-ow)/2:(ih-oh)/2,"
                        f"scale={target_w}:{available_h}:flags=bicubic,"
                        f"pad={target_w}:{target_h}:0:{top_pad_px}:color=#0E0C0A"
                    )
            else:
                crop_filter = f"crop=ih*(9/16):ih:(iw-ow)/2:0,scale={target_w}:{target_h}:flags=bicubic"

        elif layout_mode in ["split_screen", "split"]:
            dual_boxes = self.detect_dual_speakers(
                video_path=video_path,
                start_sec=start_sec,
                duration=duration,
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                target_w=target_w,
                target_h=target_h
            )
            if dual_boxes:
                actual_layout = "split_screen"
                top_box, bottom_box = dual_boxes
                crop_filter = self.get_split_screen_filter(
                    top_box=top_box,
                    bottom_box=bottom_box,
                    target_w=target_w,
                    target_h=target_h,
                    top_padding=top_padding,
                    bottom_padding=bottom_padding,
                    canvas_bg=canvas_bg
                )
            else:
                actual_layout = "speaker_focus"
                trajectory = self.compute_crop_trajectory(
                    video_path=video_path,
                    start_sec=start_sec,
                    duration=duration,
                    sample_fps=1.0,
                    top_padding=top_padding,
                    bottom_padding=bottom_padding,
                    target_w=target_w,
                    target_h=target_h
                )
                crop_filter = self.get_ffmpeg_crop_filter(
                    trajectory=trajectory,
                    target_w=target_w,
                    target_h=target_h,
                    enable_hook_zoom=enable_hook_zoom,
                    top_padding=top_padding,
                    bottom_padding=bottom_padding,
                    canvas_bg=canvas_bg
                )

        else: # speaker_focus / gameplay / default
            actual_layout = "speaker_focus"
            trajectory = self.compute_crop_trajectory(
                video_path=video_path,
                start_sec=start_sec,
                duration=duration,
                sample_fps=1.0,
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                target_w=target_w,
                target_h=target_h
            )
            crop_filter = self.get_ffmpeg_crop_filter(
                trajectory=trajectory,
                target_w=target_w,
                target_h=target_h,
                enable_hook_zoom=enable_hook_zoom,
                top_padding=top_padding,
                bottom_padding=bottom_padding,
                canvas_bg=canvas_bg
            )

        return (crop_filter, actual_layout)

