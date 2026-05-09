
import re
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import os
import json
from tkinter import Tk, Button, Label


# === BƯỚC 1: Chuyển PDF sang HTML giữ cấu trúc ===
def convert_pdf_to_structured_html(pdf_path, html_path):
    doc = fitz.open(pdf_path)
    html = ['<html><body style="position:relative; font-family:sans-serif;">']

    page = doc[0]  # chỉ trang đầu
    width = page.rect.width 
    height = page.rect.height
    html.append(f'<div style="position:relative; width:{width}px; height:{height}px;">')
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                x, y = span["bbox"][0], span["bbox"][1]
                size = span["size"]
                font = span["font"]
                html.append(
                    f'<div style="position:absolute; left:{x}px; top:{y}px; font-size:{size}px; '
                    f'font-family:{font}; white-space:nowrap;">{text}</div>'
                )
    html.append("</div></body></html>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


# === Tách tất cả text thành các block (top, left, text) ===
def get_text_blocks_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    text_blocks = []
    for div in soup.find_all("div"):
        style = div.get("style", "")
        if "left:" in style and "top:" in style:
            try:
                left = float(style.split("left:")[1].split("px")[0].strip())
                top = float(style.split("top:")[1].split("px")[0].strip())
                text = div.get_text(strip=True)
                text_blocks.append((top, left, text))
            except:
                continue
    return sorted(text_blocks, key=lambda x: x[0])  # sắp từ trên xuống


# === Trích số quyết định theo tọa độ từ HTML ===
def extract_so_quyet_dinh_from_html(html_path):
    text_blocks = get_text_blocks_from_html(html_path)
    for top, left, text in text_blocks:
        if re.match(r"(?i)^số[:\s]", text.strip()):
            closest = None
            min_dist = float("inf")
            for t_top, t_left, t_text in text_blocks:
                if abs(t_top - top) < 10 and abs(t_left - left) > 10:
                    dist = ((t_top - top) ** 2 + (t_left - left) ** 2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest = t_text
            if closest:
                return f"{closest.strip()} {text.strip().replace('Số:', '').strip()}"
            break
    return ""


# === Trích ngày ký từ HTML ===
def extract_ngay_ky_from_html(html_path):
    text_blocks = get_text_blocks_from_html(html_path)
    for top_ngay, left_ngay, text in text_blocks:
        if "ngày" in text.lower():
            nearby = [
                (t[1], t[2]) for t in text_blocks
                if abs(t[0] - top_ngay) <= 10 and abs(t[1] - left_ngay) <= 300
                and re.fullmatch(r"\d{1,4}", t[2])
            ]
            sorted_nearby = sorted(nearby, key=lambda x: x[0])

            ngay = thang = nam = ""
            for _, num in sorted_nearby:
                if not ngay and len(num) <= 2:
                    ngay = num
                elif not thang and len(num) <= 2:
                    thang = num
                elif not nam and len(num) == 4 and 1900 <= int(num) <= 2100:
                    nam = num

            # Chèn vào văn bản gốc
            base = text.strip()
            if "ngày" in base:
                base = re.sub(r"ngày\s*", f"ngày {ngay} ", base, flags=re.IGNORECASE)
            if "tháng" in base:
                base = re.sub(r"tháng\s*", f"tháng {thang} ", base, flags=re.IGNORECASE)
            if "năm" in base:
                base = re.sub(r"năm\s*", f"năm {nam} ", base, flags=re.IGNORECASE)
            return base.strip()
    return ""


def extract_so_va_ngay_from_pdf(pdf_path):
    html_path = os.path.splitext(pdf_path)[0] + "_layout.html"
    convert_pdf_to_structured_html(pdf_path, html_path)
    so_qd = extract_so_quyet_dinh_from_html(html_path)
    ngay_ky = extract_ngay_ky_from_html(html_path)
    if os.path.exists(html_path):
        os.remove(html_path)
    return {"so_quyet_dinh": so_qd, "ngay_ky": ngay_ky}

    



