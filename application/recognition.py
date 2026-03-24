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


ENCODINGS_FILE = resource_path("encodings.npy")
NAMES_FILE = resource_path("names.npy")

class FaceRecognitionEngine:
    def __init__(self):
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
        
    # def load_known_faces(self, class_name, force_reload: bool = False):
    #     npy_dir = resource_path("npy")
    #     os.makedirs(npy_dir, exist_ok=True)

    #     enc_file = os.path.join(npy_dir, f"{class_name}_encodings.npy")
    #     names_file = os.path.join(npy_dir, f"{class_name}_names.npy")

    #     if force_reload:
    #         self.faces_loaded = False
    #         self.clear_tracking_state()

    #     if self.faces_loaded:
    #         return

    #     # Load existing npy
    #     if os.path.exists(enc_file) and os.path.exists(names_file):
    #         try:
    #             self.known_faces = np.load(enc_file, allow_pickle=True)
    #             self.known_names = np.load(names_file, allow_pickle=True)

    #             print(f"✅ Loaded {len(self.known_faces)} faces for {class_name}")
    #             self.faces_loaded = True
    #             return

    #         except Exception as e:
    #             print("⚠ Failed loading npy, regenerating:", e)

    #     # Load from local_filestore
    #     faces_dir = resource_path(f"local_filestore/{class_name}")

    #     self.known_faces = []
    #     self.known_names = []

    #     if not os.path.exists(faces_dir):
    #         print(f"⚠ No folder for {class_name}")
    #         return

    #     for file_name in os.listdir(faces_dir):

    #         if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
    #             continue

    #         img_path = os.path.join(faces_dir, file_name)

    #         try:
    #             image = face_recognition.load_image_file(img_path)
    #             encodings = face_recognition.face_encodings(image)

    #             if encodings:
    #                 self.known_faces.append(encodings[0])
    #                 self.known_names.append(os.path.splitext(file_name)[0])

    #         except Exception as e:
    #             print(f"Error loading {file_name}: {e}")

    #     # Save npy per class
    #     np.save(enc_file, self.known_faces)
    #     np.save(names_file, self.known_names)

    #     print(f"💾 Saved {len(self.known_faces)} encodings for {class_name}")

    #     self.faces_loaded = True
        
    def load_known_faces(self, force_reload: bool = False):
        if force_reload:
            self.faces_loaded = False
            self.clear_tracking_state()

        if self.faces_loaded:
            return

        if os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE):
            try:
                self.known_faces = np.load(ENCODINGS_FILE, allow_pickle=True)
                self.known_names = np.load(NAMES_FILE, allow_pickle=True)

                print(f"✅ Loaded {len(self.known_faces)} faces from .npy")
                self.faces_loaded = True
                return
            except Exception as e:
                print("⚠ Failed loading .npy, regenerating:", e)

        faces_dir = resource_path("faces")

        self.known_faces = []
        self.known_names = []

        for file_name in os.listdir(faces_dir):
            img_path = os.path.join(faces_dir, file_name)

            if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            try:
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    self.known_faces.append(encodings[0])
                    self.known_names.append(os.path.splitext(file_name)[0])

            except Exception as e:
                print(f"Error loading {file_name}: {e}")

        np.save(ENCODINGS_FILE, self.known_faces)
        np.save(NAMES_FILE, self.known_names)

        print(f"💾 Saved {len(self.known_faces)} encodings to .npy")

        self.faces_loaded = True

    # def load_known_faces(self, force_reload: bool = False):
    #     if force_reload:
    #         self.known_faces.clear()
    #         self.known_names.clear()
    #         self.faces_loaded = False
    #         self.clear_tracking_state()

    #     if self.faces_loaded:
    #         return

    #     faces_dir = resource_path("faces")

    #     if not os.path.exists(faces_dir):
    #         os.makedirs(faces_dir, exist_ok=True)
    #         print(f"Faces directory created: {faces_dir}")
    #         self.faces_loaded = True
    #         return

    #     self.known_faces.clear()
    #     self.known_names.clear()

    #     for file_name in os.listdir(faces_dir):
    #         img_path = os.path.join(faces_dir, file_name)

    #         if not os.path.isfile(img_path):
    #             continue

    #         if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
    #             continue

    #         try:
    #             image = face_recognition.load_image_file(img_path)
    #             encodings = face_recognition.face_encodings(image)

    #             print(f"{file_name} -> Encodings found: {len(encodings)}")

    #             if encodings:
    #                 self.known_faces.append(encodings[0])
    #                 self.known_names.append(os.path.splitext(file_name)[0])

    #         except Exception as e:
    #             print(f"Error loading face '{file_name}': {e}")

    #     print("Total faces loaded:", len(self.known_faces))
    #     self.faces_loaded = True

    def reload_known_faces(self):
        self.load_known_faces(force_reload=True)

    def detect_and_recognize(self, frame):
    # def detect_and_recognize(self, frame, class_name):
        # self.load_known_faces(class_name)
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

            original_id = track.track_id
            name = self.recognized_ids.get(original_id)
            display_id = original_id

            l, t, r, b = map(int, track.to_ltrb())
            l = max(0, l)
            t = max(0, t)
            r = max(0, r)
            b = max(0, b)

            if original_id not in self.track_states:
                self.track_states[original_id] = "recognizing"
                self.recognized_ids[original_id] = None

            if self.track_states[original_id] == "recognizing":
                face_crop = frame[t:b, l:r]

                if face_crop.size > 0:
                    rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_crop)
                    face_encodings = face_recognition.face_encodings(
                        rgb_crop, face_locations
                    )

                    for encoding in face_encodings:
                        if len(self.known_faces) > 0:
                            face_distances = face_recognition.face_distance(
                                self.known_faces, encoding
                            )

                            best_match_index = np.argmin(face_distances)
                            best_distance = face_distances[best_match_index]

                            if best_distance < 0.6:
                                name = self.known_names[best_match_index]

                                self.recognized_ids[original_id] = name
                                self.track_states[original_id] = "done"

                                if name in self.identity_map:
                                    display_id = self.identity_map[name]
                                else:
                                    self.identity_map[name] = original_id
                                    display_id = original_id

                                break

            name = self.recognized_ids.get(original_id)

            if name:
                display_id = self.identity_map.get(name, original_id)

            if self.track_states.get(original_id) == "recognizing":
                label = "Recognizing..."
                color = (0, 0, 255)

            elif name:
                label = f"{name} id {display_id}"
                color = (0, 255, 0)

            else:
                label = f"Unknown id {original_id}"
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

            people.append((
                display_id if name else original_id,
                name if name else None,
                l,
                t,
                r,
                b
            ))

        return frame, people


# Global engine instance
_engine = FaceRecognitionEngine()


def load_known_faces():
    _engine.load_known_faces()


def reload_known_faces():
    _engine.reload_known_faces()


def detect_and_recognize(frame):
    return _engine.detect_and_recognize(frame)

# def load_known_faces(class_name):
#     _engine.load_known_faces(class_name)


# def reload_known_faces(class_name):
#     _engine.load_known_faces(class_name, force_reload=True)


# def detect_and_recognize(frame, class_name):
#     return _engine.detect_and_recognize(frame, class_name)