
import re
import pdfplumber

# 1. TRÍCH XUẤT CƠ QUAN BAN HÀNH TỪ VỊ TRÍ CỐ ĐỊNH
def extract_co_quan_ban_hanh_by_position(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            words = pdf.pages[0].extract_words()
            left_words = [w for w in words if w["x0"] < 250 and w["top"] < 180]
            sorted_words = sorted(left_words, key=lambda w: (w["top"], w["x0"]))

            collected = []
            current_top = -100
            current_line = []

            stop_pattern = r"(số\\s*:?)|(/)|(:)|\\\\"

            for w in sorted_words:
                text = w["text"]
                if abs(w["top"] - current_top) > 10:
                    if current_line:
                        joined = " ".join(current_line).lower()
                        if re.search(stop_pattern, joined):
                            break
                        collected.append(joined)
                    current_line = [text]
                    current_top = w["top"]
                else:
                    current_line.append(text)

            if current_line:
                joined = " ".join(current_line).lower()
                if not re.search(stop_pattern, joined):
                    collected.append(joined)

            return " ".join(collected).strip().upper()

    except Exception as e:
        print("Lỗi khi trích xuất cơ quan ban hành:", e)
        return ""   