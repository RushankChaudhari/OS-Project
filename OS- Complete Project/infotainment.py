from vehicle_control import Task, VehicleControlSystem
import pygame
import os
from typing import List, Optional, Dict, Any
import time
from dataclasses import dataclass
import json

@dataclass
class TrackInfo:
    """Information about a media track"""
    path: str
    title: str
    artist: str
    duration: float
    format: str

class InfotainmentSystem:
    def __init__(self, control_system: VehicleControlSystem):
        self.control_system = control_system
        self.is_playing = False
        self.current_track = 0
        self.tracks: List[TrackInfo] = []
        self.playlist: List[int] = []  # Indices of tracks in current playlist
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        self.repeat_mode = "none"  # none, one, all
        self.shuffle = False
        self.last_play_time = 0
        self.play_cooldown = 0.5  # Prevent too frequent track changes
        self.pygame_initialized = False
        
        # Initialize pygame mixer with error handling
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.music.set_volume(self.volume)
            self.pygame_initialized = True
            self.control_system.logger.log("Audio system initialized successfully", "info")
        except Exception as e:
            self.control_system.logger.log(
                f"Failed to initialize audio system: {str(e)}", "error")
            
    def cleanup(self):
        """Clean up pygame resources"""
        if self.pygame_initialized:
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.quit()
                self.pygame_initialized = False
                self.control_system.logger.log("Audio system cleaned up successfully", "info")
            except Exception as e:
                self.control_system.logger.log(f"Error cleaning up audio system: {str(e)}", "error")
            
    def load_audio_files(self, directory: str) -> bool:
        """Load audio files with improved error handling and metadata extraction"""
        try:
            self.tracks.clear()
            self.playlist.clear()
            
            for file in os.listdir(directory):
                if file.lower().endswith(('.mp3', '.wav')):
                    file_path = os.path.join(directory, file)
                    try:
                        # Get basic file info
                        file_size = os.path.getsize(file_path)
                        if file_size == 0:
                            continue
                            
                        # Create track info
                        track = TrackInfo(
                            path=file_path,
                            title=os.path.splitext(file)[0],
                            artist="Unknown",
                            duration=0.0,
                            format=os.path.splitext(file)[1][1:].lower()
                        )
                        
                        # Try to load the file to verify it's valid
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.unload()
                        
                        self.tracks.append(track)
                        self.playlist.append(len(self.tracks) - 1)
                        
                    except Exception as e:
                        self.control_system.logger.log(
                            f"Error loading file {file}: {str(e)}", "warning")
                        continue
                        
            if self.tracks:
                self._update_playlist()
                return True
            return False
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error loading audio directory: {str(e)}", "error")
            return False
            
    def play_media(self) -> bool:
        """Play media with improved error handling"""
        if not self.tracks:
            self.control_system.logger.log("No tracks available", "warning")
            return False
            
        current_time = time.time()
        if current_time - self.last_play_time < self.play_cooldown:
            return False
            
        try:
            track = self.tracks[self.playlist[self.current_track]]
            pygame.mixer.music.load(track.path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.last_play_time = current_time
            
            def media_action():
                self.control_system.logger.log(
                    f"Playing: {track.title}", "info")
                    
            task = Task("Media Playback", 3, media_action)
            self.control_system.add_task(task)
            return True
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error playing media: {str(e)}", "error")
            # Try to reinitialize the mixer
            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                pygame.mixer.music.set_volume(self.volume)
            except Exception as e:
                self.control_system.logger.log(
                    f"Failed to reinitialize audio system: {str(e)}", "error")
            return False
        
    def pause_media(self) -> bool:
        """Pause media with error handling"""
        if not self.is_playing:
            return False
            
        try:
            pygame.mixer.music.pause()
            self.is_playing = False
            
            def pause_action():
                self.control_system.logger.log("Media paused", "info")
                
            task = Task("Media Pause", 3, pause_action)
            self.control_system.add_task(task)
            return True
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error pausing media: {str(e)}", "error")
            return False
        
    def next_track(self) -> bool:
        """Play next track with improved playlist management"""
        if not self.tracks:
            return False
            
        try:
            # Update current track index
            if self.repeat_mode == "one":
                # Stay on current track
                pass
            else:
                self.current_track = (self.current_track + 1) % len(self.playlist)
                
            # Load and play the track
            track = self.tracks[self.playlist[self.current_track]]
            pygame.mixer.music.load(track.path)
            if self.is_playing:
                pygame.mixer.music.play()
                
            def next_action():
                self.control_system.logger.log(
                    f"Switched to: {track.title}", "info")
                    
            task = Task("Next Track", 3, next_action)
            self.control_system.add_task(task)
            return True
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error switching tracks: {str(e)}", "error")
            return False
            
    def previous_track(self) -> bool:
        """Play previous track"""
        if not self.tracks:
            return False
            
        try:
            # Update current track index
            if self.repeat_mode == "one":
                # Stay on current track
                pass
            else:
                self.current_track = (self.current_track - 1) % len(self.playlist)
                
            # Load and play the track
            track = self.tracks[self.playlist[self.current_track]]
            pygame.mixer.music.load(track.path)
            if self.is_playing:
                pygame.mixer.music.play()
                
            def prev_action():
                self.control_system.logger.log(
                    f"Switched to: {track.title}", "info")
                    
            task = Task("Previous Track", 3, prev_action)
            self.control_system.add_task(task)
            return True
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error switching tracks: {str(e)}", "error")
            return False
            
    def set_volume(self, volume: float) -> bool:
        """Set volume with validation"""
        try:
            if 0.0 <= volume <= 1.0:
                self.volume = volume
                pygame.mixer.music.set_volume(volume)
                return True
            return False
        except Exception as e:
            self.control_system.logger.log(
                f"Error setting volume: {str(e)}", "error")
            return False
            
    def toggle_repeat(self) -> str:
        """Toggle repeat mode"""
        modes = ["none", "one", "all"]
        current_index = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_index + 1) % len(modes)]
        return self.repeat_mode
        
    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode"""
        self.shuffle = not self.shuffle
        if self.shuffle:
            self._update_playlist()
        return self.shuffle
        
    def _update_playlist(self):
        """Update playlist based on current settings"""
        if self.shuffle:
            import random
            self.playlist = list(range(len(self.tracks)))
            random.shuffle(self.playlist)
        else:
            self.playlist = list(range(len(self.tracks)))
            
    def get_current_track_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current track"""
        if not self.tracks or not self.playlist:
            return None
            
        try:
            track = self.tracks[self.playlist[self.current_track]]
            return {
                "title": track.title,
                "artist": track.artist,
                "format": track.format,
                "duration": track.duration,
                "is_playing": self.is_playing,
                "volume": self.volume,
                "repeat_mode": self.repeat_mode,
                "shuffle": self.shuffle
            }
        except Exception as e:
            self.control_system.logger.log(
                f"Error getting track info: {str(e)}", "error")
            return None
            
    def save_playlist(self, filename: str) -> bool:
        """Save current playlist to file"""
        try:
            playlist_data = {
                "tracks": [track.path for track in self.tracks],
                "current_track": self.current_track,
                "playlist": self.playlist,
                "repeat_mode": self.repeat_mode,
                "shuffle": self.shuffle,
                "volume": self.volume
            }
            
            with open(filename, 'w') as f:
                json.dump(playlist_data, f)
            return True
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error saving playlist: {str(e)}", "error")
            return False
            
    def load_playlist(self, filename: str) -> bool:
        """Load playlist from file"""
        try:
            with open(filename, 'r') as f:
                playlist_data = json.load(f)
                
            # Verify all tracks still exist
            valid_tracks = []
            for path in playlist_data["tracks"]:
                if os.path.exists(path):
                    valid_tracks.append(path)
                    
            if not valid_tracks:
                return False
                
            # Load the tracks
            if self.load_audio_files(os.path.dirname(valid_tracks[0])):
                self.current_track = min(
                    playlist_data["current_track"],
                    len(self.tracks) - 1
                )
                self.repeat_mode = playlist_data["repeat_mode"]
                self.shuffle = playlist_data["shuffle"]
                self.volume = playlist_data["volume"]
                return True
                
            return False
            
        except Exception as e:
            self.control_system.logger.log(
                f"Error loading playlist: {str(e)}", "error")
            return False

    def navigation_update(self):
        def nav_action():
            print("Infotainment: Updating navigation")
        task = Task("Navigation Update", 2, nav_action)
        self.control_system.add_task(task) 