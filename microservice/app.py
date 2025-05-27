import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# --- Konfigurasi Aplikasi Flask ---
app = Flask(__name__)

# Konfigurasi database MySQL
# Ganti 'root', '', '127.0.0.1:3306', dan 'face_recognition_db'
# dengan kredensial MySQL Anda dan nama database yang baru Anda buat.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/face_recognition_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Model Database untuk Menyimpan Embedding Wajah ---
# Kita asumsikan embedding adalah string JSON dari array float
class FaceEmbedding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), unique=True, nullable=False) # NIK dari pegawai, harus unik
    name = db.Column(db.String(255), nullable=False) # Nama pegawai
    # Embedding data akan disimpan sebagai TEXT atau JSON string
    # Nantinya ini akan berisi array float dari fitur wajah
    embedding_data = db.Column(db.Text, nullable=False) # TEXT cocok untuk menyimpan JSON string dari array float

    def __repr__(self):
        return f'<FaceEmbedding {self.nik} - {self.name}>'

# --- Endpoint API ---

@app.route('/register_face', methods=['POST'])
def register_face():
    # Pastikan request body adalah JSON
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()

    # Validasi data yang diterima dari Laravel
    required_fields = ['image', 'name', 'nik']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing field: {field}"}), 400

    image_base64 = data['image']
    name = data['name']
    nik = data['nik']

    # --- Simulasi Logika Face Recognition dan Penyimpanan Embedding ---
    # Di sini nantinya akan ada kode untuk:
    # 1. Mengubah image_base64 menjadi format gambar (misal dengan OpenCV).
    # 2. Mendeteksi wajah dan mengekstrak embedding (array angka).
    # 3. Mengubah array embedding menjadi string (misal JSON) untuk disimpan.

    # Untuk sementara, kita akan menggunakan string dummy sebagai embedding
    # Anggap ini adalah hasil dari proses face recognition
    simulated_embedding = f"[{nik}_embedding_simulasi_untuk_{name}]"

    # Cek apakah NIK sudah terdaftar
    existing_face = FaceEmbedding.query.filter_by(nik=nik).first()
    if existing_face:
        # Jika NIK sudah ada, update embedding yang lama
        existing_face.embedding_data = simulated_embedding
        existing_face.name = name # Update nama juga jika berubah
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
            embedding_data=simulated_embedding
        )
        db.session.add(new_face_embedding)
        db.session.commit()
        return jsonify({
            "message": "Face registered successfully.",
            "nik": nik,
            "name": nik # Menggunakan NIK sebagai nama di sini juga untuk konsistensi
        }), 201 # 201 Created

@app.route('/recognize_face', methods=['POST'])
def recognize_face():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()

    if 'image' not in data:
        return jsonify({"message": "Missing field: image"}), 400

    image_base64 = data['image']

    # --- Simulasi Logika Face Recognition dan Pengenalan ---
    # Di sini nantinya akan ada kode untuk:
    # 1. Mengubah image_base64 menjadi format gambar.
    # 2. Mendeteksi wajah dan mengekstrak embedding.
    # 3. Mengambil semua embedding yang tersimpan dari database (FaceEmbedding.query.all()).
    # 4. Membandingkan embedding baru dengan semua embedding yang ada
    #    untuk mencari kemiripan (misal menggunakan cosine similarity).
    # 5. Mengembalikan NIK dari wajah yang paling cocok dengan confidence score.

    # Untuk simulasi, kita akan "mengenali" NIK pertama yang ada di database
    # atau mengembalikan UNKNOWN jika database kosong.
    first_registered_face = FaceEmbedding.query.first()

    if first_registered_face:
        # Asumsikan wajah ini dikenali dengan NIK yang ada di database
        recognized_nik = first_registered_face.nik
        recognized_name = first_registered_face.name
        confidence = 0.95 # Angka kepercayaan simulasi
        message = f"Face recognized as {recognized_name} (NIK: {recognized_nik})"
        status_code = 200
    else:
        recognized_nik = "UNKNOWN"
        recognized_name = "UNKNOWN"
        confidence = 0.0
        message = "Face not recognized. No embeddings in database."
        status_code = 404 # 404 Not Found jika tidak ada kecocokan

    return jsonify({
        "message": message,
        "nik": recognized_nik,
        "name": recognized_name,
        "confidence": confidence
    }), status_code


if __name__ == '__main__':
    # Buat tabel database jika belum ada
    with app.app_context():
        db.create_all()
    
    # Jalankan server Flask
    # host='0.0.0.0' agar bisa diakses dari luar localhost (jika perlu)
    # port=5000 harus sama dengan PYTHON_MICROSERVICE_URL di .env Laravel
    app.run(debug=True, host='0.0.0.0', port=5000)
