import pdfplumber, re, fitz, os

#Thuật toán trích xuất phần nội dung trong văn bản QUYẾT ĐỊNH: 
# - Lấy nội dung theo keyword: "Căn cứ" và dừng lại khi gặp kí tự "./." ----> Có thể phát triển để lấy nội dung trong văn bản khác
# bằng cách lấy đoạn text bắt đầu từ sau trích yếu và dừng lại khi gặp kí tự "./."


def check_table_in_content_area(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += "\n" + text

            end_match = re.search(r"(nơi nhận|\./\.)", full_text, re.IGNORECASE)
            if end_match:
                full_text = full_text[:end_match.start()]
            start_match = re.search(r"(Căn cứ|Điều\s+\d+)", full_text, re.IGNORECASE)
            if start_match:
                full_text = full_text[start_match.start():]

            for page in pdf.pages:
                tables = page.extract_tables()
                if any(table for table in tables if table):
                    return True
        return False
    except:
        return False

# === Hàm trích nội dung không có bảng ===
def extract_noi_dung_without_tables(pdf_path):
    try:
        collected_lines = []
        started = False
        ended = False

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                tables = page.find_tables()

                table_areas = [t.bbox for t in tables if t.bbox]

                lines_by_y = {}
                for word in words:
                    y0 = round(float(word["top"]))
                    lines_by_y.setdefault(y0, []).append(word)

                for y in sorted(lines_by_y.keys()):
                    line_words = sorted(lines_by_y[y], key=lambda w: w["x0"])
                    line_text = " ".join(w["text"] for w in line_words).strip()
                    if not line_text:
                        continue
                    line_y = float(line_words[0]["top"])
                    if any(top <= line_y <= bottom for (_, top, _, bottom) in table_areas):
                        continue

                    lower = line_text.lower()
                    if not started and ("căn cứ" in lower or re.match(r"^điều\s+\d+", line_text, re.IGNORECASE)):
                        started = True

                    if started:
                        if "nơi nhận" in lower or "./." in line_text:
                            ended = True
                            break
                        collected_lines.append(line_text)

                if ended:
                    break

        return "\n".join(collected_lines).strip()

    except Exception as e:
        print("Lỗi khi trích nội dung không có bảng:", e)
        return ""

# === Hàm trích nội dung bình thường ===
def extract_noi_dung_binh_thuong(full_text):
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    noi_dung_lines = []
    started = False
    for line in lines:
        lower = line.lower()
        if not started and ("căn cứ" in lower or re.match(r"^điều\s+\d+", line, re.IGNORECASE)):
            started = True
        if started:
            if "./." in line or "nơi nhận" in lower:
                break
            noi_dung_lines.append(line)
    return "\n".join(noi_dung_lines).strip()

# === Hàm chính ===
def convert_pdf_to_html_and_extract_info(pdf_path, html_output):
    doc = fitz.open(pdf_path)
    html_lines = ['<html><body style="font-family:sans-serif; margin:30px;">']
    full_text = ""

    for page_num, page in enumerate(doc, 1):
        html_lines.append(f'<div style="margin-bottom:80px;"> <!-- Page {page_num} -->')
        blocks = page.get_text("blocks")
        blocks_sorted = sorted(blocks, key=lambda b: (round(b[1]), b[0]))
        grouped_lines = []
        current_line_y = None
        line = []

        for block in blocks_sorted:
            x0, y0, x1, y1, text, *_ = block
            clean = text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            full_text += text + "\n"
            if not clean:
                continue
            if current_line_y is None or abs(y0 - current_line_y) <= 2:
                line.append((x0, clean))
                current_line_y = y0
            else:
                line_sorted = sorted(line)
                line_text = " ".join(t for _, t in line_sorted)
                grouped_lines.append(line_text.strip())
                line = [(x0, clean)]
                current_line_y = y0
        if line:
            line_sorted = sorted(line)
            line_text = " ".join(t for _, t in line_sorted)
            grouped_lines.append(line_text.strip())

        for l in grouped_lines:
            html_lines.append(f"<p style='margin:2px 0'>{l}</p>")

        html_lines.append("</div>")

    html_lines.append("</body></html>")
    with open(html_output, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    end_match = re.search(r"(nơi nhận|\./\.)", full_text, re.IGNORECASE)
    if end_match:
        full_text = full_text[:end_match.start()]

    info = {}
    has_table = check_table_in_content_area(pdf_path)
    if has_table:
        info["noi_dung"] = extract_noi_dung_without_tables(pdf_path)
    else:
        info["noi_dung"] = extract_noi_dung_binh_thuong(full_text)

    info["noi_dung"] = " ".join(info["noi_dung"].split())

    if os.path.exists(html_output):
        os.remove(html_output)

    return info



#def tach_can_cu_va_dieu(noi_dung: str):
    """
    Tách nội dung thành danh sách các căn cứ và điều.
    - 'cac_can_cu': list các dòng bắt đầu bằng 'Căn cứ'
    - 'cac_dieu': list các điều, mỗi điều có thể gồm nhiều dòng
    """
    lines = [line.strip() for line in noi_dung.splitlines() if line.strip()]
    
    cac_can_cu = []
    cac_dieu = []
    current_dieu = []

    for line in lines:
        if line.lower().startswith("căn cứ"):
            cac_can_cu.append(line)

        elif re.match(r"^Điều\s+\d+", line, re.IGNORECASE):
            # Nếu đang gom nội dung cho điều trước đó thì lưu lại
            if current_dieu:
                cac_dieu.append("\n".join(current_dieu).strip())
                current_dieu = []
            current_dieu.append(line)

        else:
            if current_dieu:  # đang ở trong 1 điều thì nối thêm
                current_dieu.append(line)

    # Thêm điều cuối cùng
    if current_dieu:
        cac_dieu.append("\n".join(current_dieu).strip())

    return {
        "cac_can_cu": cac_can_cu,
        "cac_dieu": cac_dieu
    }



#from bs4 import BeautifulSoup

#def tach_can_cu_va_dieu(html):
    """
    Tách phần nội dung văn bản quyết định từ HTML.
    - Bắt đầu từ 'Căn cứ'
    - Kết thúc khi gặp './.' hoặc 'Nơi nhận'
    - Trả về: căn cứ, nội dung chính, các điều
    """

    # 1. Tách text từ HTML
    soup = BeautifulSoup(html, "html.parser")
    raw_lines = soup.get_text(separator="\n").split("\n")

    # loại dòng trống + strip
    lines = [l.strip() for l in raw_lines if l.strip()]

    # ==========================
    # Chuẩn bị regex nhận dạng
    # ==========================
    pattern_can_cu = re.compile(r"^Căn cứ", re.IGNORECASE)
    pattern_dieu = re.compile(r"^Điều[\s\.\-:]*0*([0-9]+)\b", re.IGNORECASE)
    pattern_stop = re.compile(r"Nơi nhận", re.IGNORECASE)
    stop_token = "./."

    in_noi_dung = False   # đã bắt đầu từ Căn cứ chưa
    in_can_cu = False
    in_dieu = False

    noi_dung_chinh = []
    cac_can_cu = []
    cac_dieu = []
    current_dieu = ""

    for line in lines:

        # Chưa vào phần nội dung → chỉ vào khi gặp "Căn cứ"
        if not in_noi_dung:
            if pattern_can_cu.match(line):
                in_noi_dung = True
                in_can_cu = True
                cac_can_cu.append(line)
                noi_dung_chinh.append(line)
            continue

        # Nếu đã vào nội dung → kiểm tra điểm dừng
        if stop_token in line or pattern_stop.search(line):
            break

        # Ghép toàn bộ vào noi_dung_chinh
        noi_dung_chinh.append(line)

        # ==========================
        # 1) TÁCH PHẦN CĂN CỨ
        # ==========================
        if in_can_cu:
            # Nếu gặp Điều → kết thúc phần căn cứ
            if pattern_dieu.match(line):
                in_can_cu = False
                in_dieu = True
                current_dieu = line
                cac_dieu.append(line)
                continue

            # Nếu vẫn trong căn cứ → nối vào mục căn cứ cuối cùng
            cac_can_cu[-1] += " " + line
            continue

        # ==========================
        # 2) TÁCH CÁC ĐIỀU
        # ==========================
        match_dieu = pattern_dieu.match(line)
        if match_dieu:
            # gặp điều mới → lưu điều cũ (nếu có)
            if current_dieu:
                cac_dieu.append(current_dieu)
            current_dieu = line
            in_dieu = True
            continue

        # Nếu đang trong điều → nối dòng tiếp theo vào điều hiện tại
        if in_dieu:
            current_dieu += " " + line
            continue

    # thêm điều cuối cùng nếu có
    if current_dieu:
        cac_dieu.append(current_dieu)

    # ==========================
    # Chuẩn hóa dữ liệu trả về
    # ==========================
    noi_dung_chinh_text = " ".join(noi_dung_chinh).strip()

    return {
        "noi_dung": {
            "noi_dung_chinh": noi_dung_chinh_text,
            "cac_can_cu": [re.sub(r"\s+", " ", x).strip() for x in cac_can_cu],
            "cac_dieu": [re.sub(r"\s+", " ", x).strip() for x in cac_dieu]
        }
    }




import re

def tach_can_cu_va_dieu(text):
    """
    Nhận text liền mạch.
    - Bắt đầu từ 'Căn cứ'
    - Kết thúc khi gặp './.' hoặc 'Nơi nhận'
    - Tách cac_can_cu và cac_dieu (từ Điều 1, Điều 2... tăng dần)
    Trả về dict:
    {
      "noi_dung": {
        "noi_dung_chinh": "...",
        "cac_can_cu": [...],
        "cac_dieu": [...]
      }
    }
    """

    # 1. Chuẩn hóa whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # 2. Tìm bắt đầu "Căn cứ"
    start_m = re.search(r"Căn cứ", text)
    if not start_m:
        return {"noi_dung_chinh": "", "cac_can_cu": [], "cac_dieu": []}

    start_idx = start_m.start()

    # 3. Tìm điểm dừng: "./." hoặc "Nơi nhận"
    stop_m = re.search(r"\./\.|Nơi nhận", text[start_idx:], flags=re.IGNORECASE)
    if stop_m:
        end_idx = start_idx + stop_m.start()
    else:
        end_idx = len(text)

    
    # 3.1 Tìm điểm dừng của các căn cứ: "QUYẾT ĐỊNH" -> test
    stop_cc = re.search(r"QUYẾT\s*ĐỊNH", text[start_idx:])
    if stop_cc:
        end_idx_cc = start_idx + stop_cc.start()
    else: 
        end_idx_cc = len(text)

    segment_cc = text[start_idx:end_idx_cc].strip()  # phần từ Căn cứ tới trước Quyết định
    
    #==================================================================
    segment = text[start_idx:end_idx].strip()  # phần từ Căn cứ tới trước stop token
    noi_dung_chinh = segment  # lưu nguyên phần nội dung chính


    stop_cc = re.search(r"QUYẾT\s*ĐỊNH", text[start_idx:])
    if stop_cc:
        end_idx_cc = start_idx + stop_cc.start()
    else: 
        end_idx_cc = len(text)

    segment_cc = text[start_idx:end_idx_cc].strip()  # phần từ Căn cứ tới trước Quyết định


    # 4. Tách cac_can_cu: lấy các đoạn bắt đầu bằng "Căn cứ"
    #    Cách đơn giản: chia theo từ "Căn cứ" (giữ tiền tố) rồi làm sạch các mục rỗng.
    can_cu_splits = re.split(r"(?i)(?=Căn cứ\b)", segment_cc)  # giữ "Căn cứ" ở đầu từng phần
    cac_can_cu = []
    for part in can_cu_splits:
        part = part.strip()
        if not part:
            continue
        if re.match(r"(?i)^Căn cứ\b", part):
            # nếu phần chứa "Căn cứ" nhưng tiếp theo là nhiều nội dung, cố gắng tách theo ";" nếu có
            # ví dụ: "Căn cứ ...; Căn cứ ...;"
            # tách những đoạn con bắt đầu bằng "Căn cứ"
            subparts = re.split(r"(?i)(?=Căn cứ\b)", part)
            for sp in subparts:
                sp = sp.strip().rstrip(";")
                if sp:
                    cac_can_cu.append(re.sub(r"\s+", " ", sp))
        else:
            # phần đầu nếu không bắt đầu bằng Căn cứ (header) -> bỏ qua
            continue

    # 5. Tách các Điều:
    #    pattern bắt các dạng: "Điều 1", "Điều1", "Điều 1.", "Điều 1 .", "ĐIỀU 01:", ...
    pattern_dieu = re.compile(r"Điều\s*\.?\s*0*([0-9]+)\s*[\.\:\-–—]?", re.IGNORECASE)

    # tìm tất cả match trong segment và thu vị trí
    matches = list(pattern_dieu.finditer(segment))

    # Giả sử phan_sau là phần chứa các Điều
    cac_dieu = []
    current_dieu = 1
    while True:
        pat_this = rf"Điều\s*{current_dieu}\s*\.?"
        this_m = re.search(pat_this, segment, flags=re.IGNORECASE)
        if not this_m:
            break
        start_d = this_m.start()

        # Điều kế tiếp
        pat_next = rf"Điều\s*{current_dieu+1}\s*\.?"
        next_m = re.search(pat_next, segment, flags=re.IGNORECASE)
        if next_m:
            end_d = next_m.start()
        else:
            end_d = len(segment)  # <-- slice tới hết segment nếu không có điều kế tiếp

        dieu_text = segment[start_d:end_d].strip()
        dieu_text = re.sub(r"\s+", " ", dieu_text)
        cac_dieu.append(dieu_text)
        current_dieu += 1



    # 6. Chuẩn hóa dữ liệu trả về
    cac_can_cu = [re.sub(r"\s+", " ", c).strip() for c in cac_can_cu]
    cac_dieu = [re.sub(r"\s+", " ", d).strip() for d in cac_dieu]
    noi_dung_chinh = re.sub(r"\s+", " ", noi_dung_chinh).strip()

    return {
        "noi_dung_chinh": noi_dung_chinh,
        "cac_can_cu": cac_can_cu,
        "cac_dieu": cac_dieu
    }

