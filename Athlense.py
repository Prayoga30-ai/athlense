import cv2
import numpy as np
import math
import pyttsx3
import time
import subprocess
import os
import socket
from flask import Flask, Response
import threading

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("⚠️  Picamera2 tidak tersedia, menggunakan mode simulasi")

class TrackDetector:
    def __init__(self):
        self.previous_turn_angle = 0
        self.smoothing_factor = 0.7
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Variabel untuk streaming
        self.current_frame = None
        self.current_mask = None
        self.current_direction = "TIDAK ADA LINTASAN"
        self.current_angle = 0
        self.streaming_active = False
        self.running = True
        
        # Inisialisasi kamera
        self.picam2 = None
        self.camera_available = False
        self.configure_camera()
    
    def cleanup_camera_processes(self):
        """Bersihkan proses yang menggunakan kamera"""
        try:
            subprocess.run(['sudo', 'pkill', '-f', 'libcamera'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'pkill', '-f', 'rpicam'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            print("✅ Camera processes cleaned up")
            return True
        except Exception as e:
            print(f"⚠️  Warning cleaning camera: {e}")
            return False
    
    def configure_camera(self):
        """Konfigurasi Raspberry Pi Camera dengan error handling"""
        if not PICAMERA_AVAILABLE:
            print("⚠️  Picamera2 tidak tersedia, menggunakan mode simulasi")
            return
        
        try:
            # Bersihkan proses kamera terlebih dahulu
            self.cleanup_camera_processes()
            
            self.picam2 = Picamera2()
            
            # Konfigurasi preview camera
            preview_config = self.picam2.create_preview_configuration(
                main={"size": (640, 480)},
                controls={"FrameRate": 30}
            )
            self.picam2.configure(preview_config)
            
            # Set controls untuk fokus dan exposure
            self.picam2.set_controls({
                "AfMode": controls.AfModeEnum.Continuous,
                "AfSpeed": controls.AfSpeedEnum.Fast,
                "ExposureTime": 10000,
                "AnalogueGain": 1.0
            })
            
            self.picam2.start()
            self.camera_available = True
            print("✅ Camera Raspberry Pi siap!")
            time.sleep(2)  # Warm-up camera
            
        except Exception as e:
            print(f"❌ Error konfigurasi camera: {e}")
            print("⚠️  Menggunakan mode simulasi tanpa kamera")
            self.camera_available = False
    
    def get_frame(self):
        """Ambil frame dari camera atau generate frame simulasi"""
        if not self.camera_available or self.picam2 is None:
            # Generate frame simulasi jika kamera tidak tersedia
            return self.generate_test_frame()
        
        try:
            # Capture frame dari camera
            frame = self.picam2.capture_array()
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Convert BGR ke RGB (karena OpenCV menggunakan BGR)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame
        except Exception as e:
            print(f"❌ Error mengambil frame: {e}")
            return self.generate_test_frame()
    
    def generate_test_frame(self):
        """Generate frame simulasi untuk testing"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "MODE SIMULASI", (150, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Kamera tidak tersedia", (120, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame

    def setup_tts(self):
        """Setup text-to-speech engine"""
        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'indonesia' in voice.name.lower() or 'id' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
        except Exception as e:
            print(f"❌ Error setup TTS: {e}")
    
    def speak(self, text):
        """Fungsi untuk berbicara dengan text-to-speech"""
        try:
            print(f"🔊: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Error TTS: {e}")
    
    def calculate_turn_angle(self, steering_angle, track_detected):
        """Menghitung sudut belok berdasarkan steering angle"""
        if not track_detected:
            return self.previous_turn_angle * 0.5
        
        normalized_angle = max(min(steering_angle, 45), -45)
        turn_angle = normalized_angle * 0.67
        
        smoothed_angle = (self.smoothing_factor * turn_angle + 
                         (1 - self.smoothing_factor) * self.previous_turn_angle)
        
        self.previous_turn_angle = smoothed_angle
        return smoothed_angle
    
    def get_turn_direction_id(self, turn_angle):
        """Mendapatkan arah belok dalam Bahasa Indonesia"""
        if abs(turn_angle) < 3:
            return "JALAN LURUS"
        elif turn_angle > 0:
            return f"BELOK KANAN {abs(turn_angle):.1f} DERAJAT"
        else:
            return f"BELOK KIRI {abs(turn_angle):.1f} DERAJAT"
    
    def detect_track(self, frame):
        """Mendeteksi lintasan dari frame camera"""
        if frame is None:
            return None, 0, False, "FRAME ERROR", None
        
        frame = cv2.resize(frame, (640, 480))
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        
        # Konversi ke HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Deteksi warna merah (lintasan atletik)
        lower_red1 = np.array([0, 80, 80])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([160, 80, 80])
        upper_red2 = np.array([180, 255, 255])
        
        # Deteksi warna coklat (aspal/tanah)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 200, 200])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # Gabungkan mask
        mask = cv2.bitwise_or(mask_red1, mask_red2)
        mask = cv2.bitwise_or(mask, mask_brown)
        
        # Operasi morfologi
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Region of Interest (fokus pada bagian bawah gambar)
        roi_mask = np.zeros_like(mask)
        height, width = mask.shape
        roi_points = np.array([[
            (0, height),
            (width, height),
            (width, int(height * 0.6)),
            (0, int(height * 0.6))
        ]])
        cv2.fillPoly(roi_mask, roi_points, 255)
        mask = cv2.bitwise_and(mask, roi_mask)
        
        # Temukan kontur
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        result = frame.copy()
        steering_angle = 0
        turn_angle = 0
        track_detected = False
        direction_id = "TIDAK ADA LINTASAN"
        
        if contours:
            min_area = 500
            valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            if valid_contours:
                largest_contour = max(valid_contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                track_center_x = x + w // 2
                track_center_y = y + h // 2
                
                frame_center_x = frame_width // 2
                steering_angle = ((track_center_x - frame_center_x) / frame_center_x) * 45
                turn_angle = self.calculate_turn_angle(steering_angle, True)
                
                track_detected = True
                direction_id = self.get_turn_direction_id(turn_angle)
                
                # Gambar visualisasi
                cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.drawContours(result, [largest_contour], -1, (255, 0, 0), 2)
                cv2.circle(result, (track_center_x, track_center_y), 8, (0, 0, 255), -1)
                cv2.circle(result, (frame_center_x, frame_height//2), 8, (255, 255, 0), -1)
                
                # Gambar panah arah
                arrow_length = 80
                arrow_x = int(frame_center_x + arrow_length * math.sin(math.radians(turn_angle)))
                arrow_y = int(frame_height//2 - arrow_length * math.cos(math.radians(turn_angle)))
                cv2.arrowedLine(result, (frame_center_x, frame_height//2), 
                               (arrow_x, arrow_y), (0, 255, 255), 3, tipLength=0.3)
        
        if not track_detected:
            turn_angle = self.calculate_turn_angle(0, False)
            direction_id = self.get_turn_direction_id(turn_angle)
        
        # Tampilkan informasi pada gambar
        info_lines = [
            f"Sudut: {turn_angle:6.1f}°",
            f"Arah: {direction_id}",
            f"Status: {'DETECTED' if track_detected else 'NOT FOUND'}",
            f"Frame: {frame_width}x{frame_height}"
        ]
        
        for i, line in enumerate(info_lines):
            color = (0, 255, 0) if track_detected else (0, 0, 255)
            if "BELOK" in line:
                color = (0, 165, 255)
            
            cv2.putText(result, line, (10, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Gambar garis bantu
        cv2.line(result, (frame_width//2, 0), (frame_width//2, frame_height), (255, 255, 255), 1)
        cv2.line(result, (0, int(frame_height * 0.6)), (frame_width, int(frame_height * 0.6)), (255, 0, 0), 1)
        
        # Simpan frame untuk streaming
        self.current_frame = result
        self.current_mask = mask
        self.current_direction = direction_id
        self.current_angle = turn_angle
        
        return result, turn_angle, track_detected, direction_id, mask

    def start_streaming(self, host='0.0.0.0', port=5000):
        """Memulai streaming server Flask"""
        self.streaming_active = True
        
        app = Flask(__name__)
        
        def generate_frames():
            while self.streaming_active and self.running:
                if self.current_frame is not None:
                    try:
                        ret, buffer = cv2.imencode('.jpg', self.current_frame)
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    except:
                        pass
                time.sleep(0.1)
        
        def generate_mask():
            while self.streaming_active and self.running:
                if self.current_mask is not None:
                    try:
                        mask_colored = cv2.cvtColor(self.current_mask, cv2.COLOR_GRAY2BGR)
                        ret, buffer = cv2.imencode('.jpg', mask_colored)
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    except:
                        pass
                time.sleep(0.1)
        
        @app.route('/')
        def index():
            return f"""
            <html>
            <head><title>Track Detection Streaming</title></head>
            <body>
                <h1>Track Detection Streaming</h1>
                <div>
                    <h2>Status: {self.current_direction}</h2>
                    <p>Sudut: {self.current_angle:.1f}°</p>
                </div>
                <div>
                    <h3>Camera View</h3>
                    <img src="/video_feed" width="640" height="480">
                </div>
                <div>
                    <h3>Mask Detection</h3>
                    <img src="/mask_feed" width="640" height="480">
                </div>
            </body>
            </html>
            """
        
        @app.route('/video_feed')
        def video_feed():
            return Response(generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @app.route('/mask_feed')
        def mask_feed():
            return Response(generate_mask(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @app.route('/status')
        def status():
            return {
                "direction": self.current_direction,
                "angle": float(self.current_angle),
                "timestamp": time.time()
            }
        
        print(f"🌐 Streaming server mulai di http://{host}:{port}")
        
        # Jalankan Flask server di thread terpisah
        flask_thread = threading.Thread(
            target=app.run,
            kwargs={'host': host, 'port': port, 'debug': False, 'threaded': True, 'use_reloader': False}
        )
        flask_thread.daemon = True
        flask_thread.start()
        
        return app

    def stop(self):
        """Hentikan semua proses"""
        self.running = False
        self.streaming_active = False
        time.sleep(1)

    def cleanup(self):
        """Bersihkan resources"""
        self.stop()
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except:
                pass
        cv2.destroyAllWindows()
        print("✅ Camera dan resources dibersihkan")

def get_local_ip():
    """Mendapatkan alamat IP lokal Raspberry Pi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    """Program utama dengan kontrol tanpa keyboard interrupt"""
    print("=" * 60)
    print("SISTEM DETEKSI LINTASAN - RASPBERRY PI CAMERA")
    print("=" * 60)
    print("Program akan berjalan secara otomatis")
    print("Streaming akan aktif di port 5000")
    print("=" * 60)
    
    # Bersihkan proses kamera
    try:
        subprocess.run(['sudo', 'pkill', '-f', 'libcamera'], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', 'pkill', '-f', 'rpicam'], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass
    
    # Buat detector
    detector = TrackDetector()
    last_speech_time = 0
    speech_cooldown = 3
    local_ip = get_local_ip()
    
    # Mulai streaming otomatis
    try:
        detector.start_streaming()
        print(f"🌐 Streaming aktif di http://{local_ip}:5000")
        streaming_enabled = True
    except Exception as e:
        print(f"❌ Gagal memulai streaming: {e}")
        streaming_enabled = False
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while detector.running:
            # Ambil frame dari camera
            frame = detector.get_frame()
            if frame is None:
                print("❌ Gagal mengambil frame")
                time.sleep(1)
                continue
            
            # Deteksi lintasan
            result, turn_angle, detected, direction, mask = detector.detect_track(frame)
            
            if result is not None:
                # Hitung FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    fps = frame_count / (time.time() - start_time)
                    print(f"📊 FPS: {fps:.1f}")
                    frame_count = 0
                    start_time = time.time()
                
                # Tampilkan info di console setiap 10 frame
                if frame_count % 10 == 0:
                    print(f"Sudut: {turn_angle:6.1f}° | Arah: {direction} | Detected: {detected}")
                
                # Auto-speak setiap 10 detik jika terdeteksi
                current_time = time.time()
                if detected and (current_time - last_speech_time) > 10:
                    detector.speak(direction)
                    last_speech_time = current_time
            
            # Delay untuk mengurangi CPU usage
            time.sleep(0.05)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        detector.cleanup()
        print("🎉 Program selesai")

if __name__ == "__main__":
    main()
