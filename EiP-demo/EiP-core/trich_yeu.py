from import_lib import pdfplumber, re

#======================================TRÍCH TRÍCH YẾU=======================================================

# Trích trích yếu linh hoạt
def extract_trich_yeu_from_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text()
            if not text:
                return ""
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            trich_yeu_lines = []

            # Từ khóa tiêu đề tài liệu
            title_keywords = [
                "QUYẾT ĐỊNH", "THÔNG BÁO", "TỜ TRÌNH", "BIÊN BẢN", "BÁO CÁO", "DANH SÁCH", "CÔNG VĂN"
            ]
            found = False
            for i, line in enumerate(lines):
                if any(kw in line.upper() for kw in title_keywords):
                    found = True
                    continue
                if found:
                    upper = line.upper()
                    if (
                        re.match(r"^\u0110iều\s+\d+", line, re.IGNORECASE)
                        or "CĂN CỨ" in upper
                        or "ĐIỀU 1" in upper
                        or "NƠI NHẬN" in upper
                        or "KÝ TÊN" in upper
                        or line.isupper()
                        or len(line) < 10
                    ):
                        break
                    trich_yeu_lines.append(line)

            return " ".join(trich_yeu_lines).strip()
    except Exception as e:
        return ""