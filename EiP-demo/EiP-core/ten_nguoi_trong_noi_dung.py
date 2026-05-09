import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import json
import re
import os
from bs4 import BeautifulSoup

 # tiền tố chỉ người học: học viên, sinh  viên, học viên cao học, HVCH, nghiên cứu sinh, NCS.
 # tiền tố chỉ cán bộ nhân viên: học hàm học vị, cán bộ, đồng chí, nhân viên, ông, bà, chuyên viên
 # tên học viên và tên cán bộ luôn có tiền tố
# 1. TRÍCH TÊN NGƯỜI (CÓ KIỂM TRA TIỀN TỐ + HOA CHỮ CÁI ĐẦU)
def find_person_names(text):
    # Tiền tố người học
    student_prefixes = [
        "học viên", "sinh viên", "học viên cao học",
        "hvch", "HVCH", "nghiên cứu sinh", "NCS", "ncs"
    ]

    # Tiền tố cán bộ - nhân viên
    staff_prefixes = [
        "cán bộ", "đồng chí", "nhân viên",
        "ông", "bà", "chuyên viên"
    ]

    # Học hàm - học vị
    academic_titles = [
        "GS", "PGS", "TS", "ThS",
        "GS.", "PGS.", "TS.", "ThS.", "CN."
    ]

    all_prefixes = student_prefixes + staff_prefixes + academic_titles

    # Regex tìm: tiền tố + khoảng trắng + tên (tên capitalized)
    pattern = (
        r"(?i)\b(" + "|".join(all_prefixes) +
        r")\s+([A-ZĐ][a-zà-ỹ]+(?:\s+[A-ZĐ][a-zà-ỹ]+)+)\b"
    )

    matches = re.findall(pattern, text, flags=re.UNICODE)

    # matches = [(prefix, name), ...]
    extracted_list = []

    for prefix, name in matches:
        # Kiểm tra tên có viết hoa đầu mỗi từ
        words = name.split()
        if all(w[0].isupper() and w[1:].islower() for w in words):
            extracted_list.append({
                "tien_to": prefix.strip(),
                "ten": name.strip(),
                "full_name": f"{prefix.strip()} {name.strip()}"
                })

    # Loại trùng
    unique = {
        item["full_name"]: item
        for item in extracted_list
    }

    return list(unique.values())



# 2. TRÍCH NỘI DUNG TỪ "Căn cứ" ĐẾN "./." / "Nơi nhận"
def extract_noi_dung_from_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text("\n", strip=True)

    lower_text = text.lower()

    # Tìm “Căn cứ”
    start_index = lower_text.find("điều")
    if start_index == -1:
        return ""

    extracted = text[start_index:]

    # Các điều kiện kết thúc
    end_patterns = [
        r"\./\.",
        r"nơi nhận",
        r"noi nhan"
    ]

    end_pos = None
    for pattern in end_patterns:
        match = re.search(pattern, extracted, flags=re.IGNORECASE)
        if match:
            end_pos = match.start()
            break

    if end_pos:
        extracted = extracted[:end_pos]

    return extracted.strip()


# 3. PDF → HTML TEXT
def pdf_to_html_text(pdf_path):
    doc = fitz.open(pdf_path)
    html_text = ""

    for page in doc:
        html_text += page.get_text("html")

    return html_text


# 4. GHI JSON
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# 5. HÀM CHÍNH ĐÃ CẬP NHẬT
def tim_ten_nguoi(pdf_path):
    if not pdf_path:
        return
    
    output_dir = os.path.dirname(pdf_path)
    # B1: PDF → HTML text
    html_text = pdf_to_html_text(pdf_path)

    # B2: Trích nội dung từ "Căn cứ"
    noi_dung = extract_noi_dung_from_html(html_text)

    if not noi_dung:
        return ""

    # B3: Lưu nội dung draf dạng JSON
    json_noi_dung_path = os.path.join(output_dir, "noi_dung.json")
    save_json(json_noi_dung_path, {"noi_dung": noi_dung})

    # B4: Trích tên người
    names = find_person_names(noi_dung)

    # B5: Lưu tên người vào file
    #json_names_path = os.path.join(output_dir,"names.json")
    #save_json(json_names_path, {"names": names})

    # B6: Xóa file nội dung draf dạng JSON
    if os.path.exists(json_noi_dung_path):
        os.remove(json_noi_dung_path)

    return names


