import tkinter as tk
import customtkinter as ctk
import cv2
import os
import pickle
import face_recognition
import threading
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime
import time
from scipy.spatial import distance as dist

# --- CẤU HÌNH GIAO DIỆN HIỆN ĐẠI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # Theme màu tối chuyên nghiệp

# Định nghĩa các màu sắc chủ đạo (Palette An Ninh)
COLOR_BG = "#1a1a1a"        # Nền chính siêu tối
COLOR_SIDEBAR = "#2b2b2b"   # Nền sidebar
COLOR_ACCENT = "#3498db"    # Màu xanh chủ đạo (Cyan/Blue)
COLOR_SUCCESS = "#2ecc71"   # Màu thành công (Green)
COLOR_WARNING = "#f39c12"   # Màu cảnh báo (Orange)
COLOR_DANGER = "#e74c3c"    # Màu nguy hiểm (Red)
COLOR_TEXT = "#ecf0f1"      # Màu chữ trắng sáng

class SecurityApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH HỆ THỐNG ---
        self.ADMIN_PASSWORD = "admin"
        self.DOOR_OPEN_DURATION = 5.0
        
        # Cấu hình Nháy mắt (Liveness)
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 2
        self.COUNTER = 0
        self.TOTAL_BLINKS = 0
        self.REQUIRED_BLINKS = 1
        
        # Cài đặt cửa sổ chính
        self.title("SMART SECURITY SYSTEM v2.0")
        self.geometry("1280x800")
        self.minsize(1024, 768)
        
        # Biến hệ thống
        self.capture = cv2.VideoCapture(0)
        self.known_face_encodings = []
        self.known_face_names = []
        self.process_this_frame = True
        self.is_training = False
        self.face_locations = []
        self.face_names = []
        
        # Biến trạng thái
        self.last_unlock_time = 0
        self.is_door_open = False
        self.waiting_for_blink = False
        self.current_candidate = None
        
        # Đường dẫn
        self.db_dir = "data/images"
        self.log_dir = "logs"
        self.encoding_file = "data/encodings.pickle"
        
        if not os.path.exists(self.db_dir): os.makedirs(self.db_dir)
        if not os.path.exists(self.log_dir): os.makedirs(self.log_dir)

        self.load_data()

        # --- THIẾT KẾ LAYOUT (GRID) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR (BÊN TRÁI)
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Spacer

        # Logo & Header
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🛡️ SECURITY AI", font=ctk.CTkFont(size=26, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 20))

        # Panel Trạng thái Cửa (Card design)
        self.status_card = ctk.CTkFrame(self.sidebar_frame, fg_color=COLOR_BG, corner_radius=15)
        self.status_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_door_icon = ctk.CTkLabel(self.status_card, text="🔒", font=ctk.CTkFont(size=40))
        self.lbl_door_icon.pack(pady=(15, 0))
        
        self.lbl_door_status = ctk.CTkLabel(self.status_card, text="ĐANG KHÓA", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT)
        self.lbl_door_status.pack(pady=(5, 15))

        # Đồng hồ
        self.lbl_clock = ctk.CTkLabel(self.sidebar_frame, text="00:00:00", font=ctk.CTkFont(family="Consolas", size=24))
        self.lbl_clock.grid(row=2, column=0, pady=20)
        self.update_clock()

        # Separator
        ctk.CTkLabel(self.sidebar_frame, text="QUẢN TRỊ HỆ THỐNG", text_color="gray", font=ctk.CTkFont(size=12)).grid(row=3, column=0, sticky="w", padx=25, pady=(20,5))

        # Các nút chức năng (Styled Buttons)
        self.btn_register = ctk.CTkButton(self.sidebar_frame, text="  👤  Thêm Cư Dân  ", height=45, fg_color=COLOR_ACCENT, hover_color="#2980b9", font=ctk.CTkFont(weight="bold"), anchor="w", command=self.register_new_user)
        self.btn_register.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_train = ctk.CTkButton(self.sidebar_frame, text="  🔄  Huấn Luyện AI ", height=45, fg_color="#34495e", hover_color="#2c3e50", font=ctk.CTkFont(weight="bold"), anchor="w", command=self.start_training_thread)
        self.btn_train.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Progress Bar & Info
        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame, progress_color=COLOR_SUCCESS)
        self.progress_bar.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.info_label = ctk.CTkLabel(self.sidebar_frame, text="System Ready", text_color="gray")
        self.info_label.grid(row=7, column=0, padx=20)

        # Footer
        ctk.CTkLabel(self.sidebar_frame, text="© 2024 Project CV", font=ctk.CTkFont(size=10)).grid(row=9, column=0, pady=10)


        # 2. MAIN CONTENT (BÊN PHẢI)
        self.main_frame = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header Title
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="ew")
        ctk.CTkLabel(self.header_frame, text="CAMERA GIÁM SÁT", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        self.lbl_fps = ctk.CTkLabel(self.header_frame, text="FPS: 0", text_color="gray")
        self.lbl_fps.pack(side="right")

        # CAMERA FEED CONTAINER (Viền đẹp)
        self.cam_container = ctk.CTkFrame(self.main_frame, fg_color="#000000", corner_radius=15, border_width=2, border_color="#404040")
        self.cam_container.grid(row=1, column=0, padx=30, pady=10, sticky="nsew")
        
        self.camera_label = ctk.CTkLabel(self.cam_container, text="")
        self.camera_label.place(relx=0.5, rely=0.5, anchor="center")

        # THÔNG BÁO TRẠNG THÁI (LỚN)
        self.notification_frame = ctk.CTkFrame(self.main_frame, height=60, fg_color=COLOR_SIDEBAR)
        self.notification_frame.grid(row=2, column=0, padx=30, pady=10, sticky="ew")
        
        self.lbl_main_status = ctk.CTkLabel(self.notification_frame, text="ĐANG GIÁM SÁT...", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_main_status.place(relx=0.5, rely=0.5, anchor="center")
        
        self.lbl_guide = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(size=16), text_color=COLOR_WARNING)
        self.lbl_guide.grid(row=3, column=0, pady=(0, 10))

        # LOG HOẠT ĐỘNG (SCROLL)
        self.log_frame = ctk.CTkScrollableFrame(self.main_frame, height=150, label_text="NHẬT KÝ HOẠT ĐỘNG", label_font=ctk.CTkFont(weight="bold"))
        self.log_frame.grid(row=4, column=0, padx=30, pady=(10, 30), sticky="ew")

        # Bắt đầu luồng camera
        self.update_camera()

    # --- ĐỒNG HỒ ---
    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_clock.configure(text=now)
        self.after(1000, self.update_clock)

    # --- NHẬT KÝ ---
    def add_log_entry(self, text, type="info"):
        color = "white"
        if type == "success": color = COLOR_SUCCESS
        elif type == "danger": color = COLOR_DANGER
        
        time_str = datetime.now().strftime("[%H:%M:%S]")
        lbl = ctk.CTkLabel(self.log_frame, text=f"{time_str} {text}", text_color=color, anchor="w")
        lbl.pack(fill="x", padx=5, pady=2)

    # --- LOGIC TÍNH TOÁN MẮT (EAR) ---
    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    # --- ĐIỀU KHIỂN CỬA ---
    def grant_access(self, name):
        self.is_door_open = True
        self.last_unlock_time = time.time()
        
        # Giao diện MỞ CỬA
        self.status_card.configure(fg_color=COLOR_SUCCESS)
        self.lbl_door_icon.configure(text="🔓")
        self.lbl_door_status.configure(text="CỬA MỞ")
        self.cam_container.configure(border_color=COLOR_SUCCESS)
        
        self.lbl_main_status.configure(text=f"XIN CHÀO: {name.upper()}", text_color=COLOR_SUCCESS)
        self.lbl_guide.configure(text="Xác thực thành công. Mời vào!")
        self.add_log_entry(f"Cửa mở cho: {name}", "success")
        
        # Reset blink
        self.TOTAL_BLINKS = 0
        self.waiting_for_blink = False
        self.current_candidate = None

    def lock_door(self):
        self.is_door_open = False
        
        # Giao diện ĐÓNG CỬA
        self.status_card.configure(fg_color=COLOR_BG)
        self.lbl_door_icon.configure(text="🔒")
        self.lbl_door_status.configure(text="ĐANG KHÓA")
        self.cam_container.configure(border_color="#404040")
        
        self.lbl_main_status.configure(text="ĐANG GIÁM SÁT...", text_color="white")
        self.lbl_guide.configure(text="")
        self.TOTAL_BLINKS = 0

    # --- HỆ THỐNG ---
    def check_admin_permission(self):
        dialog = ctk.CTkInputDialog(text="Nhập mật khẩu (admin):", title="Bảo mật")
        pwd = dialog.get_input()
        if pwd == self.ADMIN_PASSWORD: return True
        else:
            tk.messagebox.showerror("Lỗi", "Sai mật khẩu quản trị!")
            return False

    def load_data(self):
        if os.path.exists(self.encoding_file):
            try:
                with open(self.encoding_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data["encodings"]
                    self.known_face_names = data["names"]
                self.info_label.configure(text=f"Database: {len(self.known_face_names)} users")
            except: pass

    def update_camera(self):
        start_time = time.time()
        ret, frame = self.capture.read()
        if ret:
            # Auto lock
            if self.is_door_open and (time.time() - self.last_unlock_time > self.DOOR_OPEN_DURATION):
                self.lock_door()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # DETECTION
            if self.process_this_frame and not self.is_training:
                self.face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, self.face_locations)
                
                self.face_names = []
                
                if len(self.face_locations) == 0:
                    self.current_candidate = None
                    self.waiting_for_blink = False
                    if not self.is_door_open: self.lbl_guide.configure(text="")

                for idx, face_encoding in enumerate(face_encodings):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.45)
                    name = "Unknown"
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            
                            # LOGIC LIVENESS
                            if not self.is_door_open:
                                self.current_candidate = name
                                self.waiting_for_blink = True
                                
                                if idx < len(face_landmarks_list):
                                    landmarks = face_landmarks_list[idx]
                                    leftEye = landmarks['left_eye']
                                    rightEye = landmarks['right_eye']
                                    ear = (self.eye_aspect_ratio(leftEye) + self.eye_aspect_ratio(rightEye)) / 2.0
                                    
                                    if ear < self.EYE_AR_THRESH:
                                        self.COUNTER += 1
                                    else:
                                        if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                                            self.TOTAL_BLINKS += 1
                                        self.COUNTER = 0
                                    
                                    if self.TOTAL_BLINKS < self.REQUIRED_BLINKS:
                                        self.lbl_main_status.configure(text=f"PHÁT HIỆN: {name}", text_color=COLOR_WARNING)
                                        self.lbl_guide.configure(text=f"⚠️ VUI LÒNG NHÁY MẮT ({self.TOTAL_BLINKS}/{self.REQUIRED_BLINKS})")
                                    else:
                                        self.grant_access(name)
                                        threading.Thread(target=self.log_attendance, args=(name,)).start()
                        else:
                            if not self.is_door_open:
                                self.lbl_main_status.configure(text="NGƯỜI LẠ", text_color=COLOR_DANGER)
                                self.lbl_guide.configure(text="Không có quyền truy cập!", text_color=COLOR_DANGER)
                                self.cam_container.configure(border_color=COLOR_DANGER)

                    self.face_names.append(name)

            self.process_this_frame = not self.process_this_frame

            # DRAWING
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                top *= 4; right *= 4; bottom *= 4; left *= 4
                color = (46, 204, 113) if name == self.current_candidate and self.is_door_open else (231, 76, 60)
                if name != "Unknown" and not self.is_door_open: color = (241, 196, 15)

                # Vẽ khung đẹp hơn (Bo góc giả lập)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name.upper(), (left + 10, bottom - 8), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

            # Hiển thị lên UI
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            # Resize ảnh để vừa khung hình
            imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(720, 540)) 
            self.camera_label.configure(image=imgtk)

            # Tính FPS
            fps = 1.0 / (time.time() - start_time)
            self.lbl_fps.configure(text=f"FPS: {int(fps)}")

        self.after(10, self.update_camera)

    def log_attendance(self, name):
        now = datetime.now()
        filename = f"{self.log_dir}/log_{now.strftime('%Y-%m-%d')}.csv"
        try:
            if not os.path.exists(filename):
                with open(filename, "w", encoding='utf-8') as f: f.write("Name,Time\n")
            with open(filename, "a", encoding='utf-8') as f:
                f.write(f"{name},{now.strftime('%H:%M:%S')}\n")
        except: pass

    def register_new_user(self):
        if not self.check_admin_permission(): return
        dialog = ctk.CTkInputDialog(text="Nhập tên cư dân (Viết liền):", title="Đăng ký")
        name = dialog.get_input()
        if name:
            ret, frame = self.capture.read()
            if ret:
                path = f"{self.db_dir}/{name}.jpg"
                cv2.imwrite(path, frame)
                tk.messagebox.showinfo("OK", "Đã chụp ảnh xong.\nHãy bấm 'Huấn Luyện AI' để cập nhật!")
                self.add_log_entry(f"Đã thêm cư dân: {name}")

    def start_training_thread(self):
        if self.is_training: return
        if not self.check_admin_permission(): return
        self.is_training = True
        self.btn_train.configure(state="disabled", text="⏳ Đang xử lý...")
        self.progress_bar.grid(); self.progress_bar.set(0)
        threading.Thread(target=self.process_training_data).start()

    def process_training_data(self):
        known_encodings = []
        known_names = []
        image_paths = [os.path.join(self.db_dir, f) for f in os.listdir(self.db_dir) if f.endswith('.jpg')]
        total = len(image_paths)
        if total == 0:
            self.after(0, lambda: tk.messagebox.showwarning("Lỗi", "Không có dữ liệu ảnh!"))
            self.reset_ui_after_training()
            return

        for i, path in enumerate(image_paths):
            name = os.path.splitext(os.path.basename(path))[0]
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda n=name: self.info_label.configure(text=f"Learning: {n}..."))
            
            image = face_recognition.load_image_file(path)
            boxes = face_recognition.face_locations(image, model="hog")
            encodings = face_recognition.face_encodings(image, boxes)
            if len(encodings) > 0:
                known_encodings.append(encodings[0])
                known_names.append(name)

        data = {"encodings": known_encodings, "names": known_names}
        with open(self.encoding_file, "wb") as f: f.write(pickle.dumps(data))
        self.after(0, self.load_data)
        self.after(0, lambda: tk.messagebox.showinfo("Thành công", "Huấn luyện AI hoàn tất!"))
        self.after(0, self.reset_ui_after_training)

    def reset_ui_after_training(self):
        self.is_training = False
        self.btn_train.configure(state="normal", text="  🔄  Huấn Luyện AI ")
        self.progress_bar.grid_remove()
        self.info_label.configure(text="Hệ thống sẵn sàng")
        self.add_log_entry("Cập nhật dữ liệu AI thành công")

    def on_closing(self):
        self.capture.release()
        self.destroy()

if __name__ == "__main__":
    app = SecurityApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
