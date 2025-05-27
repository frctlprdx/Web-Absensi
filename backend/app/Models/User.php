<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail; // Baris ini tidak perlu jika tidak menggunakan verifikasi email
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens; // Pertahankan jika Anda berencana menggunakan Laravel Sanctum untuk API authentication

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
     */
    protected $fillable = [
        'name',
        'email',
        'password',
        'nik',          // Kolom NIK
        'phone_number', // Kolom Nomor Telepon
    ];

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var array<int, string>
     */
    protected $hidden = [
        'password',
        'remember_token',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array<string, string>
     */
    protected $casts = [
        // 'email_verified_at' => 'datetime', // Baris ini dihapus karena kolomnya sudah tidak ada di tabel
        'password' => 'hashed', // Penting: Otomatis hash password saat disimpan
    ];

    // Jika Anda berencana menggunakan fitur verifikasi email di masa depan,
    // Anda bisa mengimplementasikan MustVerifyEmail interface dan menambahkan kolomnya kembali.
    // Namun untuk saat ini, kita hapus.
}