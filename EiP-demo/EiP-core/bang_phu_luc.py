#==================TRÍCH BẢNG TỪ PDF===================================
from import_lib import unicodedata, pdfplumber, re

#Thuật toán tìm bảng trong phần phụ lục của file PDF - thuật toán này trích xuất tên người xuất hiện trong bảng
#Trích xuất thông tin sinh viên và các cán bộ liên quan
# Phương án 1: Sử dụng ngôn ngữ java và lib PDF.js để convert file PDF sang dạng html vì khi sử dụng browser để mở file PDF 
# chúng ta luôn thấy được đầy đủ thông tin
# ---> Nhưng khi thực hiện phương án này không thành công: Khi convert sang dạng HTML các element như cột, bảng rất khó để xác định và
# trích xuất nội dung rất khó và không thành công
# ---> Sử dụng phương án 2
# Phương án 2: Sử dụng python với bộ lib nhiều hơn ---> nhưng khi convert qua html cũng không thành công ----> Trích bảng trực tiếp PDF
# Sử dụng lib của python: fitz  # PyMuPDF, pdfplumber ---> nhận diện được bảng và trích xuất ngay được những thông tin cần thiết.


# Từ khóa tiêu đề chuẩn để xác định trong bảng
TIEU_DE_CHUAN = {
    "ma_sinh_vien": ["sinh vien", "mssv", "sv", "ma sv", "ma hv"],
    "ho_va_ten": ["ho ten", "ho va ten", "sv"],
    "can_bo": ["huong dan", "phan bien", "gvhd", "gvpb", "can bo", "giang vien"],
    "vai_tro": ["vai tro", "trach nhiem", "chuc danh", "nhiem vu"]
}   # -> Tiêu đề chuẩn để chuẩn hóa các tiêu đề của các cột trong bảng

#Chuẩn hóa tiêu đề trong bảng
def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = text.replace("\n", " ").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def match_column(header_norm):
    for field, patterns in TIEU_DE_CHUAN.items():
        for pattern in patterns:
            if pattern in header_norm:
                return field
    return None

def split_degree_and_name(text):
    # Ghép chuỗi học vị có thể viết rời bằng khoảng trắng hoặc thiếu dấu chấm
    hoc_vi_patterns = [
        r"(?:T\s*S\s*\.?)", r"(?:T\s*h\s*S\s*\.?)", r"(?:T\s*S\s*K\s*H\s*\.?)",
        r"(?:P\s*G\s*S\s*\.?\s*T\s*S\s*\.?)", r"(?:P\s*G\s*S\s*\.?\s*T\s*S\s*K\s*H\s*\.?)"
        r"(?:G\s*S\s*\.?\s*T\s*S\s*\.?)", r"(?:G\s*S\s*\.?\s*T\s*S\s*K\s*H\s*\.?)",
        r"(?:P\s*G\s*S\s*\.?)", r"(?:G\s*S\s*\.?)"
    ]

    pattern = r"^\s*(" + "|".join(hoc_vi_patterns) + r")\s+(.+)$"
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if match:
        hoc_vi_raw = match.group(1)
        ho_ten = match.group(2).strip()

        # Chuẩn hóa học vị về dạng chuẩn
        hoc_vi_norm = normalize_hoc_vi(hoc_vi_raw)
        return hoc_vi_norm, ho_ten
    return "", text.strip()

def normalize_hoc_vi(hoc_vi):
    hoc_vi = normalize(hoc_vi).replace(" ", "").replace(".", "").upper()
    mapping = {
        "TS": "TS.",
        "TSKH": "TSKH.",
        "THS": "ThS.",
        "PGSTS": "PGS.TS.",
        "PGS": "PGS.",
        "GSTS": "GS.TS.",
        "GS": "GS.",
        "GSTSKH":"GS.TSKH",
        "PGSTSKH":"PGS.TSKH"
    }
    return mapping.get(hoc_vi, hoc_vi)


#Phân biệt cán bộ thông qua tên
def is_can_bo(text):
    hoc_vi, _ = split_degree_and_name(text)
    return bool(hoc_vi)



#Nếu 2 cán bộ có tên trong cùng 1 ô
def tach_danh_sach_can_bo(text):
    hoc_vi_pattern = r"(?:TSKH\.|PG S\.TS\.|P GS\.TS\.|P GS\.T S|PG S\.T S|PGS\.TS\.|GS\.TSKH\.|GS\.TS\.|GS\.|PGS\.|TS\.|ThS\.)"
    pattern = rf"({hoc_vi_pattern}\s+[^\n,;]+)"
    return [match.strip() for match in re.findall(pattern, text)]



#Chuẩn hóa vai trò
VAI_TRO_KEYWORDS = {
    "phản biện": "Phản biện",
    "phản biện 1": "Phản biện",
    "phản biện 2": "Phản biện",
    "hướng dẫn": "Hướng dẫn",
    "trách nhiệm": "Chịu trách nhiệm",
    "hỗ trợ": "Hỗ trợ",
    "chủ tịch": "Chủ tịch",
    "ủy viên": "Ủy viên",
    "thư ký": "Thư ký",
    "thành viên": "Ủy viên"
}

def tim_vai_tro_tu_key(text):
    text_norm = normalize(text)
    for keyword, role in VAI_TRO_KEYWORDS.items():
        if keyword in text_norm:
            return role
    return None




def chuan_hoa_vai_tro(key_raw):
    key_norm = normalize(key_raw)
    for pattern, role in VAI_TRO_KEYWORDS.items():
        if pattern in key_norm:
            return role
    return key_raw.strip().title().replace("\n", " ")  # fallback

#Tìm vai trò trong cùng 1 dòng
def tim_vai_tro_trong_dong(row):
    for cell in row:
        role = tim_vai_tro_tu_key(cell)
        if role:
            return role
    return "Không rõ vai trò"


#Hàm xuất bảng 
#hàm này lấy được vai trò bảng cán bộ:

def extract_tables_from_pdf(pdf_path):
    sinh_vien = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue

                headers_raw = [(cell or '') for cell in table[0]]
                headers_norm = [normalize(cell) for cell in headers_raw]

                # Tìm các cột đặc biệt
                vai_tro_col_index = -1
                for idx, header in enumerate(headers_norm):
                    if match_column(header) == "vai_tro":
                        vai_tro_col_index = idx
                        break

                for row in table[1:]:
                    row_dict = {}
                    can_bo_list = []

                    for j, cell in enumerate(row):
                        key_raw = headers_raw[j] if j < len(headers_raw) else f"Cột {j+1}"
                        key_norm = headers_norm[j]
                        value = (cell or '').replace('\n', ' ').strip()
                        field = match_column(key_norm)

                        # Trường hợp mã SV
                        if field == "ma_sinh_vien":
                            row_dict["Mã sinh viên"] = value

                        # Trường hợp SV (không có học vị)
                        elif field == "ho_va_ten" and not is_can_bo(value):
                            row_dict["Họ và tên"] = value

                        # Trường hợp CÁN BỘ (có học vị)
                        elif is_can_bo(value):
                            danh_sach = tach_danh_sach_can_bo(value)
                            for item in danh_sach:
                                hoc_vi, ho_ten = split_degree_and_name(item)

                                # =========================================== TÌM VAI TRÒ ================================
                                vai_tro = None

                                # 1️⃣ Nếu là bảng hội đồng → lấy từ cột vai trò
                                if vai_tro_col_index != -1 and vai_tro_col_index < len(row):
                                    raw_vai_tro = row[vai_tro_col_index]
                                    if raw_vai_tro:
                                        vai_tro = tim_vai_tro_tu_key(raw_vai_tro) or raw_vai_tro.strip()

                                # 2️⃣ Nếu là bảng sinh viên → lấy từ tiêu đề cột hiện tại
                                if not vai_tro:
                                    vai_tro = tim_vai_tro_tu_key(key_raw)

                                # 3️⃣ Nếu vẫn chưa có → tìm trong dòng
                                if not vai_tro:
                                    for cell_check in row:
                                        vai_tro = tim_vai_tro_tu_key(cell_check)
                                        if vai_tro:
                                            break

                                if not vai_tro:
                                    vai_tro = "Không rõ vai trò"

                                can_bo_list.append({
                                    "Ho_ten": ho_ten,
                                    "hoc_vi": hoc_vi,
                                    "vai_tro": vai_tro
                                })

                    # Ghi dữ liệu
                    if "Họ và tên" in row_dict:
                        sinh_vien.append({
                            "Ma_sinh_vien": row_dict.get("Mã sinh viên", ""),
                            "Ho_va_ten": row_dict["Họ và tên"],
                            "Can_bo": can_bo_list
                        })
                    elif can_bo_list:
                        sinh_vien.append({
                            "Ma_sinh_vien": "",
                            "Ho_va_ten": "",
                            "Can_bo": can_bo_list
                        })

    return sinh_vien