import os
import base64
import numpy as np
import cv2
import face_recognition
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json # Untuk menyimpan embedding sebagai JSON string

# --- Konfigurasi Aplikasi Flask ---
app = Flask(__name__)

# Konfigurasi database MySQL
# Ganti dengan kredensial MySQL Anda dan nama database yang baru Anda buat.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/face_recognition_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Model Database untuk Menyimpan Embedding Wajah ---
class FaceEmbedding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), unique=True, nullable=False) # NIK dari pegawai, harus unik
    name = db.Column(db.String(255), nullable=False) # Nama pegawai
    # Embedding data akan disimpan sebagai TEXT (JSON string dari array float)
    embedding_data = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<FaceEmbedding {self.nik} - {self.name}>'

# --- Helper Functions for Image and Face Processing ---

def decode_base64_image(base64_string):
    """
    Mengubah string Base64 (dengan atau tanpa prefiks data URI) menjadi gambar OpenCV (numpy array).
    """
    # Hapus prefiks data URI jika ada (e.g., "data:image/jpeg;base64,")
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    
    try:
        # Dekode string Base64
        img_bytes = base64.b64decode(base64_string)
        # Ubah bytes menjadi numpy array
        np_arr = np.frombuffer(img_bytes, np.uint8)
        # Dekode numpy array menjadi gambar OpenCV (BGR)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        app.logger.error(f"Error decoding base64 image: {e}")
        return None

def get_face_embedding(image):
    """
    Mendeteksi wajah dalam gambar dan mengembalikan embedding wajah pertama yang ditemukan.
    Mengembalikan None jika tidak ada wajah terdeteksi.
    """
    if image is None:
        return None

    # Ubah gambar dari BGR (OpenCV default) ke RGB (face_recognition default)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Temukan lokasi wajah di gambar
    face_locations = face_recognition.face_locations(rgb_image)

    if not face_locations:
        return None # Tidak ada wajah terdeteksi

    # Ekstrak embedding untuk wajah pertama yang ditemukan
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
    
    if face_encodings:
        return face_encodings[0] # Mengembalikan embedding pertama
    return None

def find_matching_face(new_embedding):
    """
    Mencari embedding yang paling cocok di database.
    Mengembalikan NIK dan nama jika ditemukan, None jika tidak.
    """
    if new_embedding is None:
        return None, None

    all_faces = FaceEmbedding.query.all()
    
    known_embeddings = []
    known_niks = []
    known_names = []

    for face in all_faces:
        try:
            # Ubah string JSON embedding kembali menjadi numpy array
            embedding_array = np.array(json.loads(face.embedding_data))
            known_embeddings.append(embedding_array)
            known_niks.append(face.nik)
            known_names.append(face.name)
        except json.JSONDecodeError as e:
            app.logger.error(f"Error decoding embedding for NIK {face.nik}: {e}")
            continue # Lewati embedding yang rusak

    if not known_embeddings:
        return None, None # Tidak ada embedding di database

    # Bandingkan embedding baru dengan semua embedding yang dikenal
    # face_distance mengembalikan array jarak, di mana jarak yang lebih kecil berarti lebih mirip
    # Tolerance adalah batas seberapa mirip wajah harus sama. Default face_recognition adalah 0.6.
    # Nilai ini bisa disesuaikan.
    face_distances = face_recognition.face_distance(known_embeddings, new_embedding)
    
    # Temukan indeks wajah yang paling mirip (jarak terpendek)
    best_match_index = np.argmin(face_distances)
    
    # Tentukan apakah kecocokan terbaik itu cukup dekat (di bawah ambang batas)
    # Anda bisa menyesuaikan nilai ambang batas ini. 0.6 adalah nilai default yang umum.
    tolerance = 0.6 # Semakin kecil, semakin ketat kecocokannya
    
    if face_distances[best_match_index] < tolerance:
        return known_niks[best_match_index], known_names[best_match_index], (1 - face_distances[best_match_index]) # Mengembalikan NIK, nama, dan kepercayaan
    
    return None, None, 0.0 # Tidak ada kecocokan yang cukup kuat

# --- Endpoint API ---

@app.route('/register_face', methods=['POST'])
def register_face():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()
    required_fields = ['image', 'name', 'nik']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing field: {field}"}), 400

    image_base64 = data['image']
    name = data['name']
    nik = data['nik']

    # 1. Dekode gambar dari Base64
    image = decode_base64_image(image_base64)
    if image is None:
        return jsonify({"message": "Invalid image data provided."}), 400

    # 2. Ekstrak embedding wajah
    embedding = get_face_embedding(image)
    if embedding is None:
        return jsonify({"message": "No face detected in the image. Please try again."}), 400

    # Ubah numpy array embedding menjadi string JSON untuk penyimpanan
    embedding_json_string = json.dumps(embedding.tolist())

    # Cek apakah NIK sudah terdaftar
    existing_face = FaceEmbedding.query.filter_by(nik=nik).first()
    if existing_face:
        # Jika NIK sudah ada, update embedding dan nama
        existing_face.embedding_data = embedding_json_string
        existing_face.name = name
        db.session.commit()
        return jsonify({
            "message": "Face embedding updated successfully.",
            "nik": nik,
            "name": name
        }), 200
    else:
        # Jika NIK belum ada, buat entri baru
        new_face_embedding = FaceEmbedding(
            nik=nik,
            name=name,
            embedding_data=embedding_json_string
        )
        db.session.add(new_face_embedding)
        db.session.commit()
        return jsonify({
            "message": "Face registered successfully.",
            "nik": nik,
            "name": name
        }), 201 # 201 Created

@app.route('/recognize_face', methods=['POST'])
def recognize_face():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()
    if 'image' not in data:
        return jsonify({"message": "Missing field: image"}), 400

    image_base64 = data['image']

    # 1. Dekode gambar dari Base64
    image = decode_base64_image(image_base64)
    if image is None:
        return jsonify({"message": "Invalid image data provided."}), 400

    # 2. Ekstrak embedding wajah dari gambar yang diunggah
    new_embedding = get_face_embedding(image)
    if new_embedding is None:
        return jsonify({"message": "No face detected in the image. Please try again."}), 400

    # 3. Cari kecocokan di database
    recognized_nik, recognized_name, confidence = find_matching_face(new_embedding)

    if recognized_nik:
        return jsonify({
            "message": f"Face recognized as {recognized_name} (NIK: {recognized_nik})",
            "nik": recognized_nik,
            "name": recognized_name,
            "confidence": round(confidence * 100, 2) # Ubah ke persentase
        }), 200
    else:
        return jsonify({
            "message": "Face not recognized or no strong match found.",
            "nik": "UNKNOWN",
            "name": "UNKNOWN",
            "confidence": 0.0
        }), 404 # 404 Not Found

if __name__ == '__main__':
    with app.app_context():
        # Membuat tabel di database MySQL jika belum ada
        db.create_all()
    
    # Jalankan server Flask
    app.run(debug=True, host='0.0.0.0', port=5000)