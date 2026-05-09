#Thuật toán trích nơi nhận và người kí:
# - Tìm đoạn text "Nơi nhận:" vì ở văn bản hành chính nào cũng có
# sau đó từ nơi nhận tìm sang đối diện về phía bên phải của văn bản sẽ có khu vực người kí, có thể tìm thông tin trong 5 6 dòng đó
# sẽ ra thông tin người kí



def extract_noi_nhan_va_nguoi_ky(pdf_path):
    import pdfplumber
    import re

    result = {
        "noi_nhan": "",
        "nguoi_ky": {
            "chuc_vu": "",
            "ten": ""
        }
    }

    keywords = ["GIÁM ĐỐC", "PHÓ GIÁM ĐỐC", "KT.", "HIỆU TRƯỞNG", "PHÓ HIỆU TRƯỞNG", "KT", "CHỦ TỊCH", "TRƯỞNG PHÒNG"]

    with pdfplumber.open(pdf_path) as pdf:
        for page in reversed(pdf.pages):
            words = page.extract_words()
            lines_by_y = {}
            for word in words:
                y = round(word["top"])
                lines_by_y.setdefault(y, []).append(word)

            y_noi_nhan = None
            for y in sorted(lines_by_y.keys()):
                line_text = " ".join(w["text"] for w in lines_by_y[y])
                if "nơi nhận" in line_text.lower():
                    y_noi_nhan = y
                    break

            if y_noi_nhan is None:
                continue

            # Trích nơi nhận bên trái
            noi_nhan_lines = []
            for y in sorted(lines_by_y.keys()):
                if y >= y_noi_nhan:
                    left_text = " ".join(w["text"] for w in lines_by_y[y] if w["x0"] < 300).strip()
                    if left_text:
                        noi_nhan_lines.append(left_text)

            # Phân tích bên phải
            right_lines = []
            for y in sorted(lines_by_y.keys()):
                if y >= y_noi_nhan:
                    right_text = " ".join(w["text"] for w in lines_by_y[y] if w["x0"] >= 300).strip()
                    if right_text:
                        right_lines.append(right_text)

            # Phân tích người ký
            chuc_vu_lines = []
            ten_line = ""
            for line in right_lines:
                line_upper = line.upper()
                if any(k in line_upper for k in keywords):
                    chuc_vu_lines.append(line.strip())
                elif 2 <= len(line.split()) <= 5:
                    ten_line = re.sub(r"[^\w\sÀ-ỹ]", "", line).strip()

            result["noi_nhan"] = "\n".join(noi_nhan_lines).strip()
            result["nguoi_ky"]["chuc_vu"] = "\n".join(chuc_vu_lines).strip()
            result["nguoi_ky"]["ten"] = ten_line
            break

    return result
