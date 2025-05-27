<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http; // Penting untuk komunikasi HTTP
use App\Models\User; // Asumsi kamu akan menyimpan data user di tabel 'users'
use Illuminate\Support\Facades\Log; // Untuk logging

class FaceRecognitionController extends Controller
{
    /**
     * Mendaftarkan wajah baru ke microservice Python.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function registerFace(Request $request)
    {
        $request->validate([
            'image' => 'required|string',
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email|max:255', // Validasi email juga
            'nik' => 'required|string|unique:users,nik|max:20', // Ubah dari 'nim' ke 'nik'
            'phone_number' => 'nullable|string|max:15', // Tambahkan validasi phone_number
        ]);

        try {
            $response = Http::timeout(60)->post(env('PYTHON_MICROSERVICE_URL') . '/register_face', [
                'image' => $request->image,
                'name' => $request->name,
                'nik' => $request->nik, // Ubah dari 'nim' ke 'nik'
                // Jika Python Microservice juga butuh email/phone, kirimkan juga
            ]);

            if ($response->successful()) {
                $pythonResponse = $response->json();

                $user = User::create([
                    'name' => $request->name,
                    'email' => $request->email,
                    'password' => bcrypt($request->nik), // Bisa gunakan NIK sebagai password default
                    'nik' => $request->nik, // Simpan NIK
                    'phone_number' => $request->phone_number, // Simpan nomor telepon
                ]);

                return response()->json([
                    'message' => 'Wajah berhasil didaftarkan dan data user disimpan.',
                    'user_data' => $user,
                    'python_response' => $pythonResponse
                ], 200);

            } else {
                Log::error('Error dari Python Microservice (register_face): ' . $response->body());
                return response()->json([
                    'message' => 'Gagal mendaftarkan wajah ke microservice.',
                    'python_error' => $response->json()
                ], $response->status());
            }
        } catch (\Exception $e) {
            Log::error('Koneksi ke Python Microservice gagal (register_face): ' . $e->getMessage());
            return response()->json(['message' => 'Server error: Tidak dapat terhubung ke microservice.', 'error' => $e->getMessage()], 500);
        }
    }

    public function recognizeFace(Request $request)
    {
        $request->validate([
            'image' => 'required|string',
        ]);

        try {
            $response = Http::timeout(60)->post(env('PYTHON_MICROSERVICE_URL') . '/recognize_face', [
                'image' => $request->image,
            ]);

            if ($response->successful()) {
                $pythonResponse = $response->json();
                $recognizedNIK = $pythonResponse['nik'] ?? null; // Asumsi Python mengembalikan 'nik'
                $confidence = $pythonResponse['confidence'] ?? null;

                if ($recognizedNIK) {
                    $user = User::where('nik', $recognizedNIK)->first(); // Ubah dari 'nim' ke 'nik'

                    if ($user) {
                        // ... (logika absensi di sini)
                        return response()->json([
                            'message' => 'Wajah dikenali: ' . $user->name,
                            'user_data' => $user,
                            'recognition_details' => [
                                'nik' => $recognizedNIK, // Ubah ke 'nik'
                                'confidence' => $confidence,
                            ],
                            'python_response' => $pythonResponse
                        ], 200);
                    } else {
                        return response()->json(['message' => 'Wajah dikenali, tetapi NIK tidak ditemukan di database.', 'nik' => $recognizedNIK], 404);
                    }
                } else {
                    return response()->json(['message' => 'Wajah tidak dikenali.'], 404);
                }

            } else {
                Log::error('Error dari Python Microservice (recognize_face): ' . $response->body());
                return response()->json([
                    'message' => 'Gagal mengenali wajah via microservice.',
                    'python_error' => $response->json()
                ], $response->status());
            }
        } catch (\Exception $e) {
            Log::error('Koneksi ke Python Microservice gagal (recognize_face): ' . $e->getMessage());
            return response()->json(['message' => 'Server error: Tidak dapat terhubung ke microservice.', 'error' => $e->getMessage()], 500);
        }
    }

    /**
     * Mendapatkan daftar user.
     * Ini hanya contoh, mungkin perlu otentikasi/otorisasi.
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function getUsers()
    {
        $users = User::all();
        return response()->json($users);
    }
}