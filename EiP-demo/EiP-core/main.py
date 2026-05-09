from co_quan_ban_hanh import extract_co_quan_ban_hanh_by_position
from noi_nhan import extract_noi_nhan_va_nguoi_ky
from bang_phu_luc import extract_tables_from_pdf
from trich_yeu import extract_trich_yeu_from_text
from import_lib import scrolledtext, filedialog, messagebox, Button, tk, Tk, BOTH, WORD
from import_lib import json
from import_lib import os
from noi_dung import convert_pdf_to_html_and_extract_info, tach_can_cu_va_dieu
# from tom_tat_api import summarize_text_only
from sqd_ngayki import extract_so_va_ngay_from_pdf 
from ten_nguoi_trong_noi_dung import tim_ten_nguoi
# Hàm chính
def process_pdf():
    
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])

    if not file_paths:
        return

    output_text.delete(1.0, tk.END)
    all_results = []

    try:
        for file_path in file_paths:
# ==============================Cơ quan ban hành văn bản====================================================
            co_quan_ban_hanh = extract_co_quan_ban_hanh_by_position(file_path)

# =============================Số quyết định, ngày ký====================================================
            info = extract_so_va_ngay_from_pdf(file_path)

#==============================Nơi nhận và người ký====================================================
            noi_nhan = extract_noi_nhan_va_nguoi_ky(file_path)
        
# =============================Trích nội dung, tách căn cứ====================================================
            # Truy cập file và tạo file HTML tạm thời
            file_base = os.path.splitext(os.path.basename(file_path))[0]
            folder = os.path.dirname(file_path)
            html_output = os.path.join(folder, file_base + ".html")

            # Convert PDF to HTML and extract content
            noi_dung_file = convert_pdf_to_html_and_extract_info(file_path, html_output)

            # Tách nội dung căn cứ và điều từ nội dung content
            tach_noi_dung = tach_can_cu_va_dieu(noi_dung_file.get("noi_dung",""))

# ==============================Phụ lục====================================================
            tables = extract_tables_from_pdf(file_path)

# ===============================Trích yếu====================================================
            trich_yeu = extract_trich_yeu_from_text(file_path)

# =====================find person name in noi dung===========================================
            name_person = tim_ten_nguoi(file_path)

# =====================Gộp thông tin============================================================
            result = {
                "file": os.path.basename(file_path),
                "quoc_hieu": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
                "tieu_ngu": "Độc lập - Tự do - Hạnh phúc",
                "co_quan_ban_hanh": co_quan_ban_hanh,
                "so_quyet_dinh": info.get("so_quyet_dinh",""),
                "ngay_ky": info.get("ngay_ky", ""),
                "noi_nhan": noi_nhan.get("noi_nhan",""),
                "nguoi_ky": noi_nhan.get("nguoi_ky",""),
                "trich_yeu": trich_yeu,
                'noi_dung': tach_noi_dung,
                'ten_nguoi_trong_noi_dung': name_person,
                "loai_van_ban": "Quyết Định",
                "ten_nguoi_trong_bang_phu_luc": tables
            }
            

            all_results.append(result)
            output_text.insert(tk.END, f" Đã xử lý: {os.path.basename(file_path)}\n")

        # Ghi tất cả kết quả vào một file JSON
        json_path = os.path.join(os.path.dirname(file_paths[0]), "tong_hop_ket_qua.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)

        output_text.insert(tk.END, f"\n📄 Đã lưu toàn bộ kết quả vào: {json_path}")
        messagebox.showinfo("Hoàn tất", "Đã xử lý và lưu tất cả JSON thành công!")

    except Exception as e:
        messagebox.showerror("Lỗi", str(e))



# Giao diện
root = Tk()
root.title(" Trích xuất thông tin và bảng từ PDF sang JSON")
root.geometry("500x300")

Button(root, text="📂 Chọn file PDF", font=("Arial", 13), command=process_pdf).pack(pady=10)
output_frame = tk.LabelFrame(root, text="📄 Thông tin xử lý", padx=5, pady=5)
output_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

output_text = scrolledtext.ScrolledText(output_frame, wrap=WORD, font=("Consolas", 10))
output_text.pack(fill=BOTH, expand=True)


root.mainloop()
