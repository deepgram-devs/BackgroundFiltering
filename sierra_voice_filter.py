import datetime
import threading
import asyncio
import pyaudio
import tkinter as tk
from tkinter import ttk
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions
import os
from dotenv import load_dotenv
from pathlib import Path
import ssl
import certifi
import time
import numpy as np
import re

# Load environment variables from .env file
load_dotenv()

# Sierra AI Authentic Color Palette (from sierra.ai)
SIERRA_COLORS = {
    'primary_green': '#1B4D3E',      # Forest green for text and buttons
    'secondary_green': '#2D6A4F',    # Lighter forest green for accents
    'accent_green': '#40916C',       # Bright green for highlights
    'success_green': '#52B788',      # Success states
    'background': '#F8F6F1',         # Whitish tan background
    'card_bg': '#FFFFFF',            # Pure white for cards
    'secondary_bg': '#F1EFE9',       # Slightly darker tan
    'text_primary': '#1B4D3E',       # Dark green for primary text
    'text_secondary': '#6C757D',     # Gray for secondary text
    'text_muted': '#ADB5BD',         # Light gray for muted text
    'warning': '#F77F00',            # Orange for warnings
    'danger': '#D62828',             # Red for errors
    'border': '#DEE2E6',             # Light gray borders
    'terminal_bg': '#2D3748',        # Dark background for terminal
    'terminal_text': '#E2E8F0'       # Light text for terminal
}

class AdvancedTVNoiseFilter:
    """Advanced 5-stage TV noise filtering system"""
    
    def __init__(self):
        # TV content detection phrases
        self.tv_commercial_phrases = [
            "call now", "limited time", "but wait", "act fast", "operators standing by",
            "special offer", "don't delay", "order today", "satisfaction guaranteed",
            "money back guarantee", "as seen on tv", "not sold in stores"
        ]
        
        self.tv_news_phrases = [
            "breaking news", "this just in", "we'll be right back", "coming up next",
            "stay tuned", "live from", "reporting live", "back to you", "developing story",
            "news update", "weather forecast", "traffic report"
        ]
        
        self.tv_show_phrases = [
            "previously on", "next time on", "don't touch that dial", "after these messages",
            "brought to you by", "we now return to", "tonight's episode", "season finale",
            "coming up after the break", "stay with us"
        ]
        
        # Audio analysis thresholds
        self.noise_floor_threshold = 1000
        self.tv_frequency_ranges = {
            'tv_bass_boost': (40, 100),     # TV speakers boost bass
            'tv_compression': (200, 800),   # TV audio compression artifacts  
            'tv_enhancement': (2000, 6000), # TV audio processing
        }
        
        # Statistics tracking
        self.filter_stats = {
            'stage1_frequency': 0,
            'stage2_confidence': 0, 
            'stage3_content': 0,
            'stage4_speaker_pattern': 0,
            'stage5_voice_lock': 0,
            'passed_all_stages': 0,
            'total_processed': 0
        }
    
    def stage1_frequency_analysis(self, audio_data):
        """Stage 1: Frequency domain analysis for TV audio signatures"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            
            # Basic energy check
            energy = np.sum(audio_array ** 2) / len(audio_array)
            if energy < self.noise_floor_threshold:
                return "filtered_low_energy"
            
            # Zero-crossing rate analysis
            zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
            zcr = zero_crossings / len(audio_array)
            
            # TV music/soundtrack detection (very steady)
            if zcr < 0.005:  
                return "filtered_monotonous_tv_audio"
            
            # Static/interference detection (too chaotic)
            elif zcr > 0.35:
                return "filtered_high_frequency_noise"
            
            # Frequency analysis using FFT
            fft = np.fft.fft(audio_array)
            freqs = np.fft.fftfreq(len(fft), 1/16000)
            power = np.abs(fft)
            
            # Find dominant frequency
            positive_freqs = freqs[:len(freqs)//2]
            positive_power = power[:len(power)//2]
            
            if len(positive_power) > 0:
                peak_freq = positive_freqs[np.argmax(positive_power)]
                
                # Check for TV-specific frequency signatures
                for tv_type, (low, high) in self.tv_frequency_ranges.items():
                    if low <= abs(peak_freq) <= high:
                        # Check if it's sustained (likely TV)
                        if self.is_sustained_frequency(positive_power, positive_freqs):
                            return f"filtered_{tv_type}"
            
            return "passed_stage1"
            
        except Exception as e:
            print(f"Stage 1 error: {e}")
            return "passed_stage1"  # Default to pass on error
    
    def is_sustained_frequency(self, power, freqs):
        """Check if frequency is sustained (TV) vs varied (speech)"""
        try:
            if len(power) < 10:
                return False
                
            # Find top 3 frequency peaks
            peak_indices = np.argsort(power)[-3:]
            peak_powers = power[peak_indices]
            
            # If top frequency dominates heavily, it's likely sustained TV audio
            if len(peak_powers) > 1 and peak_powers[-1] > peak_powers[-2] * 3:
                return True
            
            return False
        except:
            return False
    
    def stage2_confidence_analysis(self, result):
        """Stage 2: Deepgram confidence scoring for processed audio detection"""
        try:
            # Check transcript confidence
            if hasattr(result.channel.alternatives[0], 'confidence'):
                confidence = result.channel.alternatives[0].confidence
                
                # TV audio often has lower confidence due to processing
                if confidence < 0.4:
                    return f"filtered_very_low_confidence_{confidence:.2f}"
                elif confidence < 0.6:
                    return f"filtered_low_confidence_{confidence:.2f}"
            
            # Check word-level confidence if available
            if hasattr(result.channel.alternatives[0], 'words'):
                words = result.channel.alternatives[0].words
                if words:
                    word_confidences = [getattr(w, 'confidence', 0.5) for w in words]
                    avg_confidence = sum(word_confidences) / len(word_confidences)
                    
                    # TV dialogue often has inconsistent word confidence
                    if avg_confidence < 0.5:
                        return f"filtered_low_word_confidence_{avg_confidence:.2f}"
                    
                    # Check for confidence variation (TV audio is often inconsistent)
                    confidence_std = np.std(word_confidences) if len(word_confidences) > 1 else 0
                    if confidence_std > 0.3:  # High variation suggests processed audio
                        return f"filtered_confidence_variation_{confidence_std:.2f}"
            
            return "passed_stage2"
            
        except Exception as e:
            print(f"Stage 2 error: {e}")
            return "passed_stage2"
    
    def stage3_content_analysis(self, transcript):
        """Stage 3: Content analysis for TV-specific phrases and patterns"""
        try:
            transcript_lower = transcript.lower().strip()
            
            if not transcript_lower or len(transcript_lower) < 3:
                return "passed_stage3"  # Too short to analyze
            
            # Check for commercial phrases
            for phrase in self.tv_commercial_phrases:
                if phrase in transcript_lower:
                    return f"filtered_commercial_phrase_{phrase.replace(' ', '_')}"
            
            # Check for news phrases
            for phrase in self.tv_news_phrases:
                if phrase in transcript_lower:
                    return f"filtered_news_phrase_{phrase.replace(' ', '_')}"
            
            # Check for TV show phrases
            for phrase in self.tv_show_phrases:
                if phrase in transcript_lower:
                    return f"filtered_show_phrase_{phrase.replace(' ', '_')}"
            
            # Check for overly perfect speech (TV dialogue characteristics)
            if self.sounds_too_scripted(transcript_lower):
                return "filtered_scripted_content"
            
            # Check for rapid commercial-style speech patterns
            word_count = len(transcript_lower.split())
            if word_count > 15:  # Only analyze longer phrases
                if self.detect_commercial_speech_pattern(transcript_lower):
                    return "filtered_commercial_speech_pattern"
            
            return "passed_stage3"
            
        except Exception as e:
            print(f"Stage 3 error: {e}")
            return "passed_stage3"
    
    def sounds_too_scripted(self, transcript):
        """Detect if content sounds too scripted/perfect for natural speech"""
        # Natural speech has disfluencies
        natural_patterns = ['um', 'uh', 'ah', 'er', 'well', 'you know', 'like', 'so']
        
        words = transcript.split()
        if len(words) > 8:  # Only check longer phrases
            # Natural speech should have some disfluencies
            has_disfluency = any(pattern in transcript for pattern in natural_patterns)
            
            # Check for overly complex sentence structure (TV dialogue)
            complex_words = ['furthermore', 'consequently', 'nevertheless', 'therefore', 'however']
            has_complex_words = any(word in transcript for word in complex_words)
            
            # TV dialogue is often too perfect
            if not has_disfluency and has_complex_words:
                return True
        
        return False
    
    def detect_commercial_speech_pattern(self, transcript):
        """Detect rapid, enthusiastic commercial-style speech"""
        # Commercial indicators
        commercial_indicators = [
            '!',  # Excessive exclamation
            'amazing', 'incredible', 'fantastic', 'revolutionary',
            'percent off', '% off', 'save', 'discount',
            'free shipping', 'free trial', 'risk free'
        ]
        
        indicator_count = sum(1 for indicator in commercial_indicators if indicator in transcript)
        
        # High density of commercial language
        word_count = len(transcript.split())
        if word_count > 0:
            commercial_density = indicator_count / word_count
            return commercial_density > 0.15  # 15% commercial language
        
        return False
    
    def stage4_speaker_pattern_analysis(self, result):
        """Stage 4: Speaker diarization patterns for TV dialogue detection"""
        try:
            if not hasattr(result.channel.alternatives[0], 'words') or not result.channel.alternatives[0].words:
                return "passed_stage4"  # No speaker data
            
            words = result.channel.alternatives[0].words
            
            # Analyze speaker switching patterns
            speakers = [getattr(word, 'speaker', 0) for word in words]
            
            if len(set(speakers)) > 1:  # Multiple speakers detected
                # Count rapid speaker changes (TV dialogue characteristic)
                speaker_changes = sum(1 for i in range(1, len(speakers)) 
                                    if speakers[i] != speakers[i-1])
                
                # TV dialogue often has very rapid speaker alternation
                words_per_speaker_change = len(words) / max(speaker_changes, 1)
                
                if speaker_changes > 3 and words_per_speaker_change < 4:
                    return f"filtered_rapid_speaker_changes_{speaker_changes}"
                
                # Check for unnatural speaker timing (TV editing)
                if self.detect_unnatural_speaker_timing(words):
                    return "filtered_unnatural_speaker_timing"
            
            # Check for TV-style perfect speaker separation
            if len(set(speakers)) > 2 and len(words) < 20:
                # Too many distinct speakers in short utterance (TV scene)
                return f"filtered_too_many_speakers_{len(set(speakers))}"
            
            return "passed_stage4"
            
        except Exception as e:
            print(f"Stage 4 error: {e}")
            return "passed_stage4"
    
    def detect_unnatural_speaker_timing(self, words):
        """Detect unnaturally perfect speaker timing (TV editing)"""
        try:
            if len(words) < 6:
                return False
            
            # Check for perfectly alternating speakers (unrealistic in natural conversation)
            speakers = [getattr(word, 'speaker', 0) for word in words]
            
            # Count alternating patterns
            alternating_count = 0
            for i in range(2, len(speakers)):
                if (speakers[i] != speakers[i-1] and 
                    speakers[i-1] != speakers[i-2] and
                    speakers[i] == speakers[i-2]):
                    alternating_count += 1
            
            # Too much alternation suggests TV dialogue
            return alternating_count > len(speakers) * 0.3
            
        except:
            return False
    
    def process_audio_through_stages(self, audio_data, result=None):
        """Process audio through all 5 stages of filtering"""
        self.filter_stats['total_processed'] += 1
        
        # Stage 1: Frequency Analysis
        stage1_result = self.stage1_frequency_analysis(audio_data)
        if stage1_result.startswith('filtered_'):
            self.filter_stats['stage1_frequency'] += 1
            return stage1_result, 1
        
        # Stage 2: Confidence Analysis (requires Deepgram result)
        if result:
            stage2_result = self.stage2_confidence_analysis(result)
            if stage2_result.startswith('filtered_'):
                self.filter_stats['stage2_confidence'] += 1
                return stage2_result, 2
            
            # Stage 3: Content Analysis
            transcript = result.channel.alternatives[0].transcript
            stage3_result = self.stage3_content_analysis(transcript)
            if stage3_result.startswith('filtered_'):
                self.filter_stats['stage3_content'] += 1
                return stage3_result, 3
            
            # Stage 4: Speaker Pattern Analysis
            stage4_result = self.stage4_speaker_pattern_analysis(result)
            if stage4_result.startswith('filtered_'):
                self.filter_stats['stage4_speaker_pattern'] += 1
                return stage4_result, 4
        
        # Passed all stages
        self.filter_stats['passed_all_stages'] += 1
        return "passed_all_stages", 0
    
    def get_filter_statistics(self):
        """Get comprehensive filtering statistics"""
        total = self.filter_stats['total_processed']
        if total == 0:
            return "No audio processed yet"
        
        stats = []
        stats.append(f"📊 ADVANCED TV NOISE FILTER STATISTICS")
        stats.append(f"{'='*50}")
        stats.append(f"Total Audio Processed: {total}")
        stats.append(f"")
        stats.append(f"🎯 FILTERING STAGES:")
        stats.append(f"Stage 1 (Frequency): {self.filter_stats['stage1_frequency']} ({self.filter_stats['stage1_frequency']/total*100:.1f}%)")
        stats.append(f"Stage 2 (Confidence): {self.filter_stats['stage2_confidence']} ({self.filter_stats['stage2_confidence']/total*100:.1f}%)")
        stats.append(f"Stage 3 (Content): {self.filter_stats['stage3_content']} ({self.filter_stats['stage3_content']/total*100:.1f}%)")
        stats.append(f"Stage 4 (Speaker Pattern): {self.filter_stats['stage4_speaker_pattern']} ({self.filter_stats['stage4_speaker_pattern']/total*100:.1f}%)")
        stats.append(f"Stage 5 (Voice Lock): {self.filter_stats['stage5_voice_lock']} (tracked separately)")
        stats.append(f"")
        stats.append(f"✅ Passed All Stages: {self.filter_stats['passed_all_stages']} ({self.filter_stats['passed_all_stages']/total*100:.1f}%)")
        stats.append(f"🚫 Total Filtered: {total - self.filter_stats['passed_all_stages']} ({(total - self.filter_stats['passed_all_stages'])/total*100:.1f}%)")
        
        return "\n".join(stats)

class SierraVoiceFilter:
    def __init__(self, terminal_display, status_display):
        self.terminal_display = terminal_display
        self.status_display = status_display
        self.deepgram = None
        self.dg_connection = None
        self.audio_stream = None
        self.is_running = False
        self.loop = None
        
        # Advanced TV noise filtering system
        self.tv_filter = AdvancedTVNoiseFilter()
        
        # Speaker diarization settings (Stage 5)
        self.primary_speaker_id = None  # Track the primary user
        self.speaker_lock_enabled = True
        self.min_words_to_lock = 3  # Minimum words before locking speaker
        self.total_speakers_detected = set()
        self.filtered_count = 0
        self.accepted_count = 0
        
        # Initialize Deepgram client with SSL context
        try:
            print("🔧 Initializing Sierra Voice Filter with Deepgram...")
            self.log_to_terminal("🔧 Initializing Sierra Voice Filter with Advanced TV Noise Filtering...")
            
            # Import EmbeddedConfig for proper API key handling
            from embedded_config import EmbeddedConfig
            
            api_key = EmbeddedConfig.get_deepgram_key()
            if not api_key:
                print("❌ Warning: DEEPGRAM_API_KEY not found")
                self.log_to_terminal("❌ Warning: DEEPGRAM_API_KEY not found")
                return
            
            print(f"🔑 API Key found (length: {len(api_key)})") 
            self.log_to_terminal(f"🔑 Deepgram API Key configured")
            
            # Use SSL context for certificate verification
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            config = DeepgramClientOptions(
                options={
                    "keepalive": "true",
                    "ssl_context": ssl_context
                }
            )
            self.deepgram = DeepgramClient(api_key, config)
            print("✅ Sierra Voice Filter initialized successfully with SSL context")
            self.log_to_terminal("✅ Sierra Voice Filter with Advanced TV Filtering initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Sierra Voice Filter: {e}")
            self.log_to_terminal(f"❌ Error initializing Sierra Voice Filter: {e}")
    
    def log_to_terminal(self, message):
        """Log message to terminal display with timestamp"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            formatted_message = f"[{timestamp}] {message}\n"
            self.terminal_display.insert(tk.END, formatted_message)
            self.terminal_display.see(tk.END)
            self.terminal_display.update()
        except Exception as e:
            print(f"Error logging to terminal: {e}")
    
    def update_status(self, message, color=None):
        """Update status display"""
        try:
            if color:
                self.status_display.config(text=message, fg=color)
            else:
                self.status_display.config(text=message)
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def apply_5_stage_filtering(self, result, audio_data):
        """Apply the 5-stage TV noise filtering system"""
        self.log_to_terminal("🎯 Applying 5-stage TV noise filtering...")
        
        # Process through stages 1-4 using the advanced TV filter
        filter_result, failed_stage = self.tv_filter.process_audio_through_stages(audio_data, result)
        
        if filter_result.startswith('filtered_'):
            # Audio was filtered out at one of the first 4 stages
            stage_names = ["", "Frequency Analysis", "Confidence Scoring", "Content Analysis", "Speaker Patterns"]
            self.log_to_terminal(f"🚫 STAGE {failed_stage} FILTER: {stage_names[failed_stage]} - {filter_result}")
            
            # Log detailed reason
            reason = filter_result.replace('filtered_', '').replace('_', ' ').title()
            self.log_to_terminal(f"   Reason: {reason}")
            
            return None  # Audio filtered out before voice locking
        
        # Passed stages 1-4, now apply Stage 5 (Voice Locking)
        self.log_to_terminal("✅ Passed Stages 1-4 → Applying Stage 5 (Voice Locking)")
        return self.filter_by_primary_speaker(result)
    
    def filter_by_primary_speaker(self, result):
        """Stage 5: Filter transcript to only include primary speaker's words"""
        if not hasattr(result.channel.alternatives[0], 'words') or not result.channel.alternatives[0].words:
            self.log_to_terminal("🔍 No word-level data available, using full transcript")
            return result.channel.alternatives[0].transcript
        
        words = result.channel.alternatives[0].words
        
        # Group words by speaker
        speaker_words = {}
        for word_info in words:
            speaker_id = getattr(word_info, 'speaker', 0)
            if speaker_id not in speaker_words:
                speaker_words[speaker_id] = []
            speaker_words[speaker_id].append(word_info)
            
            # Track all detected speakers
            self.total_speakers_detected.add(speaker_id)
        
        self.log_to_terminal(f"🎤 Stage 5 - Speakers in utterance: {list(speaker_words.keys())}")
        self.log_to_terminal(f"📊 Total speakers detected in session: {len(self.total_speakers_detected)}")
        
        # Lock onto first speaker if not already locked
        if self.primary_speaker_id is None and self.speaker_lock_enabled:
            # Find speaker with most words in this utterance
            if speaker_words:
                primary_candidate = max(speaker_words.keys(), 
                                      key=lambda s: len(speaker_words[s]))
                
                # Only lock if they said enough words
                if len(speaker_words[primary_candidate]) >= self.min_words_to_lock:
                    self.primary_speaker_id = primary_candidate
                    self.log_to_terminal(f"🔒 STAGE 5 VOICE LOCK: Locked to Speaker {self.primary_speaker_id}")
                    self.update_status(f"🔒 Voice Locked to Speaker {self.primary_speaker_id}", SIERRA_COLORS['success_green'])
                    
                    # Update speaker lock display
                    try:
                        speaker_lock_label.config(text=f"🔒 Speaker {self.primary_speaker_id} Locked", 
                                                 fg=SIERRA_COLORS['success_green'])
                    except:
                        pass
        
        # Return only primary speaker's words
        if self.primary_speaker_id is not None and self.primary_speaker_id in speaker_words:
            primary_words = speaker_words[self.primary_speaker_id]
            # Reconstruct transcript from primary speaker's words only
            filtered_transcript = ' '.join([getattr(word, 'word', '') for word in primary_words])
            
            self.accepted_count += 1
            self.tv_filter.filter_stats['stage5_voice_lock'] += len([s for s in speaker_words.keys() if s != self.primary_speaker_id])
            
            self.log_to_terminal(f"✅ STAGE 5 ACCEPTED: Speaker {self.primary_speaker_id} said: '{filtered_transcript}'")
            self.log_to_terminal(f"📈 Session Stats - Accepted: {self.accepted_count} | Stage 5 Filtered: {self.filtered_count}")
            
            return filtered_transcript
        elif self.primary_speaker_id is not None:
            self.filtered_count += 1
            # Log which speakers were filtered out
            filtered_speakers = [s for s in speaker_words.keys() if s != self.primary_speaker_id]
            self.log_to_terminal(f"🚫 STAGE 5 FILTERED: Speaker(s) {filtered_speakers} (not primary speaker)")
            self.log_to_terminal(f"📈 Session Stats - Accepted: {self.accepted_count} | Stage 5 Filtered: {self.filtered_count}")
            return None
        
        # Fallback to full transcript if no speaker lock
        self.log_to_terminal("⚠️ No speaker lock active - processing all speech")
        return result.channel.alternatives[0].transcript
    
    def reset_speaker_lock(self):
        """Reset speaker lock to re-identify primary speaker"""
        self.primary_speaker_id = None
        self.total_speakers_detected = set()
        self.filtered_count = 0
        self.accepted_count = 0
        
        self.log_to_terminal("🔓 SPEAKER LOCK RESET - will re-identify on next speech")
        self.update_status("🔓 Ready to lock onto voice", SIERRA_COLORS['warning'])
        
        try:
            speaker_lock_label.config(text="🔓 No Speaker Lock", fg=SIERRA_COLORS['text_muted'])
        except:
            pass
    
    def show_filter_statistics(self):
        """Display comprehensive filtering statistics in terminal"""
        stats = self.tv_filter.get_filter_statistics()
        self.log_to_terminal("\n" + stats + "\n")
        
    def process_transcript(self, result):
        """Process the recognized text from Deepgram with 5-stage filtering"""
        try:
            # Extract text from Deepgram result
            if result.is_final:
                self.log_to_terminal(f"📝 Raw transcript received: '{result.channel.alternatives[0].transcript}'")
                
                # Apply the revolutionary 5-stage filtering system
                # This integrates all TV noise filtering with voice locking
                filtered_transcript = self.apply_5_stage_filtering(result, None)  # audio_data not available here
                
                if filtered_transcript and filtered_transcript.strip():
                    self.log_to_terminal(f"📝 Final filtered transcript: '{filtered_transcript}'")
                    
                    # Add to transcription display
                    try:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        transcription_display.insert(tk.END, f"[{timestamp}] {filtered_transcript}\n")
                        transcription_display.see(tk.END)
                        transcription_display.update()
                    except Exception as e:
                        print(f"Error updating transcription display: {e}")
                    
                    # Check for exit command
                    if "exit sierra" in filtered_transcript.lower() or "stop sierra" in filtered_transcript.lower():
                        self.log_to_terminal("🛑 Exit command detected - stopping Sierra Voice Filter")
                        self.stop_filter()
                    
                    # Check for statistics command
                    elif "show stats" in filtered_transcript.lower() or "show statistics" in filtered_transcript.lower():
                        self.show_filter_statistics()
                        
                elif filtered_transcript is None:
                    # This means the speech was filtered out by one of the 5 stages
                    pass  # Already logged in filtering stages
                    
        except Exception as e:
            self.log_to_terminal(f"❌ Error processing transcript: {e}")
            print(f"Error processing transcript: {e}")
    
    def on_message(self, result, **kwargs):
        """Handle Deepgram message events"""
        try:
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            
            self.process_transcript(result)
        except Exception as e:
            self.log_to_terminal(f"❌ Error in on_message: {e}")
    
    def on_error(self, error, **kwargs):
        """Handle Deepgram error events"""
        self.log_to_terminal(f"🔴 Deepgram error: {error}")
    
    def on_close(self, close, **kwargs):
        """Handle Deepgram connection close"""
        self.log_to_terminal(f"🔌 Deepgram connection closed: {close}")
    
    async def start_audio_stream(self):
        """Start the audio stream and Deepgram transcription"""
        try:
            self.log_to_terminal("🎯 Starting Sierra Voice Filter audio stream...")
            
            if not self.deepgram:
                self.log_to_terminal("❌ Deepgram client not initialized")
                return
                
            self.log_to_terminal("🎤 Initializing PyAudio...")
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Set up audio stream
            self.audio_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            self.log_to_terminal("✅ Audio stream initialized")
            
            # Configure Deepgram options
            self.log_to_terminal("⚙️ Configuring Deepgram with speaker diarization...")
            options = LiveOptions(
                model="nova-3",  
                language="en-US",
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                endpointing=300,
                punctuate=True,
                diarize=True,                 # ← ENABLED for speaker diarization
                encoding="linear16",
                sample_rate=16000
            )
            self.log_to_terminal("✅ Deepgram configured: model=nova-3, diarize=True")
            
            # Create a websocket connection
            self.log_to_terminal("🌐 Creating WebSocket connection...")
            self.dg_connection = self.deepgram.listen.websocket.v("1")
            
            # Store reference to access VoiceFilter instance from event handlers
            voice_filter = self
            
            # Define event handlers
            def on_open(self, open, **kwargs):
                voice_filter.log_to_terminal("🟢 Sierra Voice Filter connection opened!")
                voice_filter.update_status("🟢 Connected & Listening", SIERRA_COLORS['success_green'])

            def on_message(self, result, **kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) == 0:
                        return
                    
                    if result.is_final:
                        voice_filter.log_to_terminal(f"📝 Raw transcript received: '{sentence}'")
                        voice_filter.process_transcript(result)
                    else:
                        voice_filter.log_to_terminal(f"📝 Interim: '{sentence}'")
                except Exception as e:
                    voice_filter.log_to_terminal(f"❌ Error in transcript handler: {e}")

            def on_error(self, error, **kwargs):
                voice_filter.log_to_terminal(f"🔴 Deepgram error: {error}")
                voice_filter.update_status("🔴 Connection Error", SIERRA_COLORS['danger'])

            def on_close(self, close, **kwargs):
                voice_filter.log_to_terminal("🔌 Deepgram connection closed")
                voice_filter.update_status("🔌 Disconnected", SIERRA_COLORS['text_muted'])
            
            # Register event handlers
            self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Close, on_close)
            
            self.log_to_terminal("✅ Event handlers registered")
            
            # Start Deepgram connection
            self.log_to_terminal("🚀 Starting Deepgram connection...")
            start_result = self.dg_connection.start(options)
            
            if not start_result:
                self.log_to_terminal("❌ Failed to start Deepgram connection")
                return
            
            self.log_to_terminal("✅ Sierra Voice Filter started successfully!")
            self.log_to_terminal("=" * 50)
            self.log_to_terminal("🎤 SIERRA VOICE FILTER - ACTIVE")
            self.log_to_terminal("🔍 Listening for speakers...")
            self.log_to_terminal("🔒 Will lock onto first speaker with 3+ words")
            self.log_to_terminal("🗣️ Say 'exit sierra' or 'stop sierra' to stop")
            self.log_to_terminal("=" * 50)
            
            # Give the connection a moment to fully establish
            await asyncio.sleep(0.5)
            
            self.is_running = True
            
            # Audio streaming loop
            loop_count = 0
            while self.is_running:
                try:
                    # Read audio data
                    audio_data = self.audio_stream.read(1024, exception_on_overflow=False)
                    
                    # STAGE 1 PRE-FILTERING: Apply frequency analysis before sending to Deepgram
                    if loop_count % 10 == 0:  # Check every 10th frame for efficiency
                        stage1_result = self.tv_filter.stage1_frequency_analysis(audio_data)
                        if stage1_result.startswith('filtered_'):
                            self.tv_filter.filter_stats['stage1_frequency'] += 1
                            self.tv_filter.filter_stats['total_processed'] += 1
                            
                            if loop_count % 100 == 0:  # Log occasionally to avoid spam
                                reason = stage1_result.replace('filtered_', '').replace('_', ' ').title()
                                self.log_to_terminal(f"🚫 STAGE 1 PRE-FILTER: {reason}")
                            
                            # Skip sending this audio to Deepgram
                            await asyncio.sleep(0.01)
                            loop_count += 1
                            continue
                    
                    # Send to Deepgram (will go through Stages 2-5 in process_transcript)
                    if self.dg_connection:
                        self.dg_connection.send(audio_data)
                        
                        # Debug every 500 loops (roughly every 5 seconds)
                        loop_count += 1
                        if loop_count % 500 == 0:
                            self.log_to_terminal(f"🔄 Audio streaming active (loop {loop_count}) - Stage 1 pre-filtering enabled")
                        
                    # Small delay to prevent overwhelming the API
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    self.log_to_terminal(f"❌ Error in audio loop: {e}")
                    await asyncio.sleep(0.1)  # Brief pause before retrying
            
        except Exception as e:
            self.log_to_terminal(f"❌ Error starting audio stream: {e}")
            print(f"❌ Error starting audio stream: {e}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.log_to_terminal("🛑 Stopping Sierra Voice Filter...")
        self.is_running = False
        
        if self.dg_connection:
            try:
                self.dg_connection.finish()
                self.log_to_terminal("✅ Deepgram connection finished")
            except Exception as e:
                self.log_to_terminal(f"❌ Error finishing Deepgram connection: {e}")
            
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.log_to_terminal("✅ Audio stream closed")
            except Exception as e:
                self.log_to_terminal(f"❌ Error closing audio stream: {e}")
        
        self.log_to_terminal("✅ Sierra Voice Filter cleanup completed")
        self.update_status("🔴 Stopped", SIERRA_COLORS['text_muted'])
    
    def stop_filter(self):
        """Stop the voice filter"""
        self.log_to_terminal("🛑 Sierra Voice Filter termination requested...")
        self.is_running = False

# Global variable to store the filter instance
current_filter = None

def start_voice_filter():
    """Start the Sierra voice filter"""
    global current_filter
    current_filter = SierraVoiceFilter(terminal_display, status_label)
    
    # Update UI
    start_button.config(text="🛑 Stop Filter", command=stop_voice_filter, 
                       bg=SIERRA_COLORS['danger'], fg="black")
    reset_button.config(state=tk.NORMAL)
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(current_filter.start_audio_stream())
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()

def stop_voice_filter():
    """Stop the Sierra voice filter"""
    global current_filter
    if current_filter:
        current_filter.stop_filter()
        current_filter = None
    
    # Reset UI
    start_button.config(text="🎤 Start Voice Filter", command=start_voice_filter,
                       bg=SIERRA_COLORS['primary_green'], fg="black")
    reset_button.config(state=tk.DISABLED)

def reset_speaker_lock():
    """Reset the speaker lock"""
    global current_filter
    if current_filter:
        current_filter.reset_speaker_lock()
    else:
        terminal_display.insert(tk.END, "[INFO] Voice filter not running. Start filter first.\n")
        terminal_display.see(tk.END)

def clear_terminal():
    """Clear both terminal and transcription displays, reset statistics"""
    terminal_display.delete(1.0, tk.END)
    transcription_display.delete(1.0, tk.END)
    
    # Reset statistics if voice filter is running
    global current_filter
    if current_filter and current_filter.tv_filter:
        current_filter.tv_filter.filter_stats = {
            'stage1_frequency': 0,
            'stage2_confidence': 0, 
            'stage3_content': 0,
            'stage4_speaker_pattern': 0,
            'stage5_voice_lock': 0,
            'passed_all_stages': 0,
            'total_processed': 0
        }
        current_filter.filtered_count = 0
        current_filter.accepted_count = 0
        current_filter.log_to_terminal("📊 Statistics reset - starting fresh filtering metrics")
    
    # Show welcome message again
    show_welcome_message()

# Create main GUI with Authentic Sierra AI styling (whitish tan + forest green)
root = tk.Tk()
root.title("Sierra Voice Filter - Speaker Diarization Demo")
root.geometry("1200x800")
root.configure(bg=SIERRA_COLORS['background'])
root.resizable(True, True)

# Header Frame
header_frame = tk.Frame(root, bg=SIERRA_COLORS['card_bg'], height=80, relief=tk.FLAT, bd=1)
header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
header_frame.pack_propagate(False)

# Sierra branding
brand_frame = tk.Frame(header_frame, bg=SIERRA_COLORS['card_bg'])
brand_frame.pack(expand=True, fill=tk.BOTH)

# Sierra logo/title with proper forest green
sierra_title = tk.Label(brand_frame, text="SIERRA", 
                       font=("Arial", 28, "bold"), 
                       bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['primary_green'])
sierra_title.pack(pady=(15, 2))

subtitle = tk.Label(brand_frame, text="Voice Filter & Speaker Diarization", 
                   font=("Arial", 14), 
                   bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['text_secondary'])
subtitle.pack(pady=(0, 10))

# Status Frame
status_frame = tk.Frame(root, bg=SIERRA_COLORS['card_bg'], height=70, relief=tk.FLAT, bd=1)
status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
status_frame.pack_propagate(False)

status_inner = tk.Frame(status_frame, bg=SIERRA_COLORS['card_bg'])
status_inner.pack(expand=True, fill=tk.BOTH)

# Status indicator
status_indicator = tk.Label(status_inner, text="⚫", font=("Arial", 18), 
                           bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['text_muted'])
status_indicator.pack(side=tk.LEFT, padx=20, pady=20)

status_label = tk.Label(status_inner, text="🔴 Ready to Start", 
                       font=("Arial", 14, "bold"), 
                       bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['text_primary'])
status_label.pack(side=tk.LEFT, pady=20)

# Speaker lock status (right side)
speaker_lock_label = tk.Label(status_inner, text="🔓 No Speaker Lock", 
                             font=("Arial", 12), 
                             bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['text_muted'])
speaker_lock_label.pack(side=tk.RIGHT, padx=20, pady=20)

# Control Panel
control_frame = tk.Frame(root, bg=SIERRA_COLORS['card_bg'], relief=tk.FLAT, bd=1)
control_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

control_inner = tk.Frame(control_frame, bg=SIERRA_COLORS['card_bg'])
control_inner.pack(fill=tk.X, padx=30, pady=20)

# Main control button with Sierra green
start_button = tk.Button(control_inner, text="🎤 Start Voice Filter", 
                        command=start_voice_filter,
                        font=("Arial", 16, "bold"), 
                        bg=SIERRA_COLORS['primary_green'], fg="black",
                        relief=tk.FLAT, bd=0,
                        padx=40, pady=15,
                        cursor="hand2")
start_button.pack(pady=(0, 15))

# Secondary controls
secondary_frame = tk.Frame(control_inner, bg=SIERRA_COLORS['card_bg'])
secondary_frame.pack()

reset_button = tk.Button(secondary_frame, text="🔄 Reset Speaker Lock", 
                        command=reset_speaker_lock,
                        font=("Arial", 12), 
                        bg=SIERRA_COLORS['secondary_green'], fg="black",
                        relief=tk.FLAT, bd=0,
                        padx=20, pady=10,
                        cursor="hand2",
                        state=tk.DISABLED)
reset_button.pack(side=tk.LEFT, padx=10)

clear_button = tk.Button(secondary_frame, text="🗑️ Clear Displays", 
                        command=clear_terminal,
                        font=("Arial", 12), 
                        bg=SIERRA_COLORS['secondary_green'], fg="black",
                        relief=tk.FLAT, bd=0,
                        padx=20, pady=10,
                        cursor="hand2")
clear_button.pack(side=tk.LEFT, padx=10)

# MAIN CONTENT AREA - 50/50 SPLIT
main_content_frame = tk.Frame(root, bg=SIERRA_COLORS['background'])
main_content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

# LEFT SIDE - TRANSCRIPTION (50%)
transcription_frame = tk.Frame(main_content_frame, bg=SIERRA_COLORS['card_bg'], relief=tk.FLAT, bd=1)
transcription_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

# Transcription header
trans_header = tk.Frame(transcription_frame, bg=SIERRA_COLORS['card_bg'])
trans_header.pack(fill=tk.X, padx=20, pady=(15, 0))

trans_title = tk.Label(trans_header, text="📝 Live Transcription", 
                      font=("Arial", 14, "bold"), 
                      bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['primary_green'])
trans_title.pack(side=tk.LEFT)

trans_subtitle = tk.Label(trans_header, text="Accepted speech from locked speaker", 
                         font=("Arial", 10), 
                         bg=SIERRA_COLORS['card_bg'], fg=SIERRA_COLORS['text_secondary'])
trans_subtitle.pack(side=tk.RIGHT)

# Transcription text area
trans_text_frame = tk.Frame(transcription_frame, bg=SIERRA_COLORS['card_bg'])
trans_text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

transcription_display = tk.Text(trans_text_frame, 
                               wrap=tk.WORD, 
                               font=("Arial", 12), 
                               bg=SIERRA_COLORS['background'], 
                               fg=SIERRA_COLORS['text_primary'],
                               insertbackground=SIERRA_COLORS['primary_green'],
                               selectbackground=SIERRA_COLORS['accent_green'],
                               relief=tk.FLAT, bd=2,
                               padx=15, pady=15)
transcription_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Transcription scrollbar
trans_scrollbar = tk.Scrollbar(trans_text_frame, orient=tk.VERTICAL, 
                              command=transcription_display.yview,
                              bg=SIERRA_COLORS['border'], 
                              troughcolor=SIERRA_COLORS['background'], 
                              activebackground=SIERRA_COLORS['accent_green'])
transcription_display.configure(yscrollcommand=trans_scrollbar.set)
trans_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# RIGHT SIDE - TERMINAL (50%)
terminal_frame = tk.Frame(main_content_frame, bg=SIERRA_COLORS['terminal_bg'], relief=tk.FLAT, bd=1)
terminal_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

# Terminal header
terminal_header = tk.Frame(terminal_frame, bg=SIERRA_COLORS['terminal_bg'])
terminal_header.pack(fill=tk.X, padx=20, pady=(15, 0))

terminal_title = tk.Label(terminal_header, text="🖥️ Voice Filter Terminal", 
                         font=("Arial", 14, "bold"), 
                         bg=SIERRA_COLORS['terminal_bg'], fg=SIERRA_COLORS['terminal_text'])
terminal_title.pack(side=tk.LEFT)

terminal_subtitle = tk.Label(terminal_header, text="Real-time filtering activity", 
                            font=("Arial", 10), 
                            bg=SIERRA_COLORS['terminal_bg'], fg=SIERRA_COLORS['text_muted'])
terminal_subtitle.pack(side=tk.RIGHT)

# Terminal text area
terminal_text_frame = tk.Frame(terminal_frame, bg=SIERRA_COLORS['terminal_bg'])
terminal_text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

terminal_display = tk.Text(terminal_text_frame, 
                          wrap=tk.WORD, 
                          font=("Consolas", 10), 
                          bg=SIERRA_COLORS['terminal_bg'], 
                          fg=SIERRA_COLORS['terminal_text'],
                          insertbackground=SIERRA_COLORS['terminal_text'],
                          selectbackground=SIERRA_COLORS['accent_green'],
                          relief=tk.FLAT, bd=0,
                          padx=15, pady=15)
terminal_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Terminal scrollbar
terminal_scrollbar = tk.Scrollbar(terminal_text_frame, orient=tk.VERTICAL, 
                                 command=terminal_display.yview,
                                 bg=SIERRA_COLORS['terminal_bg'], 
                                 troughcolor=SIERRA_COLORS['terminal_bg'], 
                                 activebackground=SIERRA_COLORS['accent_green'])
terminal_display.configure(yscrollcommand=terminal_scrollbar.set)
terminal_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Footer
footer_frame = tk.Frame(root, bg=SIERRA_COLORS['secondary_bg'], height=50, relief=tk.FLAT, bd=1)
footer_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
footer_frame.pack_propagate(False)

footer_inner = tk.Frame(footer_frame, bg=SIERRA_COLORS['secondary_bg'])
footer_inner.pack(expand=True, fill=tk.BOTH)

# Instructions with Sierra styling - Updated for 5-stage system
instructions = tk.Label(footer_inner, text="🎯 Advanced TV noise filtering active | 📊 Say 'show statistics' for metrics | 🗣️ Say 'exit sierra' to stop", 
                       font=("Arial", 11), 
                       bg=SIERRA_COLORS['secondary_bg'], fg=SIERRA_COLORS['text_primary'])
instructions.pack(pady=15)

# Add welcome message
def show_welcome_message():
    """Show welcome message in both displays"""
    # Terminal welcome - Updated for 5-stage system
    terminal_display.insert(tk.END, "=" * 55 + "\n")
    terminal_display.insert(tk.END, "🎯 SIERRA 5-STAGE TV NOISE FILTER\n")
    terminal_display.insert(tk.END, "=" * 55 + "\n")
    terminal_display.insert(tk.END, "🎵 Stage 1: Frequency Analysis (Pre-filter)\n")
    terminal_display.insert(tk.END, "🎯 Stage 2: Deepgram Confidence Scoring\n")
    terminal_display.insert(tk.END, "📝 Stage 3: TV Content Pattern Detection\n")
    terminal_display.insert(tk.END, "👥 Stage 4: Speaker Diarization Analysis\n")
    terminal_display.insert(tk.END, "🔒 Stage 5: Intelligent Voice Locking\n")
    terminal_display.insert(tk.END, "=" * 55 + "\n")
    terminal_display.insert(tk.END, "🚫 Filters: TV music, commercials, dialogue\n")
    terminal_display.insert(tk.END, "📊 Say 'show statistics' for live metrics\n")
    terminal_display.insert(tk.END, "🗣️ Say 'exit sierra' to stop\n")
    terminal_display.insert(tk.END, "=" * 55 + "\n\n")
    terminal_display.insert(tk.END, "Ready for revolutionary TV noise filtering...\n\n")
    terminal_display.see(tk.END)
    
    # Transcription welcome - Updated messaging
    transcription_display.insert(tk.END, "=" * 45 + "\n")
    transcription_display.insert(tk.END, "📝 SIERRA FILTERED TRANSCRIPTION\n")
    transcription_display.insert(tk.END, "=" * 45 + "\n")
    transcription_display.insert(tk.END, "This panel shows ONLY speech that passes all 5 filtering stages.\n\n")
    transcription_display.insert(tk.END, "🎯 Revolutionary TV noise filtering:\n")
    transcription_display.insert(tk.END, "  • Stage 1-4: Filter TV audio, commercials, dialogue\n") 
    transcription_display.insert(tk.END, "  • Stage 5: Lock onto YOUR voice only\n")
    transcription_display.insert(tk.END, "🔊 Background TV will be filtered out automatically\n")
    transcription_display.insert(tk.END, "📊 Watch terminal for detailed filtering activity\n")
    transcription_display.insert(tk.END, "=" * 45 + "\n\n")
    transcription_display.insert(tk.END, "Click 'Start Voice Filter' to begin...\n\n")
    transcription_display.see(tk.END)

# Show welcome message on startup
root.after(100, show_welcome_message)

# Button hover effects
def on_enter(event):
    """Button hover effect with Sierra colors"""
    if event.widget.cget('state') != 'disabled':
        current_bg = event.widget.cget('bg')
        if current_bg == SIERRA_COLORS['primary_green']:
            event.widget.config(bg=SIERRA_COLORS['accent_green'])
        elif current_bg == SIERRA_COLORS['secondary_green']:
            event.widget.config(bg=SIERRA_COLORS['accent_green'])
        elif current_bg == SIERRA_COLORS['danger']:
            event.widget.config(bg='#E04444')

def on_leave(event):
    """Button hover effect with Sierra colors"""
    if event.widget.cget('state') != 'disabled':
        # Restore original color based on button
        if event.widget == start_button:
            if "Stop" in start_button.cget('text'):
                event.widget.config(bg=SIERRA_COLORS['danger'])
            else:
                event.widget.config(bg=SIERRA_COLORS['primary_green'])
        else:
            event.widget.config(bg=SIERRA_COLORS['secondary_green'])

# Bind hover effects
for button in [start_button, reset_button, clear_button]:
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# Start the GUI
if __name__ == "__main__":
    root.mainloop() 