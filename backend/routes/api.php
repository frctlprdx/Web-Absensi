<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\FaceRecognitionController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "api" middleware group. Make something great!
|
*/

Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

// --- Route untuk Face Recognition ---
// Endpoint untuk mendaftarkan wajah baru
Route::post('/face-register', [FaceRecognitionController::class, 'registerFace']);

// Endpoint untuk melakukan absensi/pengenalan wajah
Route::post('/face-recognize', [FaceRecognitionController::class, 'recognizeFace']);

// Endpoint untuk mendapatkan daftar pengguna (jika dibutuhkan)
Route::get('/users', [FaceRecognitionController::class, 'getUsers']);

