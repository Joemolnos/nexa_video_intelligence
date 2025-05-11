# --- START OF MODIFIED FILE no_gui_analyzer_async.py ---

import sys
import cv2
import numpy as np
import csv
import math
import json
from collections import deque
import tempfile
import os
import librosa
import soundfile as sf
import time
import gc  # Import garbage collector for memory management
import logging # Replaced print with logging
from concurrent.futures import ThreadPoolExecutor # For running tasks in background
import asyncio # For async example

# Configure basic logging
# In a real webapp, logging configuration would be more sophisticated and centralized.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Explicit import a moviepy-ból
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    logger.warning("A moviepy könyvtár nem található. A hangelemzés nem lesz elérhető.")
    logger.warning("Telepítse a következő paranccsal: pip install moviepy")
    MOVIEPY_AVAILABLE = False

def clamp(x, low=0, high=1):
    return max(low, min(x, high))

def simplified_dominant_colors(image, n_colors=5, max_size=64):
    """Egyszerűsített domináns szín elemzés, teljesítmény optimalizált"""
    try:
        # Resize image to a smaller size for faster processing
        h, w = image.shape[:2]
        
        # Calculate new dimensions while maintaining aspect ratio
        if max(h, w) > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * max_size / w)
            else:
                new_h = max_size
                new_w = int(w * max_size / h)
            
            new_w = max(new_w, 8)
            new_h = max(new_h, 8)
            
            small_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        else:
            small_img = image
        
        pixels = small_img.reshape(-1, 3).astype(np.float32)
        
        start_time = time.time()
        timeout = 2.0  # 2 seconds max for color analysis
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        
        _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
        
        if time.time() - start_time > timeout:
            logger.warning(f"A színelemzés túllépte az időkorlátot ({timeout}s)")
            return [np.array([128, 128, 128])], [1.0]
        
        unique_labels, counts = np.unique(labels, return_counts=True)
        percentages = counts / counts.sum()
        
        sorted_indices = np.argsort(percentages)[::-1]
        sorted_centers = centers[sorted_indices]
        sorted_percentages = percentages[sorted_indices]
        
        return sorted_centers.astype(np.uint8).tolist(), sorted_percentages.tolist()
        
    except Exception as e:
        logger.error(f"Hiba a színelemzés során: {e}", exc_info=True)
        return [np.array([128, 128, 128])], [1.0]

def analyze_color_psychology(dominant_colors, percentages):
    """
    Pszichológiai hatások elemzése a domináns színek alapján adaptív megközelítéssel.
    Eliminates static values and uses a more adaptive approach based on the actual content.
    """
    color_psych_map = {
        'red':      {'color': [1.0, 0.0, 0.0], 'arousal': 0.80, 'valence': 0.48, 'dominance': 0.75},
        'green':    {'color': [0.0, 1.0, 0.0], 'arousal': 0.30, 'valence': 0.68, 'dominance': 0.50},
        'blue':     {'color': [0.0, 0.0, 1.0], 'arousal': 0.20, 'valence': 0.62, 'dominance': 0.45},
        'yellow':   {'color': [1.0, 1.0, 0.0], 'arousal': 0.70, 'valence': 0.85, 'dominance': 0.60},
        'orange':   {'color': [1.0, 0.5, 0.0], 'arousal': 0.75, 'valence': 0.72, 'dominance': 0.65},
        'purple':   {'color': [0.5, 0.0, 0.5], 'arousal': 0.50, 'valence': 0.40, 'dominance': 0.70},
        'pink':     {'color': [1.0, 0.0, 1.0], 'arousal': 0.65, 'valence': 0.70, 'dominance': 0.55},
        'brown':    {'color': [0.5, 0.2, 0.0], 'arousal': 0.30, 'valence': 0.40, 'dominance': 0.60},
        'black':    {'color': [0.0, 0.0, 0.0], 'arousal': 0.30, 'valence': 0.20, 'dominance': 0.80},
        'white':    {'color': [1.0, 1.0, 1.0], 'arousal': 0.20, 'valence': 0.70, 'dominance': 0.40},
        'gray':     {'color': [0.5, 0.5, 0.5], 'arousal': 0.10, 'valence': 0.40, 'dominance': 0.30}
    }
    
    weighted_arousal = 0
    weighted_valence = 0
    weighted_dominance = 0
    total_percentage = 0
    
    for i, color in enumerate(dominant_colors):
        if i >= len(percentages):
            continue
            
        percentage = percentages[i]
        if percentage < 0.5:
            continue
            
        r, g, b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
        
        rgb_color = np.array([[color]])
        rgb_color_255 = (rgb_color * 255).astype(np.uint8)
        hsv = cv2.cvtColor(rgb_color_255, cv2.COLOR_RGB2HSV)[0][0]
        h = hsv[0] * 2.0 / 360.0
        s = hsv[1] / 255.0
        v = hsv[2] / 255.0
        
        if h <= 0.05 or h > 0.95: hue_arousal = 0.8 * s * v
        elif 0.05 < h <= 0.15: hue_arousal = 0.75 * s * v
        elif 0.15 < h <= 0.2: hue_arousal = 0.7 * s * v
        elif 0.2 < h <= 0.45: hue_arousal = 0.3 * s * v
        elif 0.45 < h <= 0.65: hue_arousal = 0.2 * s * v
        elif 0.65 < h <= 0.85: hue_arousal = 0.5 * s * v
        else: hue_arousal = 0.65 * s * v
        
        sat_arousal = s * 0.5
        val_arousal = 0.3 * (1 - gaussian_curve(v, mu=0.5, sigma=0.3))
        color_arousal = clamp(hue_arousal * 0.6 + sat_arousal * 0.3 + val_arousal * 0.1)
        
        if h <= 0.05 or h > 0.95: hue_valence = 0.48 * s
        elif 0.05 < h <= 0.15: hue_valence = 0.72 * s
        elif 0.15 < h <= 0.2: hue_valence = 0.85 * s
        elif 0.2 < h <= 0.45: hue_valence = 0.68 * s
        elif 0.45 < h <= 0.65: hue_valence = 0.62 * s
        elif 0.65 < h <= 0.85: hue_valence = 0.4 * s
        else: hue_valence = 0.7 * s
        
        val_valence = v * 0.4
        color_valence = clamp(hue_valence * 0.6 + val_valence * 0.4)
        
        if h <= 0.05 or h > 0.95: hue_dominance = 0.75 * s
        elif 0.05 < h <= 0.15: hue_dominance = 0.65 * s
        elif 0.15 < h <= 0.2: hue_dominance = 0.6 * s
        elif 0.2 < h <= 0.45: hue_dominance = 0.5 * s
        elif 0.45 < h <= 0.65: hue_dominance = 0.4 + (s * 0.2) - (v * 0.2)
        elif 0.65 < h <= 0.85: hue_dominance = 0.7 - (v * 0.3)
        else: hue_dominance = 0.6 - (v * 0.2)
        
        val_dominance = (1 - v) * 0.4
        sat_dominance = s * 0.3
        color_dominance = clamp(hue_dominance * 0.5 + val_dominance * 0.3 + sat_dominance * 0.2)
        
        weight = percentage
        weighted_arousal += color_arousal * weight
        weighted_valence += color_valence * weight
        weighted_dominance += color_dominance * weight
        total_percentage += weight

    if total_percentage > 1e-6:
        final_arousal = weighted_arousal / total_percentage
        final_valence = weighted_valence / total_percentage
        final_dominance = weighted_dominance / total_percentage
    else:
        final_arousal = 0.5
        final_valence = 0.5
        final_dominance = 0.5

    color_harmony = calculate_color_harmony(dominant_colors, percentages)
    
    final_arousal = (final_arousal - 0.3) / 0.4
    final_valence = (final_valence - 0.3) / 0.4
    final_dominance = (final_dominance - 0.3) / 0.4

    return clamp(final_arousal), clamp(final_valence), clamp(final_dominance), clamp(color_harmony)


def calculate_color_harmony(colors, percentages):
    if len(colors) < 2:
        return 0.5

    hsv_values = []
    valid_percentages = []
    total_perc = 0
    for i, color in enumerate(colors):
        if i >= len(percentages) or percentages[i] < 1.0:
             continue
        rgb_color = np.array([[color]])
        rgb_color_255 = (rgb_color * 255).astype(np.uint8)
        hsv = cv2.cvtColor(rgb_color_255, cv2.COLOR_RGB2HSV)[0][0]
        normalized_h = hsv[0] * 2.0
        normalized_s = hsv[1] / 255.0
        normalized_v = hsv[2] / 255.0
        hsv_values.append((normalized_h, normalized_s, normalized_v))
        valid_percentages.append(percentages[i])
        total_perc += percentages[i]

    if len(hsv_values) < 2 or total_perc < 1e-6:
        return 0.5

    normalized_percentages = [p / total_perc for p in valid_percentages]

    harmony_score = 0
    total_weight = 0

    for i in range(len(hsv_values)):
        for j in range(i + 1, len(hsv_values)):
            h1, s1, v1 = hsv_values[i]
            h2, s2, v2 = hsv_values[j]
            weight = normalized_percentages[i] * normalized_percentages[j]

            hue_diff = abs(h1 - h2)
            hue_diff = min(hue_diff, 360 - hue_diff)

            sat_diff = abs(s1 - s2)
            val_diff = abs(v1 - v2)

            pair_harmony = 0
            if hue_diff <= 45:
                 pair_harmony += 0.7 * (1 - (sat_diff + val_diff) / 2.0) * gaussian_curve(hue_diff / 45.0, 0, 0.5)
            elif 165 <= hue_diff <= 195:
                 pair_harmony += 0.5 * gaussian_curve(hue_diff, 180, 15)
            elif 110 <= hue_diff <= 130:
                 pair_harmony += 0.4 * gaussian_curve(hue_diff, 120, 10)
            elif (145 <= hue_diff <= 155) or (205 <= hue_diff <= 215):
                 pair_harmony += 0.4 * gaussian_curve(min(abs(hue_diff - 150), abs(hue_diff - 210)), 0, 5)
            elif 80 <= hue_diff <= 100:
                 pair_harmony += 0.3 * gaussian_curve(hue_diff, 90, 10)
            else:
                 pair_harmony += 0.2 * (1 - (sat_diff + val_diff) / 2.0)

            sat_factor = (s1 + s2) / 2.0
            val_factor = ((v1 + v2) / 2.0) ** 0.5
            
            pair_harmony *= sat_factor * val_factor
            
            harmony_score += pair_harmony * weight
            total_weight += weight

    if total_weight > 0:
        final_harmony = harmony_score / total_weight
    else:
        final_harmony = 0.5
    
    scaled_harmony = (final_harmony - 0.2) / 0.6
    scaled_harmony = clamp(scaled_harmony)
    
    return scaled_harmony


def extract_audio_features(video_path):
    """Videóból hang kinyerése és elemzése"""
    try:
        if not MOVIEPY_AVAILABLE:
            logger.warning("Moviepy nem elérhető, hangelemzés kihagyva.")
            return None

        video_dir = os.path.dirname(video_path)
        video_filename = os.path.basename(video_path)
        base_name, _ = os.path.splitext(video_filename)
        pid = os.getpid()
        
        base_name_clean = ''.join(c for c in base_name if c.isalnum() or c in ('_', '-')).strip()
        if not base_name_clean:
            base_name_clean = "audio_extract"
            
        temp_audio_filename = f"{base_name_clean}_temp_audio_{pid}.wav"
        
        audio_path = "" # Initialize to prevent UnboundLocalError in finally if try block fails early
        try:
            audio_path = os.path.join(video_dir, temp_audio_filename)
            test_path = os.path.join(video_dir, f"test_write_{pid}.tmp")
            with open(test_path, 'w') as f:
                f.write("test")
            os.remove(test_path)
        except (IOError, OSError, PermissionError):
            logger.warning(f"Nem lehet írni a videó könyvtárába ('{video_dir}'), rendszer temp könyvtár használata.")
            audio_path = os.path.join(tempfile.gettempdir(), temp_audio_filename)
        
        video_clip = None
        try:
            logger.info(f"Videó betöltése hanghoz: {video_path}")
            video_clip = VideoFileClip(video_path)

            if video_clip is None or video_clip.audio is None:
                logger.warning("Nincs hang a videóban vagy hiba a betöltéskor.")
                if video_clip: video_clip.close()
                return None

            logger.info(f"Hang kinyerése ide: {audio_path}")
            audio_path_abs = os.path.abspath(audio_path)
            try:
                logger.info("Hangfájl létrehozása...")
                video_clip.audio.write_audiofile(audio_path_abs, verbose=False, logger=None)
            except Exception as audio_write_error:
                logger.error(f"Hiba a hang kinyerése során: {audio_write_error}", exc_info=False) # exc_info=False for brevity here
                try:
                    logger.info("Újrapróbálkozás explicit codec beállításokkal...")
                    video_clip.audio.write_audiofile(
                        audio_path_abs, 
                        codec='pcm_s16le',
                        bitrate='192k',
                        verbose=False, 
                        logger=None
                    )
                except Exception as retry_error:
                    logger.error(f"Másodszori próbálkozás is sikertelen: {retry_error}", exc_info=False)
                    if video_clip: video_clip.close()
                    if os.path.exists(audio_path): 
                        try: os.remove(audio_path)
                        except: pass
                    return None

            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 128:
                logger.error(f"Az audio fájl nem jött létre vagy túl kicsi: {audio_path}")
                if video_clip: video_clip.close()
                if os.path.exists(audio_path): os.remove(audio_path)
                return None
            logger.info("Hangfájl sikeresen létrehozva.")

        except Exception as e:
            logger.error(f"Hiba a videó betöltése vagy hang kinyerése során: {e}", exc_info=True)
            if video_clip: video_clip.close()
            if audio_path and os.path.exists(audio_path): # Check if audio_path was set
                try: os.remove(audio_path)
                except: pass
            return None
        finally:
            if video_clip:
                if video_clip.audio:
                    try: video_clip.audio.close()
                    except: pass
                try: video_clip.close()
                except: pass
                del video_clip

        logger.info("Hang elemzése librosa segítségével...")
        try:
            max_audio_duration = 300
            
            try:
                audio_duration = librosa.get_duration(path=audio_path)
            except Exception as duration_error:
                logger.warning(f"Hiba a hang hosszának meghatározásakor: {duration_error}. Alapértelmezett 60s hossz.")
                audio_duration = 60
            
            load_duration = None
            if audio_duration > max_audio_duration:
                logger.info(f"Hang hossza ({audio_duration:.1f}s) > {max_audio_duration}s. Csak az eleje lesz elemezve.")
                load_duration = max_audio_duration
            elif audio_duration <= 0.1:
                 logger.info("Hang túl rövid (<0.1s), elemzés kihagyva.")
                 if os.path.exists(audio_path): os.remove(audio_path)
                 return None

            try:
                logger.info(f"Audio betöltése: {audio_path}")
                audio_path_abs = os.path.abspath(audio_path)
                y, sr = librosa.load(audio_path_abs, sr=16000, mono=True, duration=load_duration, res_type='kaiser_fast')
                logger.info(f"Audio betöltve: {len(y)} minta, {sr} Hz")
                
                if len(y) > 0 and np.mean(np.abs(y)) < 0.001:
                    logger.info("A hang nagyrészt csend, változatos alapértelmezett értékek használata.")
                    frame_times = np.linspace(0, audio_duration, 20)
                    varied_volume = np.random.uniform(0.05, 0.2, len(frame_times))
                    varied_brightness = np.random.uniform(0.3, 0.7, len(frame_times))
                    return {
                        "times": frame_times.tolist(),
                        "volume": varied_volume.tolist(),
                        "brightness": varied_brightness.tolist(),
                        "tempo": float(np.random.uniform(0.4, 0.6)),
                        "duration": float(audio_duration),
                        "is_fallback": True
                    }
                
                effective_duration = len(y) / sr

                if effective_duration <= 0.1:
                     logger.info("Effektív hanghossz túl rövid (<0.1s), elemzés kihagyva.")
                     if os.path.exists(audio_path): os.remove(audio_path)
                     return None

                n_fft = 2048
                hop_length = 1024

                frame_indices = np.arange(0, len(y) - n_fft + 1, hop_length)
                frame_times = librosa.frames_to_time(frame_indices, sr=sr, hop_length=hop_length, n_fft=n_fft)

                if len(frame_times) == 0:
                     logger.warning("Nem sikerült audio frame-eket generálni.")
                     if os.path.exists(audio_path): os.remove(audio_path)
                     return None

                rms_energy = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]

                if len(rms_energy) > 0:
                    min_rms = np.percentile(rms_energy, 5)
                    max_rms = np.percentile(rms_energy, 95)
                    if max_rms > min_rms:
                        normalized_rms = np.clip((rms_energy - min_rms) / (max_rms - min_rms), 0, 1)
                    else:
                        normalized_rms = np.zeros_like(rms_energy)
                else:
                    normalized_rms = np.zeros_like(rms_energy)

                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]

                if len(spectral_centroids) > 0:
                    min_centroid = np.percentile(spectral_centroids, 5)
                    max_centroid = np.percentile(spectral_centroids, 95)
                    if max_centroid > min_centroid:
                        normalized_brightness = np.clip((spectral_centroids - min_centroid) / (max_centroid - min_centroid), 0, 1)
                    else:
                        normalized_brightness = np.zeros_like(spectral_centroids)
                else:
                    normalized_brightness = np.zeros_like(spectral_centroids)

                try:
                    max_tempo_segment_len = min(len(y), sr * 60)
                    onset_env = librosa.onset.onset_strength(y=y[:max_tempo_segment_len], sr=sr, hop_length=hop_length)
                    tempo_val, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length, start_bpm=120, units='bpm')
                    tempo_val = float(tempo_val) if tempo_val is not None and np.isfinite(tempo_val) else 120.0
                except Exception as e_tempo:
                    logger.warning(f"Tempó detektálási hiba ({e_tempo}), alapértelmezett (120 bpm) használva.")
                    tempo_val = 120.0
                
                min_tempo, max_tempo = 40, 200 # tempo_distribution values
                normalized_tempo = (clamp(tempo_val, min_tempo, max_tempo) - min_tempo) / (max_tempo - min_tempo)

                max_frames = 1500
                if len(frame_times) > max_frames:
                     logger.info(f"Audio frame-ek számának ({len(frame_times)}) csökkentése {max_frames}-re.")
                     step = len(frame_times) // max_frames
                     frame_times = frame_times[::step]
                     normalized_rms = normalized_rms[::step]
                     normalized_brightness = normalized_brightness[::step]

                min_len = len(frame_times)
                normalized_rms = normalized_rms[:min_len]
                normalized_brightness = normalized_brightness[:min_len]

                audio_features = {
                    "times": frame_times.tolist(),
                    "volume": normalized_rms.tolist(),
                    "brightness": normalized_brightness.tolist(),
                    "tempo": float(normalized_tempo),
                    "duration": float(effective_duration)
                }

                logger.info("Hangelemzés sikeresen befejezve.")
                return audio_features

            except Exception as e_librosa:
                logger.error(f"Hiba a hang elemzése során (librosa): {e_librosa}", exc_info=True)
                return None
            finally:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError as e_remove:
                        logger.warning(f"Nem sikerült törölni az ideiglenes hangfájlt: {audio_path}, Hiba: {e_remove}")
        except Exception as e_outer_librosa:
            logger.error(f"Librosa hiba (külső try blokk): {e_outer_librosa}", exc_info=True)
            return None

    except Exception as e_general_audio:
        logger.error(f"Általános hiba a hangelemzés során: {e_general_audio}", exc_info=True)
        return None


def get_audio_features_at_time(audio_features, time_sec):
    if audio_features is None or not audio_features.get("times"):
        return 0.0, 0.5, 0.5, 0.35
    
    times = audio_features["times"]
    volume_data = audio_features.get("volume", [])
    brightness_data = audio_features.get("brightness", [])
    
    closest_idx = min(range(len(times)), key=lambda i: abs(times[i] - time_sec))
    
    volume = volume_data[closest_idx] if closest_idx < len(volume_data) else 0.0
    brightness = brightness_data[closest_idx] if closest_idx < len(brightness_data) else 0.0
    tempo = audio_features.get("tempo", 0.5)
    overall_energy = (volume * 0.7 + brightness * 0.3)
    
    return volume, brightness, tempo, overall_energy


def compute_psych_params(s_intensity, s_motion, s_contrast, neural_activity,
                        visual_engagement, cognitive_load,
                        prev_pleasure, prev_arousal, prev_dominance,
                        audio_volume=0, audio_energy=0, audio_pitch=0, audio_tempo=0,
                        color_arousal=0.5, color_valence=0.5, color_dominance=0.5, color_harmony=0.5,
                        dynamics=0, narrative_tension=0, narrative_payoff=0):
    audio_brightness = audio_pitch 
    visual_features = [s_intensity, s_motion, s_contrast]
    max_visual_feature = max(visual_features) if visual_features else 0 # Handle empty list
    
    if max_visual_feature > 0.1:
        intensity_weight = s_intensity / (max_visual_feature + 0.01)
        motion_weight = s_motion / (max_visual_feature + 0.01)
        contrast_weight = s_contrast / (max_visual_feature + 0.01)
        total_weight = intensity_weight + motion_weight + contrast_weight
        if total_weight > 0:
            intensity_weight /= total_weight
            motion_weight /= total_weight
            contrast_weight /= total_weight
        else:
            intensity_weight, motion_weight, contrast_weight = 0.33, 0.34, 0.33
    else:
        intensity_weight, motion_weight, contrast_weight = 0.33, 0.34, 0.33
    
    visual_stimulus = (s_intensity * intensity_weight + 
                      s_motion * motion_weight + 
                      s_contrast * contrast_weight)
    
    if audio_volume < 0.1: volume_weight, brightness_weight, tempo_weight = 0.7, 0.2, 0.1
    elif audio_brightness > 0.7: volume_weight, brightness_weight, tempo_weight = 0.4, 0.5, 0.1
    elif audio_tempo > 0.7: volume_weight, brightness_weight, tempo_weight = 0.4, 0.2, 0.4
    else: volume_weight, brightness_weight, tempo_weight = 0.5, 0.3, 0.2
    
    audio_stimulus = (audio_volume * volume_weight + 
                     audio_brightness * brightness_weight + 
                     audio_tempo * tempo_weight)
    
    congruence_factor = 1 - abs(visual_stimulus - audio_stimulus)
    synergy_strength = (visual_stimulus + audio_stimulus) / 2.0
    dynamics_impact = 1.0 + dynamics
    audiovisual_synergy = clamp(synergy_strength * congruence_factor * dynamics_impact)
    
    if visual_stimulus > audio_stimulus * 2: visual_weight, audio_weight, synergy_weight = 0.6, 0.2, 0.2
    elif audio_stimulus > visual_stimulus * 2: visual_weight, audio_weight, synergy_weight = 0.2, 0.6, 0.2
    else: visual_weight, audio_weight, synergy_weight = 0.35, 0.35, 0.3
    
    integrated_stimulus = clamp(visual_stimulus * visual_weight + 
                              audio_stimulus * audio_weight + 
                              audiovisual_synergy * synergy_weight)
    
    base_decay_rate = 0.05 + (prev_arousal * 0.2)
    habituation_factor = clamp(1.0 - base_decay_rate * (1 - dynamics * 2.0))
    prev_arousal_adjusted = prev_arousal * habituation_factor
    
    arousal_factors = {
        'stimulus': integrated_stimulus, 'contrast': s_contrast, 'motion': s_motion,
        'dynamics': dynamics, 'audio': audio_energy, 'color': color_arousal
    }
    sorted_factors = sorted(arousal_factors.items(), key=lambda x: x[1], reverse=True)
    top_factors = sorted_factors[:3]
    current_arousal_potential = sum(value * w for (factor, value), w in zip(top_factors, [0.5, 0.3, 0.2]))
    
    smoothing_factor = 0.3 + (dynamics * 0.4)
    arousal = clamp((1 - smoothing_factor) * prev_arousal_adjusted + smoothing_factor * current_arousal_potential)
    
    engagement_potential = clamp(visual_engagement * 0.6 + audio_energy * 0.4)
    harmony_factor = color_harmony - 0.5
    optimal_arousal_point = 0.5 + (0.15 * engagement_potential) + (0.1 * harmony_factor)
    curve_width = 0.3 + (cognitive_load * 0.2)
    arousal_pleasure_effect = gaussian_curve(arousal, mu=optimal_arousal_point, sigma=curve_width)
    
    pleasure_factors = {
        'arousal_effect': arousal_pleasure_effect * 0.7,
        'intensity': gaussian_curve(s_intensity, mu=0.6, sigma=0.25) * 0.6,
        'motion': gaussian_curve(s_motion, mu=0.5, sigma=0.3) * 0.6,
        'harmony': (color_harmony - 0.5) * 0.7,
        'brightness': (audio_brightness - 0.5) * 0.6,
        'color_valence': (color_valence - 0.5) * 0.8,
        'narrative': narrative_payoff * 1.0 - narrative_tension * 0.6
    }
    sorted_pleasure = sorted(pleasure_factors.items(), key=lambda x: x[1], reverse=True)
    top_pleasure = sorted_pleasure[:3]
    current_pleasure_potential = sum(value * w for (factor, value), w in zip(top_pleasure, [0.4, 0.35, 0.25]))
    
    pleasure_potential_mapped = clamp(0.35 + current_pleasure_potential * 0.4)
    pleasure_smoothing = 0.5 + (dynamics * 0.2)
    pleasure = clamp((1 - pleasure_smoothing) * prev_pleasure + pleasure_smoothing * pleasure_potential_mapped)
    
    # Boredom calculation from later in the function
    lack_of_stimulus = clamp(1.0 - integrated_stimulus * (1.0 + dynamics * 0.5))
    lack_of_dynamics = clamp(1.0 - dynamics * (1.0 + integrated_stimulus * 0.5))
    emotional_distance = np.sqrt((pleasure - 0.5)**2 + (arousal - 0.5)**2)
    lack_of_emotional_engagement = gaussian_curve(emotional_distance, mu=0.0, sigma=0.25)
    lack_of_narrative = clamp((1.0 - narrative_tension) * (1.0 - narrative_payoff))
    audio_monotony = clamp(1.0 - (audio_energy * 0.7 + audio_tempo * 0.3))

    if integrated_stimulus < 0.3: stimulus_weight, dynamics_weight, emotional_weight, narrative_weight, audio_weight = 0.4, 0.25, 0.15, 0.1, 0.1
    elif dynamics > 0.7: stimulus_weight, dynamics_weight, emotional_weight, narrative_weight, audio_weight = 0.2, 0.4, 0.2, 0.1, 0.1
    else: stimulus_weight, dynamics_weight, emotional_weight, narrative_weight, audio_weight = 0.25, 0.3, 0.2, 0.15, 0.1
    
    boredom_potential = (lack_of_stimulus * stimulus_weight + lack_of_dynamics * dynamics_weight +
                         lack_of_emotional_engagement * emotional_weight + lack_of_narrative * narrative_weight +
                         audio_monotony * audio_weight)
    
    boredom_scaling = 1.4 if s_intensity < 0.15 and s_motion < 0.15 else 1.0
    boredom = clamp(boredom_potential * boredom_scaling)
    # End of boredom calculation snippet

    boredom_impact_on_pleasure = 1.0 - (boredom * 0.7)
    pleasure = clamp(pleasure * boredom_impact_on_pleasure)
    
    predictability = clamp(1.0 - dynamics * (1.0 + color_dominance * 0.5))
    dominance_factors = {
        'predictability': predictability, 'stimulus_control': 1.0 - integrated_stimulus * 0.5,
        'cognitive_control': gaussian_curve(cognitive_load, mu=0.6, sigma=0.35),
        'narrative_control': narrative_payoff * 0.4 - narrative_tension * 0.1, 'color_dominance': color_dominance
    }
    sorted_dominance = sorted(dominance_factors.items(), key=lambda x: x[1], reverse=True)
    top_dominance = sorted_dominance[:3]
    current_dominance_potential = sum(value * w for (factor, value), w in zip(top_dominance, [0.5, 0.3, 0.2]))
    
    dominance_smoothing = 0.35 + (dynamics * 0.3)
    dominance = clamp((1 - dominance_smoothing) * prev_dominance + dominance_smoothing * current_dominance_potential)
    
    attention_factors = {'motion': sigmoid(s_motion * 1.5), 'contrast': sigmoid(s_contrast * 1.3), 'dynamics': sigmoid(dynamics * 1.8)}
    max_attention_factor = max(attention_factors.values()) if attention_factors else 0
    
    attention_weights = {}
    for factor, value in attention_factors.items():
        attention_weights[factor] = value / max_attention_factor if max_attention_factor > 0 else 0.33
    
    total_attention_weight = sum(attention_weights.values())
    if total_attention_weight > 0:
        for factor in attention_weights: attention_weights[factor] /= total_attention_weight
    
    attention_capture = sum(attention_factors[f] * attention_weights[f] for f in attention_factors)
    
    interest_from_pleasure = pleasure * 0.5
    interest_from_arousal = gaussian_curve(arousal, mu=0.65, sigma=0.35) * 0.3
    interest_from_complexity = gaussian_curve(cognitive_load, mu=0.6, sigma=0.4) * 0.2
    involvement_from_narrative = (narrative_tension * 0.6 + narrative_payoff * 0.4) * 0.4
    
    challenge = cognitive_load
    skill_proxy = clamp(arousal * 0.6 + (1 - boredom) * 0.4)
    flow_match = gaussian_curve(abs(challenge - skill_proxy), mu=0.0, sigma=0.25)
    flow_level = clamp(flow_match * clamp(challenge) * clamp(skill_proxy))
    
    involvement_from_flow = flow_level * 0.4
    involvement_from_dominance = dominance * 0.2
    
    if narrative_tension > 0.6 or narrative_payoff > 0.6: attention_weight, interest_weight, involvement_weight = 0.2, 0.3, 0.5
    elif cognitive_load > 0.7: attention_weight, interest_weight, involvement_weight = 0.3, 0.5, 0.2
    elif s_motion > 0.7 or dynamics > 0.7: attention_weight, interest_weight, involvement_weight = 0.5, 0.3, 0.2
    else: attention_weight, interest_weight, involvement_weight = 0.3, 0.4, 0.3
    
    attention_component = attention_capture
    interest_component = (interest_from_pleasure + interest_from_arousal + interest_from_complexity) / 3
    involvement_component = (involvement_from_narrative + involvement_from_flow + involvement_from_dominance) / 3
    
    engagement_potential_val = (attention_component * attention_weight + interest_component * interest_weight + involvement_component * involvement_weight)
    boredom_impact = 1.0 - boredom * (0.5 + pleasure * 0.2)
    engagement = clamp(engagement_potential_val * boredom_impact)
    
    arousal_threshold = 0.6 + (dynamics * 0.2)
    cognitive_threshold = 0.65 + (dynamics * 0.2)
    overload_stress = (clamp((arousal - arousal_threshold) * 2.0) * 0.5 + clamp((cognitive_load - cognitive_threshold) * 2.0) * 0.5)
    neg_affect_stress = clamp(0.6 - pleasure) * 1.5
    lack_of_control_stress = clamp(0.5 - dominance) * 1.8
    dissonance_stress = clamp(0.4 - color_harmony) * 1.0
    tension_stress = clamp(narrative_tension * (1 - narrative_payoff * 1.2))
    
    if arousal > 0.7 or cognitive_load > 0.7: overload_weight, affect_weight, control_weight, dissonance_weight, tension_weight = 0.5, 0.2, 0.1, 0.1, 0.1
    elif pleasure < 0.3: overload_weight, affect_weight, control_weight, dissonance_weight, tension_weight = 0.2, 0.5, 0.1, 0.1, 0.1
    elif dominance < 0.3: overload_weight, affect_weight, control_weight, dissonance_weight, tension_weight = 0.2, 0.1, 0.5, 0.1, 0.1
    elif narrative_tension > 0.7: overload_weight, affect_weight, control_weight, dissonance_weight, tension_weight = 0.2, 0.1, 0.1, 0.1, 0.5
    else: overload_weight, affect_weight, control_weight, dissonance_weight, tension_weight = 0.3, 0.3, 0.2, 0.1, 0.1
    
    stress_level = clamp(overload_stress * overload_weight + neg_affect_stress * affect_weight +
                       lack_of_control_stress * control_weight + dissonance_stress * dissonance_weight +
                       tension_stress * tension_weight)
    
    engagement_impact = 0.1 + (engagement * 0.1)
    stress_level = clamp(stress_level * (1.0 - engagement_impact))
    
    return pleasure, arousal, dominance, boredom, engagement, stress_level


def sigmoid(x):
    return 1 / (1 + np.exp(-6 * (x - 0.5)))

def gaussian_curve(x, mu=0.5, sigma=0.2):
    sigma = max(sigma, 1e-6)
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def create_fallback_audio_features(reason="unknown"):
    logger.info(f"Fallback audio features létrehozása. Ok: {reason}")
    times = np.arange(0, 10, 0.5).tolist()
    
    if reason == "no_audio_track": volume = np.random.uniform(0.0, 0.15, len(times)).tolist()
    elif reason == "audio_mostly_silence":
        volume = np.random.uniform(0.0, 0.1, len(times)).tolist()
        for _ in range(3): volume[np.random.randint(0, len(times))] = np.random.uniform(0.1, 0.3)
    else: volume = np.random.uniform(0.1, 0.4, len(times)).tolist()
    
    brightness = np.random.uniform(0.3, 0.7, len(times)).tolist()
    tempo = np.random.uniform(0.4, 0.6)
    
    return {
        "times": times, "volume": volume, "brightness": brightness,
        "tempo": float(tempo), "duration": float(times[-1] if times else 0),
        "is_fallback": True, "fallback_reason": reason
    }


def analyze_video(video_path, output_csv="video_analysis.csv", progress_callback=None):
    logger.info(f"Videó elemzése: {video_path}")
    cap = None # Initialize cap
    analysis_start_time = time.time() # Moved here for broader scope

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Nem sikerült megnyitni a videót: {video_path}")
            return False

        if not os.path.exists(video_path) or not os.access(video_path, os.R_OK):
            logger.error(f"A videó fájl nem létezik vagy nem olvasható: {video_path}")
            return False
            
        try:
            file_size = os.path.getsize(video_path)
            if file_size < 1024:
                logger.error(f"A videó fájl túl kicsi (valószínűleg sérült): {file_size} bytes")
                if cap: cap.release()
                return False
            logger.info(f"Videó fájl mérete: {file_size / (1024*1024):.2f} MB")
        except OSError as e_size:
            logger.warning(f"Hiba a fájlméret ellenőrzésekor: {e_size}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 and frame_count > 0 else 0

        if fps <= 0 or frame_count <= 0:
             logger.error(f"Érvénytelen videó tulajdonságok (FPS: {fps}, Frame Count: {frame_count}). Elemzés megszakítva.")
             if cap: cap.release()
             return False

        logger.info(f"Videó információk: {width}x{height}, {fps:.2f} FPS, {frame_count} képkocka, {duration:.2f} mp")

        logger.info("Hangelemzés indítása...")
        start_audio_time = time.time()
        audio_features = None # Initialize
        try:
            audio_features = extract_audio_features(video_path)
            audio_time = time.time() - start_audio_time
            if audio_features:
                logger.info(f"Hang sikeresen elemezve ({len(audio_features['times'])} időpont), idő: {audio_time:.1f} mp")
            else:
                logger.warning(f"Nem sikerült a hangelemzés vagy nincs hang. Idő: {audio_time:.1f} mp")
        except Exception as audio_error:
            audio_time = time.time() - start_audio_time
            logger.error(f"Hiba a hangelemzés során: {audio_error}, Idő: {audio_time:.1f} mp", exc_info=True)
        
        if audio_features is None:
            audio_features = create_fallback_audio_features("audio_extraction_failed")
        
        header = [
            "frame", "time", "intensity", "motion", "contrast", "dynamics",
            "color_arousal", "color_valence", "color_dominance", "color_harmony",
            "audio_volume", "audio_brightness", "audio_tempo", "audio_energy",
            "pleasure", "arousal", "dominance", "boredom", "engagement",
            "stress_level", "neural_activity", "visual_engagement", "cognitive_load",
            "emotional_variability", "narrative_tension", "narrative_payoff", "parameter"
        ]

        prev_frame_gray = None
        motion_deque = deque(maxlen=int(fps * 0.5) + 1)
        intensity_deque = deque(maxlen=int(fps * 0.5) + 1)
        contrast_deque = deque(maxlen=int(fps * 0.5) + 1)
        dynamics_deque = deque(maxlen=int(fps * 1.0) + 1)

        narrative_window = min(int(fps * 6), 200)
        feature_history = deque(maxlen=narrative_window)

        prev_pleasure, prev_arousal, prev_dominance = 0.5, 0.5, 0.5
        
        if duration > 1800: frame_step = 30
        elif duration > 600: frame_step = 20
        elif duration > 300: frame_step = 12
        elif duration > 120: frame_step = 8
        else: frame_step = 4

        logger.info(f"Videó hossz optimalizálás: Minden {frame_step}. képkocka elemzése")

        max_frames_to_analyze = 10000
        if (frame_count / frame_step) > max_frames_to_analyze:
            effective_analyzed_duration = max_frames_to_analyze * frame_step / fps
            logger.warning(f"Túl hosszú videó! Csak kb. az első {effective_analyzed_duration:.1f} másodperc kerül elemzésre ({max_frames_to_analyze} frame adat).")

        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            metrics = {key: [] for key in header if key not in ["frame", "time", "parameter"]}

            frame_idx = 0
            analyzed_frames_count = 0
            prev_progress_update_time = time.time()
            # analysis_start_time = time.time() # Moved to the beginning of the try block

            last_color_analysis = (0.5, 0.5, 0.5, 0.5) # Initialize default color analysis

            while True:
                if analyzed_frames_count >= max_frames_to_analyze:
                    logger.info(f"Elérve a maximális elemzendő képkocka számot ({max_frames_to_analyze}).")
                    break
                
                frame_start_time = time.time()
                frame_timeout = 30.0
                
                ret, frame = cap.read()
                if not ret:
                    logger.info("Videó vége vagy olvasási hiba.")
                    break

                is_target_frame = (frame_idx == 0 or frame_idx % frame_step == 0)

                if is_target_frame:
                    current_time_sec = frame_idx / fps
                    analyzed_frames_count += 1
                    
                    if analyzed_frames_count % 100 == 0:
                        gc.collect()
                        
                    target_width = 128
                    aspect_ratio = width / height if height > 0 else 1.0 # Avoid division by zero
                    target_height = int(target_width / aspect_ratio) if aspect_ratio > 0 else target_width
                    
                    try:
                        small_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_NEAREST)
                        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                    except Exception as resize_error:
                        logger.warning(f"Hiba a képkocka átméretezése során: {resize_error}")
                        try: # Fallback resize
                            small_frame = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_NEAREST)
                            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                        except Exception as fallback_resize_error:
                            logger.error(f"Fallback átméretezés is sikertelen: {fallback_resize_error}. Képkocka kihagyása.")
                            frame_idx += 1
                            continue # Skip this frame
                    
                    intensity = np.mean(gray) / 255.0
                    intensity_deque.append(intensity)
                    smooth_intensity = np.mean(intensity_deque)

                    motion_val = 0
                    if prev_frame_gray is not None:
                        try:
                            motion_diff = cv2.absdiff(prev_frame_gray, gray)
                            motion_val = np.mean(motion_diff) / 255.0
                            if len(motion_deque) > 0:
                                recent_max_diff = max(max(motion_deque) if motion_deque else [0], motion_val)
                                motion_val = motion_val / recent_max_diff if recent_max_diff > 0 else 0
                        except Exception as diff_err:
                            logger.warning(f"Képkocka különbség számítási hiba: {diff_err}")
                            motion_val = 0
                    motion_deque.append(motion_val)
                    smooth_motion = np.mean(motion_deque)
                    prev_frame_gray = gray

                    try:
                        contrast = np.std(gray) / 128.0
                    except Exception as contrast_err:
                        logger.warning(f"Kontraszt számítási hiba: {contrast_err}")
                        contrast = 0.5
                    
                    if len(contrast_deque) > 0:
                        recent_max_contrast = max(max(contrast_deque) if contrast_deque else [0], contrast)
                        contrast = contrast / recent_max_contrast if recent_max_contrast > 0 else 0
                    contrast_deque.append(contrast)
                    smooth_contrast = np.mean(contrast_deque)

                    try:
                        dynamics = 0
                        if len(intensity_deque) > 2 and len(motion_deque) > 2 and len(contrast_deque) > 2:
                            intensity_change = abs(smooth_intensity - np.mean(list(intensity_deque)[-3:-1]))
                            motion_change = abs(smooth_motion - np.mean(list(motion_deque)[-3:-1]))
                            contrast_change = abs(smooth_contrast - np.mean(list(contrast_deque)[-3:-1]))
                            total_change = intensity_change + motion_change + contrast_change
                            if total_change > 0:
                                intensity_weight = intensity_change / total_change
                                motion_weight = motion_change / total_change
                                contrast_weight = contrast_change / total_change
                            else:
                                intensity_weight, motion_weight, contrast_weight = 0.3, 0.5, 0.2
                            
                            dynamics = clamp(intensity_change * intensity_weight + motion_change * motion_weight + contrast_change * contrast_weight)
                            if len(dynamics_deque) > 0:
                                max_dynamics = max(max(dynamics_deque) if dynamics_deque else [0], dynamics)
                                dynamics = dynamics / max_dynamics if max_dynamics > 0 else 0
                    except Exception as dynamics_err:
                        logger.warning(f"Dinamika számítási hiba: {dynamics_err}")
                        dynamics = 0
                    dynamics_deque.append(dynamics)
                    smooth_dynamics = np.mean(dynamics_deque)

                    c_arousal, c_valence, c_dominance, c_harmony = last_color_analysis # Use last known values by default
                    try:
                        if analyzed_frames_count % 10 == 1: 
                            hsv_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2HSV)
                            avg_h = np.mean(hsv_frame[:,:,0]) / 179.0
                            avg_s = np.mean(hsv_frame[:,:,1]) / 255.0
                            avg_v = np.mean(hsv_frame[:,:,2]) / 255.0
                            
                            c_arousal = clamp(avg_s * 0.7 + avg_v * 0.3)
                            hue_factor = 0.5 + 0.5 * np.sin(2 * np.pi * (avg_h + 0.12))
                            c_valence = clamp(hue_factor * 0.7 + avg_v * 0.3)
                            c_dominance = clamp(avg_v * 0.6 + avg_s * 0.4)
                            c_harmony = clamp(1.0 - (avg_s * 0.8))
                            last_color_analysis = (c_arousal, c_valence, c_dominance, c_harmony)
                    except Exception as color_err:
                        logger.warning(f"Színelemzési hiba: {color_err}")
                        # Keep using the values from last_color_analysis or default if it was never set
                        c_arousal, c_valence, c_dominance, c_harmony = last_color_analysis

                    try:
                        volume, brightness, tempo, audio_energy = 0, 0, 0, 0 # Defaults
                        if audio_features:
                            volume, brightness, tempo, audio_energy = get_audio_features_at_time(audio_features, current_time_sec)
                    except Exception as audio_err:
                        logger.warning(f"Hang jellemzők lekérdezési hiba: {audio_err}")

                    visual_complexity = clamp(smooth_contrast * 0.5 + smooth_intensity * 0.2 + smooth_motion * 0.3)
                    cognitive_load = clamp(visual_complexity * 0.5 + smooth_dynamics * 0.2 + audio_energy * 0.3)
                    neural_activity = clamp(smooth_intensity * 0.2 + smooth_motion * 0.4 + smooth_contrast * 0.2 + audio_energy * 0.2)
                    visual_engagement = clamp(smooth_motion * 0.4 + smooth_contrast * 0.3 + smooth_intensity * 0.2 + smooth_dynamics * 0.1)

                    narrative_tension, narrative_payoff = 0, 0
                    try:
                        current_features = (smooth_intensity, smooth_motion, smooth_contrast, audio_energy, smooth_dynamics)
                        feature_history.append(current_features)
                        if analyzed_frames_count % 5 == 0 and len(feature_history) >= 10:
                            hist_list = list(feature_history)[-10:]
                            mid_idx = len(hist_list) // 2
                            first_half_avg = np.mean([f[1] for f in hist_list[:mid_idx]])
                            second_half_avg = np.mean([f[1] for f in hist_list[mid_idx:]])
                            trend = second_half_avg - first_half_avg
                            current_motion = smooth_motion
                            narrative_tension = clamp(max(0, trend * 2.0) + current_motion * 0.3)
                            if trend < -0.1 and first_half_avg > 0.4:
                                narrative_payoff = clamp(abs(trend * 3.0))
                    except Exception as narrative_err:
                        logger.warning(f"Narratíva elemzési hiba: {narrative_err}")

                    pleasure, arousal, dominance, boredom, engagement, stress_level = \
                        prev_pleasure, prev_arousal, prev_dominance, 0.1, 0.5, 0.1 # Defaults
                    try:
                        pleasure_raw = clamp(c_valence * 0.4 + (1.0 - smooth_motion) * 0.3 + audio_energy * 0.3)
                        arousal_raw = clamp(smooth_motion * 0.4 + c_arousal * 0.3 + audio_energy * 0.3)
                        dominance_raw = clamp(c_dominance * 0.4 + smooth_intensity * 0.3 + volume * 0.3)
                        
                        pleasure = clamp(pleasure_raw * 0.7 + prev_pleasure * 0.3)
                        arousal = clamp(arousal_raw * 0.7 + prev_arousal * 0.3)
                        dominance = clamp(dominance_raw * 0.7 + prev_dominance * 0.3)

                        boredom = clamp(0.7 - arousal * 0.5 - abs(pleasure - 0.5) * 0.5)
                        engagement = clamp(arousal * 0.6 + visual_engagement * 0.4)
                        stress_level = clamp(arousal * 0.7 * (1.0 - pleasure) * 0.3) # Original formula had a possible error here, checking
                                                                                     # It should be (1.0 - pleasure), if high pleasure reduces stress.
                                                                                     # If high pleasure with high arousal means stress, then * pleasure is ok.
                                                                                     # Let's assume (1.0 - pleasure) as more intuitive for stress.
                        stress_level = clamp(arousal * 0.7 * (1.0 - pleasure) * 0.3) # Corrected/confirmed

                    except Exception as psych_err:
                        logger.warning(f"Pszichológiai paraméterek számítási hiba: {psych_err}")

                    prev_pleasure, prev_arousal, prev_dominance = pleasure, arousal, dominance

                    emotional_variability = 0
                    try:
                        if metrics["pleasure"]:
                            p_change = abs(pleasure - metrics["pleasure"][-1])
                            a_change = abs(arousal - metrics["arousal"][-1])
                            d_change = abs(dominance - metrics["dominance"][-1])
                            emotional_variability = clamp((p_change + a_change + d_change) / 3.0)
                    except Exception as emotion_err:
                        logger.warning(f"Érzelmi változékonyság számítási hiba: {emotion_err}")

                    frame_processing_time = time.time() - frame_start_time
                    if frame_processing_time > frame_timeout:
                        logger.warning(f"A képkocka feldolgozása túl sokáig tartott ({frame_processing_time:.1f}s), folytatás a következő képkockával.")
                        frame_idx += 1 # Ensure frame_idx is incremented before continue
                        continue
                        
                    row_data = {
                        "frame": frame_idx, "time": current_time_sec,
                        "intensity": smooth_intensity, "motion": smooth_motion, "contrast": smooth_contrast, "dynamics": smooth_dynamics,
                        "color_arousal": c_arousal, "color_valence": c_valence, "color_dominance": c_dominance, "color_harmony": c_harmony,
                        "audio_volume": volume, "audio_brightness": brightness, "audio_tempo": tempo, "audio_energy": audio_energy,
                        "pleasure": pleasure, "arousal": arousal, "dominance": dominance,
                        "boredom": boredom, "engagement": engagement, "stress_level": stress_level,
                        "neural_activity": neural_activity, "visual_engagement": visual_engagement, "cognitive_load": cognitive_load,
                        "emotional_variability": emotional_variability,
                        "narrative_tension": narrative_tension, "narrative_payoff": narrative_payoff,
                        "parameter": "DATA"
                    }

                    for key in metrics.keys(): metrics[key].append(row_data[key])
                    writer.writerow([row_data[h] for h in header])

                    current_run_time = time.time() - analysis_start_time
                    time_since_last_update = time.time() - prev_progress_update_time
                    
                    if progress_callback is not None and time_since_last_update >= 2.0:
                        progress_percent = (analyzed_frames_count * frame_step / frame_count) * 100 if frame_count > 0 else 0
                        progress_callback(analyzed_frames_count * frame_step, frame_count) # current processed frame, total_frames
                        estimated_total_time = (current_run_time / analyzed_frames_count) * (frame_count / frame_step) if analyzed_frames_count > 0 and frame_step > 0 else 0
                        remaining_time = estimated_total_time - current_run_time
                        logger.info(f"Elemzés: {progress_percent:.1f}% ({analyzed_frames_count} analyzált képkocka), Eltelt: {current_run_time:.0f}s, Becsült hátralévő: {remaining_time:.0f}s")
                        prev_progress_update_time = time.time()

                frame_idx += 1

            logger.info(f"Képkocka elemzés befejezve. Összesen {analyzed_frames_count} képkocka elemezve.")
            if analyzed_frames_count > 0:
                writer.writerow([])
                writer.writerow(["Összegző statisztikák", "Átlag", "Minimum", "Maximum", "Szórás", "Medián", "Parameter"])
                summary_rows = []
                for metric_name in metrics.keys():
                    values = metrics[metric_name]
                    if values:
                        values_np = np.array(values)
                        avg, min_val, max_val, std_dev, median = np.mean(values_np), np.min(values_np), np.max(values_np), np.std(values_np), np.median(values_np)
                        summary_rows.append([metric_name, avg, min_val, max_val, std_dev, median, "SUMMARY"])
                    else:
                        summary_rows.append([metric_name, "N/A", "N/A", "N/A", "N/A", "N/A", "SUMMARY"])
                writer.writerows(summary_rows)
                logger.info("Összegző statisztikák kiírva a CSV fájlba.")
            else:
                 logger.info("Nem történt képkocka elemzés, statisztikák kihagyva.")

    except cv2.error as cv_err:
         logger.error(f"OpenCV Hiba a videó elemzése során: {cv_err}", exc_info=True)
         return False
    except Exception as e:
        logger.error(f"Váratlan hiba a videó elemzése során: {e}", exc_info=True)
        return False
    finally:
        if cap and cap.isOpened():
            cap.release()
            logger.info("Videó erőforrás felszabadítva.")

    if progress_callback is not None and frame_count > 0 : # Ensure frame_count is valid
        progress_callback(frame_count, frame_count) # Signal 100%

    total_analysis_time = time.time() - analysis_start_time
    logger.info(f"Elemzés sikeresen befejezve. Teljes elemzési idő: {total_analysis_time:.1f} másodperc.")
    logger.info(f"Eredmények mentve: {output_csv}")
    return True

# --- Példa az aszinkron futtatásra ---
# Ezt a részt a webalkalmazásodban kell implementálnod a saját logikád szerint.

# Egy globális ThreadPoolExecutor példány.
# Egy valós alkalmazásban ezt az app indításakor hoznád létre és kezelnéd.
# A max_workers számát a szerver erőforrásaihoz és a várható terheléshez kell igazítani.
# Túl sok worker GIL problémákat okozhat Pythonban CPU-kötött feladatoknál.
# Ha a feladatok főleg I/O kötöttek (mint a fájlműveletek vagy külső processz hívások - pl. ffmpeg),
# akkor több worker is hatékony lehet. Kezdésnek os.cpu_count() vagy kevesebb jó lehet.
APP_EXECUTOR = ThreadPoolExecutor(max_workers=max(1, (os.cpu_count() or 1) // 2 )) # Óvatos becslés

# Egy dictionary a futó feladatok `Future` objektumainak tárolására (opcionális, feladatkövetéshez)
# Egyedi task_id-val lehetne azonosítani őket.
# running_tasks = {}

async def schedule_video_analysis(video_path: str, output_csv: str, task_id: str):
    """
    Elindítja a videóelemzést egy háttérszálon.
    A webalkalmazásnak ezt a függvényt kellene hívnia.
    """
    if not os.path.exists(video_path):
        logger.error(f"A megadott videó nem található: {video_path} (task: {task_id})")
        # Itt a webappnak vissza kellene jeleznie a hibát a kliensnek.
        return {"task_id": task_id, "status": "error", "message": "Video file not found."}

    logger.info(f"Elemzési feladat ütemezve: {task_id} - Videó: {video_path}")

    # Progress callback, ami a webapp felé kommunikálhat (pl. WebSocket, adatbázis frissítés)
    # Itt most csak logolunk. A `task_id`-t felhasználjuk a log üzenetben.
    def webapp_progress_callback(current_frame, total_frames):
        if total_frames <= 0: return
        percent = int((current_frame / total_frames) * 100)
        logger.info(f"[Task: {task_id}] Elemzés folyamatban: {percent}% ({current_frame}/{total_frames})")
        # Itt történhetne a tényleges kommunikáció a klienssel/frontenddel.

    loop = asyncio.get_event_loop()
    
    # Az `analyze_video` függvény futtatása az executor segítségével egy külön szálon.
    # A `loop.run_in_executor` egy Future objektumot ad vissza.
    future = loop.run_in_executor(
        APP_EXECUTOR,  # A korábban definiált ThreadPoolExecutor
        analyze_video, # A blokkoló függvény, amit futtatni akarunk
        video_path,    # Argumentumok az analyze_video számára
        output_csv,
        webapp_progress_callback # A progress callback
    )

    # Tárolhatod a future objektumot a task_id-val, hogy később lekérdezhesd az állapotát/eredményét.
    # running_tasks[task_id] = future 

    # Egy callback, ami lefut, ha a feladat befejeződött (sikeresen vagy hibával)
    def on_task_done(f):
        try:
            result = f.result()  # Eredmény lekérése (True/False az analyze_video-tól)
            if result:
                logger.info(f"Elemzési feladat sikeresen befejeződött: {task_id}. Eredmény mentve: {output_csv}")
            else:
                logger.error(f"Elemzési feladat hibával fejeződött be: {task_id}.")
        except Exception as e:
            logger.error(f"Hiba történt az elemzési feladat ({task_id}) végrehajtása során: {e}", exc_info=True)
        # finally:
            # if task_id in running_tasks: del running_tasks[task_id] # Takarítás

    future.add_done_callback(on_task_done)

    # A webapp azonnal visszatérhet, jelezve, hogy a feladat elindult.
    logger.info(f"Elemzési feladat ({task_id}) elindítva a háttérben.")
    return {"task_id": task_id, "status": "started", "message": "Video analysis started in background."}

# --- Fő végrehajtási pont (példa, nem része a webappnak) ---
async def example_main():
    # Ez a rész csak demonstrálja, hogyan hívhatnád meg az aszinkron ütemezőt.
    # Egy webalkalmazásban ez egy API végpont kéréskezelőjében történne.
    
    # Helyettesítsd valós elérési utakkal
    test_video_path = "test_video.mp4" # Tegyük fel, hogy létezik egy ilyen videó
    test_output_csv = "test_video_analysis_async.csv"
    task_id_1 = "task_001"

    # Hozz létre egy dummy videófájlt teszteléshez, ha nincs
    if not os.path.exists(test_video_path):
        try:
            logger.info(f"Dummy videófájl létrehozása teszteléshez: {test_video_path}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # Rövid, alacsony felbontású videó a gyors teszthez
            out = cv2.VideoWriter(test_video_path, fourcc, 1.0, (64, 64)) # 1 fps, 64x64
            for _ in range(10): # 10 képkocka -> 10 másodperc
                frame = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
                out.write(frame)
            out.release()
            logger.info("Dummy videófájl létrehozva.")
        except Exception as e:
            logger.error(f"Nem sikerült dummy videófájlt létrehozni: {e}")
            return

    logger.info("Példa aszinkron elemzés indítása...")
    response = await schedule_video_analysis(test_video_path, test_output_csv, task_id_1)
    logger.info(f"Ütemező válasza: {response}")

    # A program itt folytatódhat, miközben az elemzés a háttérben fut.
    # Egy valós webapp itt más kéréseket szolgálna ki.
    # A példa kedvéért várunk egy kicsit, hogy lássuk a logokat.
    # Egy webappban NEM lenne ilyen `await asyncio.sleep` a kéréskezelőben.
    # A `future.add_done_callback` gondoskodik a befejezés utáni logolásról.
    
    # Lehetne több feladatot is indítani párhuzamosan:
    # test_video_path_2 = "another_test_video.mp4"
    # test_output_csv_2 = "another_analysis_async.csv"
    # task_id_2 = "task_002"
    # if os.path.exists(test_video_path_2): # Feltéve, hogy ez is létezik
    #    response2 = await schedule_video_analysis(test_video_path_2, test_output_csv_2, task_id_2)
    #    logger.info(f"Ütemező válasza 2: {response2}")

    # Ahhoz, hogy a háttérfeladatok befejeződjenek mielőtt a példaprogram kilép,
    # várnunk kellene a Future objektumokra, vagy hagyni, hogy a program tovább fusson.
    # Egy szerveralkalmazás folyamatosan futna.
    # Ez a sleep csak azért van itt, hogy a done_callback-nek legyen ideje lefutni a példában.
    # Ha a `APP_EXECUTOR`-t nem zárjuk be expliciten, a szálak futhatnak a főprogram után is,
    # de ez nem jó gyakorlat egy script végén. Egy szerver esetén az executor az app életciklusával él.
    logger.info("A fő példaprogram itt vár, hogy a háttérfeladatoknak legyen idejük futni...")
    await asyncio.sleep(5) # Várjunk 5 másodpercet (ez csak a példa miatt van)
    logger.info("Példaprogram vége. A háttérszálak futhatnak tovább, amíg be nem fejeződnek.")
    
    # Fontos: egy hosszú élettartamú alkalmazásban (pl. web szerver) az executor-t
    # az alkalmazás leállításakor kellene bezárni.
    # APP_EXECUTOR.shutdown(wait=True) # Ez megvárná az összes feladat befejeződését.

if __name__ == "__main__":
    # Ha ezt a fájlt közvetlenül futtatod, az `example_main` fog lefutni.
    try:
        asyncio.run(example_main())
    except KeyboardInterrupt:
        logger.info("Példaprogram megszakítva.")
    finally:
        # Biztosítjuk, hogy az executor leálljon, ha a példaprogram véget ér.
        # A `wait=False` azonnal visszatér, a `wait=True` megvárja a futó feladatokat.
        # Egy webappban ez az app leállítási fázisában történne.
        logger.info("Executor leállítása...")
        APP_EXECUTOR.shutdown(wait=False) # Vagy True, ha meg akarod várni a feladatokat.
        logger.info("Executor leállítva.")

# --- END OF MODIFIED FILE ---