import mysql.connector
from flask import Flask, render_template, request, redirect, flash, make_response
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'faris_secret_key'


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'db_rawatinap_faris'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT * FROM pasien_faris
    """
    cursor.execute(query)
    data_pasien = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', data_pasien=data_pasien)

@app.route('/cetak')
def cetak():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_pasien, nama, alamat, kontak FROM pasien_faris")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)
    pdf.set_font_size(16)
    pdf.cell(0, 10, 'Data Pasien Rawat Inap', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font_size(12)
    pdf.cell(40, 10, 'ID Pasien', 1, 0, 'C')
    pdf.cell(60, 10, 'Nama Pasien', 1, 0, 'C')
    pdf.cell(60, 10, 'Alamat', 1, 0, 'C')
    pdf.cell(40, 10, 'Kontak', 1, 1, 'C')
    pdf.set_fill_color(240, 240, 240)
    for d in data:
        pdf.cell(40, 10, str(d['id_pasien']), 1, 0, 'C', fill=True)
        pdf.cell(60, 10, d['nama'], 1, 0, 'C', fill=True)
        pdf.cell(60, 10, d['alamat'], 1, 0, 'C', fill=True)
        pdf.cell(40, 10, d['kontak'], 1, 1, 'C', fill=True)

    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=data_pasien_rawat_inap.pdf'
    return response


@app.route('/transaksi/cetak')
def cetak_transaksi():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id_transaksi, t.id_pasien, p.nama, t.total_biaya, t.status_pembayaran, t.tgl
        FROM transaksi_faris t
        JOIN pasien_faris p ON t.id_pasien = p.id_pasien
        ORDER BY t.id_transaksi DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)
    pdf.set_font_size(16)
    pdf.cell(0, 10, 'Data Transaksi', 0, 1, 'C')
    pdf.ln(8)
    pdf.set_font_size(11)
    pdf.cell(25, 8, 'ID', 1, 0, 'C')
    pdf.cell(55, 8, 'Nama Pasien', 1, 0, 'C')
    pdf.cell(35, 8, 'Total', 1, 0, 'C')
    pdf.cell(35, 8, 'Tanggal', 1, 0, 'C')
    pdf.cell(30, 8, 'Status', 1, 1, 'C')
    pdf.set_fill_color(245, 245, 245)
    for d in data:
        pdf.cell(25, 8, f"TRX-00{d['id_transaksi']}", 1, 0, 'C', fill=True)
        pdf.cell(55, 8, d['nama'][:30], 1, 0, 'L', fill=True)
        pdf.cell(35, 8, f"Rp {d['total_biaya']:,.0f}", 1, 0, 'R', fill=True)
        pdf.cell(35, 8, str(d['tgl']), 1, 0, 'C', fill=True)
        status = 'Lunas' if d['status_pembayaran'] else 'Belum Lunas'
        pdf.cell(30, 8, status, 1, 1, 'C', fill=True)

    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=data_transaksi.pdf'
    return response


@app.route('/transaksi/cetak/pasien/<int:id_pasien>')
def cetak_transaksi_pasien(id_pasien):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id_transaksi, t.id_pasien, p.nama, t.total_biaya, t.status_pembayaran, t.tgl
        FROM transaksi_faris t
        JOIN pasien_faris p ON t.id_pasien = p.id_pasien
        WHERE t.id_pasien = %s
        ORDER BY t.id_transaksi DESC
    """, (id_pasien,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)
    pdf.set_font_size(15)
    pasien_nama = data[0]['nama'] if data else f'ID {id_pasien}'
    pdf.cell(0, 10, f'Data Transaksi - {pasien_nama}', 0, 1, 'C')
    pdf.ln(8)
    pdf.set_font_size(11)
    pdf.cell(30, 8, 'ID Trans.', 1, 0, 'C')
    pdf.cell(50, 8, 'Tanggal', 1, 0, 'C')
    pdf.cell(50, 8, 'Total', 1, 0, 'C')
    pdf.cell(50, 8, 'Status', 1, 1, 'C')
    pdf.set_fill_color(245, 245, 245)
    for d in data:
        pdf.cell(30, 8, f"TRX-00{d['id_transaksi']}", 1, 0, 'C', fill=True)
        pdf.cell(50, 8, str(d['tgl']), 1, 0, 'C', fill=True)
        pdf.cell(50, 8, f"Rp {d['total_biaya']:,.0f}", 1, 0, 'R', fill=True)
        status = 'Lunas' if d['status_pembayaran'] else 'Belum Lunas'
        pdf.cell(50, 8, status, 1, 1, 'C', fill=True)

    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=data_transaksi_pasien_{id_pasien}.pdf'
    return response

@app.route('/bayar/<id_rawat>')
def proses_bayar(id_rawat):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    

    cursor.execute("""
        SELECT ri.*, k.harga 
        FROM rawat_inap_faris ri 
        JOIN kamar_faris k ON ri.id_kamar = k.id_kamar 
        WHERE ri.id_rawat = %s""", (id_rawat,))
    row = cursor.fetchone()
    
    if row:
        selisih = row['tgl_keluar'] - row['tgl_masuk']
        durasi = max(selisih.days, 1) 
        total_biaya = durasi * row['harga']
        tgl_skrg = datetime.now().strftime('%Y-%m-%d')
        
        sql = "INSERT INTO transaksi_faris (id_pasien, total_biaya, status_pembayaran, tgl) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (row['id_pasien'], total_biaya, 1, tgl_skrg))
        conn.commit()
        flash(f"Transaksi Berhasil! Total Biaya: Rp {total_biaya:,.0f}")
    
    cursor.close()
    conn.close()
    return redirect('/transaksi')

@app.route('/transaksi')
def list_transaksi():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT t.id_transaksi, t.id_pasien, p.nama, t.total_biaya, t.status_pembayaran, t.tgl
        FROM transaksi_faris t
        JOIN pasien_faris p ON t.id_pasien = p.id_pasien
        ORDER BY t.id_transaksi DESC
    """
    cursor.execute(query)
    data_transaksi = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transaksi.html', data_transaksi=data_transaksi)

@app.route('/transaksi/update/<int:id_transaksi>')
def update_transaksi(id_transaksi):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status_pembayaran FROM transaksi_faris WHERE id_transaksi = %s", (id_transaksi,))
    current = cursor.fetchone()
    if current is not None:
        new_status = 0 if current['status_pembayaran'] else 1
        cursor.execute("UPDATE transaksi_faris SET status_pembayaran = %s WHERE id_transaksi = %s", (new_status, id_transaksi))
        conn.commit()
        flash("Status pembayaran diperbarui.")
    cursor.close()
    conn.close()
    return redirect('/transaksi')

@app.route('/transaksi/delete/<int:id_transaksi>')
def delete_transaksi(id_transaksi):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transaksi_faris WHERE id_transaksi = %s", (id_transaksi,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Data transaksi dihapus.")
    return redirect('/transaksi')

@app.route('/transaksi/edit/<int:id_transaksi>', methods=['GET', 'POST'])
def edit_transaksi(id_transaksi):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        total_biaya = request.form['total_biaya']
        tgl = request.form['tgl']
        status_pembayaran = request.form['status_pembayaran']
        cursor.execute(
            "UPDATE transaksi_faris SET total_biaya=%s, tgl=%s, status_pembayaran=%s WHERE id_transaksi=%s",
            (total_biaya, tgl, status_pembayaran, id_transaksi)
        )
        conn.commit()
        flash("Data transaksi berhasil diubah.")
        cursor.close()
        conn.close()
        return redirect('/transaksi')
    else:
        cursor.execute("SELECT t.*, p.nama FROM transaksi_faris t JOIN pasien_faris p ON t.id_pasien = p.id_pasien WHERE t.id_transaksi=%s", (id_transaksi,))
        transaksi = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('edit_transaksi.html', transaksi=transaksi)

@app.route('/transaksi/tambah', methods=['GET', 'POST'])
def tambah_transaksi():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    kelas_list = [
        {'nama': 'Standar', 'harga': 200000},
        {'nama': 'Reguler', 'harga': 350000},
        {'nama': 'VIP', 'harga': 500000}
    ]

    if request.method == 'POST':
        nama_pasien = request.form['nama_pasien']
        kelas = request.form['kelas']
        tgl_masuk = request.form['tgl_masuk']
        tgl_keluar = request.form['tgl_keluar']
        status_pembayaran = request.form['status_pembayaran']

        if not nama_pasien or not kelas or not tgl_masuk or not tgl_keluar or status_pembayaran not in ['0', '1']:
            flash('Semua field wajib diisi!')
            cursor.close()
            conn.close()
            return redirect('/transaksi/tambah')
        try:
            tgl1 = datetime.strptime(tgl_masuk, '%Y-%m-%d')
            tgl2 = datetime.strptime(tgl_keluar, '%Y-%m-%d')
        except ValueError:
            flash('Format tanggal tidak valid!')
            cursor.close()
            conn.close()
            return redirect('/transaksi/tambah')
        if tgl2 < tgl1:
            flash('Tanggal keluar tidak boleh sebelum tanggal masuk!')
            cursor.close()
            conn.close()
            return redirect('/transaksi/tambah')

        harga_per_hari = next((k['harga'] for k in kelas_list if k['nama'] == kelas), 0)

        durasi = max((tgl2 - tgl1).days, 1)
        total_biaya = durasi * harga_per_hari

        cursor.execute("SELECT id_transaksi FROM transaksi_faris ORDER BY id_transaksi")
        existing_ids = [row['id_transaksi'] for row in cursor.fetchall()]
        new_id = 1
        for eid in existing_ids:
            if eid != new_id:
                break
            new_id += 1

        cursor.execute("""
            INSERT INTO transaksi_faris (id_transaksi, nama, total_biaya, status_pembayaran, tgl)
            VALUES (%s, %s, %s, %s, %s)
        """, (new_id, nama_pasien, total_biaya, status_pembayaran, tgl_keluar))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Data transaksi berhasil ditambahkan dengan ID TRX-00{new_id:02d}.")
        return redirect('/transaksi')

    cursor.close()
    conn.close()
    return render_template('tambah_transaksi.html', kelas_list=kelas_list)

if __name__ == '__main__':
    app.run(debug=True)

