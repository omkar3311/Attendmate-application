import os
import sys
import cv2
import face_recognition
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import numpy as np


def resource_path(path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)


class FaceRecognitionEngine:
    def __init__(self, class_name):
        self.class_name = class_name
        self.model = YOLO(resource_path("yolov8n.pt"))
        self.tracker = DeepSort(max_age=40)

        self.known_faces = []
        self.known_names = []

        self.recognized_ids = {}
        self.track_states = {}
        self.identity_map = {}
        self.faces_loaded = False

    def clear_tracking_state(self):
        self.recognized_ids.clear()
        self.track_states.clear()
        self.identity_map.clear()

    def load_known_faces(self, force_reload=False):
        if force_reload:
            self.faces_loaded = False
            self.clear_tracking_state()

        if self.faces_loaded:
            return

        self.known_faces = []
        self.known_names = []

        class_name = self.class_name

        student_enc_file = f"{class_name}_encodings.npy"
        student_names_file = f"{class_name}_names.npy"

        teacher_enc_file = "teacher_encodings.npy"
        teacher_names_file = "teacher_names.npy"

        student_dir = resource_path(f"local_filestore/{class_name}")
        teacher_dir = resource_path("local_filestore/teachers_faces")

        student_encodings = []
        student_names = []

        if os.path.exists(student_enc_file) and os.path.exists(student_names_file):
            student_encodings = list(np.load(student_enc_file, allow_pickle=True))
            student_names = list(np.load(student_names_file, allow_pickle=True))

        existing_students = set(student_names)

        if os.path.exists(student_dir):
            for file_name in os.listdir(student_dir):
                if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    continue

                name = os.path.splitext(file_name)[0].lower()

                if name in existing_students:
                    continue

                img_path = os.path.join(student_dir, file_name)

                try:
                    image = face_recognition.load_image_file(img_path)
                    encodings = face_recognition.face_encodings(image)

                    if encodings:
                        student_encodings.append(encodings[0])
                        student_names.append(name)

                except:
                    continue

        np.save(student_enc_file, student_encodings)
        np.save(student_names_file, student_names)

        teacher_encodings = []
        teacher_names = []

        if os.path.exists(teacher_enc_file) and os.path.exists(teacher_names_file):
            teacher_encodings = list(np.load(teacher_enc_file, allow_pickle=True))
            teacher_names = list(np.load(teacher_names_file, allow_pickle=True))

        existing_teachers = set(teacher_names)

        if os.path.exists(teacher_dir):
            for file_name in os.listdir(teacher_dir):
                if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    continue

                name = os.path.splitext(file_name)[0].lower()

                if name in existing_teachers:
                    continue

                img_path = os.path.join(teacher_dir, file_name)

                try:
                    image = face_recognition.load_image_file(img_path)
                    encodings = face_recognition.face_encodings(image)

                    if encodings:
                        teacher_encodings.append(encodings[0])
                        teacher_names.append(name)

                except:
                    continue

        np.save(teacher_enc_file, teacher_encodings)
        np.save(teacher_names_file, teacher_names)

        for enc, name in zip(student_encodings, student_names):
            self.known_faces.append(enc)
            self.known_names.append("student_" + name)

        for enc, name in zip(teacher_encodings, teacher_names):
            self.known_faces.append(enc)
            self.known_names.append("teacher_" + name)

        self.faces_loaded = True

    def reload_known_faces(self):
        self.load_known_faces(force_reload=True)

    def detect_and_recognize(self, frame):
        self.load_known_faces()

        results = self.model(frame, conf=0.4, classes=[0], verbose=False)

        detections = []

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()

            for box, score in zip(boxes, scores):
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                detections.append(([x1, y1, w, h], float(score), "person"))

        tracks = self.tracker.update_tracks(detections, frame=frame)

        people = []

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id

            l, t, r, b = map(int, track.to_ltrb())

            face_crop = frame[t:b, l:r]

            name = None

            if face_crop.size > 0:
                rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                encs = face_recognition.face_encodings(rgb)

                for enc in encs:
                    if len(self.known_faces) > 0:
                        dists = face_recognition.face_distance(self.known_faces, enc)
                        idx = np.argmin(dists)

                        if dists[idx] < 0.6:
                            name = self.known_names[idx]
                            break

            people.append((track_id, name))
            if name:
                label = name
                color = (0, 255, 0)
            else:
                label = "Unknown"
                color = (0, 255, 255)

            cv2.rectangle(frame, (l, t), (r, b), color, 2)
            cv2.putText(
                frame,
                label,
                (l, max(20, t - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        students = []
        teachers = []

        for _, name in people:
            if not name:
                continue

            if name.startswith("teacher_"):
                teachers.append(name.replace("teacher_", ""))
            else:
                students.append(name.replace("student_", ""))

        return frame, students, teachers


# Global engine instance
# _engine = FaceRecognitionEngine()


# def load_known_faces():
#     _engine.load_known_faces()


# def reload_known_faces():
#     _engine.reload_known_faces()


# def detect_and_recognize(frame):
#     return _engine.detect_and_recognize(frame)

# def load_known_faces(class_name):
#     _engine.load_known_faces(class_name)


# def reload_known_faces(class_name):
#     _engine.load_known_faces(class_name, force_reload=True)


# def detect_and_recognize(frame, class_name):
#     return _engine.detect_and_recognize(frame, class_name)