# Import modul yang diperlukan
from flask import Flask, render_template, request, redirect, session, send_from_directory, flash, jsonify
import sqlite3  # Modul untuk bekerja dengan database SQLite
import os       # Modul untuk menangani operasi sistem file
from werkzeug.security import generate_password_hash, check_password_hash  # Untuk keamanan password

# Inisialisasi aplikasi Flask
app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))
app.secret_key = 'your_secret_key'  # Kunci rahasia untuk sesi pengguna

# Fungsi untuk menginisialisasi database SQLite
def init_db():
    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()

    # Membuat tabel User jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS User (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL)''')

    # Membuat tabel Transactions jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    note TEXT,
                    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE)''')

    conn.commit()  # Simpan perubahan
    conn.close()   # Tutup koneksi database

# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Jika pengguna mengirim form login
        username = request.form['username']  # Ambil username
        password = request.form['password']  # Ambil password

        conn = sqlite3.connect('finance.db')  # Koneksi ke database
        c = conn.cursor()
        c.execute("SELECT * FROM User WHERE username = ?", (username,))  # Cari pengguna berdasarkan username
        user = c.fetchone()  # Ambil hasil query
        conn.close()  # Tutup koneksi

        # Periksa apakah username dan password cocok
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]  # Simpan user_id di sesi
            return redirect('/')  # Arahkan ke halaman utama
        else:
            flash('Username atau password salah.', 'error')  # Tampilkan pesan kesalahan

    return render_template('login.html')  # Render halaman login

# Route untuk registrasi pengguna baru
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Jika pengguna mengirim form registrasi
        username = request.form['username']  # Ambil username
        password = generate_password_hash(request.form['password'])  # Hash password untuk keamanan

        conn = sqlite3.connect('finance.db')  # Koneksi ke database
        c = conn.cursor()
        c.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, password))  # Simpan pengguna baru
        conn.commit()  # Simpan perubahan
        conn.close()  # Tutup koneksi

        flash('Registrasi berhasil. Silakan login.', 'success')  # Pesan sukses
        return redirect('/login')  # Arahkan ke halaman login

    return render_template('register.html')  # Render halaman registrasi

# Route untuk logout pengguna
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Hapus sesi pengguna
    flash('Anda telah logout.', 'info')  # Tampilkan pesan logout
    return redirect('/login')  # Arahkan ke halaman login

# Route untuk halaman utama (dashboard)
@app.route('/')
def index():
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return redirect('/login')

    user_id = session['user_id']  # Ambil user_id dari sesi

    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()

    # Hitung saldo berdasarkan transaksi pengguna
    c.execute('''SELECT SUM(CASE 
                                WHEN type = 'Pemasukan' THEN amount 
                                ELSE -amount 
                            END) AS balance 
                 FROM Transactions WHERE user_id = ?''', (user_id,))
    balance = c.fetchone()[0] or 0.0  # Jika tidak ada transaksi, saldo = 0

    # Ambil semua transaksi pengguna
    c.execute("SELECT * FROM Transactions WHERE user_id = ?", (user_id,))
    transactions = c.fetchall()
    conn.close()  # Tutup koneksi

    return render_template('index.html', transactions=transactions, balance=balance)  # Render dashboard

# Route untuk menambahkan transaksi
@app.route('/add', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return redirect('/login')

    # Ambil data dari form transaksi
    user_id = session['user_id']
    transaction_type = request.form['type']
    amount = float(request.form['amount'])
    date = request.form['date']
    note = request.form['note']

    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()
    c.execute("INSERT INTO Transactions (user_id, type, amount, date, note) VALUES (?, ?, ?, ?, ?)",
              (user_id, transaction_type, amount, date, note))  # Simpan transaksi
    conn.commit()  # Simpan perubahan
    conn.close()  # Tutup koneksi
    return redirect('/')  # Arahkan kembali ke dashboard

# Route untuk menghapus transaksi
@app.route('/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return redirect('/login')

    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()
    c.execute("DELETE FROM Transactions WHERE transaction_id = ?", (transaction_id,))  # Hapus transaksi
    conn.commit()  # Simpan perubahan
    conn.close()  # Tutup koneksi
    return redirect('/')  # Arahkan kembali ke dashboard

# Route untuk mereset semua transaksi pengguna
@app.route('/reset', methods=['POST'])
def reset_transactions():
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return redirect('/login')

    user_id = session['user_id']  # Ambil user_id dari sesi
    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()
    c.execute("DELETE FROM Transactions WHERE user_id = ?", (user_id,))  # Hapus semua transaksi pengguna
    conn.commit()  # Simpan perubahan
    conn.close()  # Tutup koneksi
    return redirect('/')  # Arahkan kembali ke dashboard

# Route untuk melayani file CSS
@app.route('/styles.css')
def serve_css():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'styles.css')  # Kirim file CSS

# REST API: Mendapatkan semua transaksi pengguna
@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return jsonify({"error": "Unauthorized access"}), 401

    user_id = session['user_id']  # Ambil user_id dari sesi

    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()
    c.execute("SELECT * FROM Transactions WHERE user_id = ?", (user_id,))  # Ambil semua transaksi
    transactions = c.fetchall()
    conn.close()  # Tutup koneksi

    # Format hasil ke dalam JSON
    transactions_list = [
        {
            "transaction_id": row[0],
            "user_id": row[1],
            "type": row[2],
            "amount": row[3],
            "date": row[4],
            "note": row[5]
        } for row in transactions
    ]
    return jsonify(transactions_list)  # Kembalikan data sebagai JSON

# REST API: Mendapatkan saldo pengguna
@app.route('/api/balance', methods=['GET'])
def api_get_balance():
    if 'user_id' not in session:  # Periksa apakah pengguna sudah login
        return jsonify({"error": "Unauthorized access"}), 401

    user_id = session['user_id']  # Ambil user_id dari sesi

    conn = sqlite3.connect('finance.db')  # Koneksi ke database
    c = conn.cursor()
    c.execute('''SELECT SUM(CASE 
                                WHEN type = 'Pemasukan' THEN amount 
                                ELSE -amount 
                            END) AS balance 
                 FROM Transactions WHERE user_id = ?''', (user_id,))
    balance = c.fetchone()[0] or 0.0  # Jika tidak ada transaksi, saldo = 0
    conn.close()  # Tutup koneksi

    return jsonify({"balance": balance})  # Kembalikan saldo sebagai JSON

# Jalankan aplikasi
if __name__ == '__main__':
    init_db()  # Inisialisasi database
    app.run(debug=True)  # Jalankan aplikasi dalam mode debug