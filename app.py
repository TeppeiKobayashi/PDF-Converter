from flask import Flask, request, send_file, render_template, redirect, url_for
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF, for rendering pages to images
import tempfile
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# 'uploads'フォルダが存在しない場合は作成する
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def create_4_in_1_page(pages):
    packet = io.BytesIO()
    temp_writer = PdfWriter()
    for page in pages:
        if page is not None:
            temp_writer.add_page(page)
    temp_writer.write(packet)
    packet.seek(0)

    packet_data = packet.getvalue()
    doc = fitz.open("pdf", packet_data)
    first_page = doc[0]
    page_width = first_page.rect.width
    page_height = first_page.rect.height

    new_page_width = page_width * 2
    new_page_height = page_height * 2

    result = io.BytesIO()
    c = canvas.Canvas(result, pagesize=(new_page_width, new_page_height))
    positions = [(0, page_height), (page_width, page_height), (0, 0), (page_width, 0)]

    for i, page in enumerate(pages):
        if page is not None:
            x, y = positions[i]
            c.saveState()
            c.translate(x, y)
            pix = doc[i].get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                tmp_img_file.write(pix.tobytes("png"))
                tmp_img_file.close()
                c.drawImage(tmp_img_file.name, 0, 0, width=page_width, height=page_height)
            c.restoreState()
    c.save()
    result.seek(0)
    return PdfReader(result).pages[0]

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files['file']
        if file:
            try:
                reader = PdfReader(file)
                writer = PdfWriter()
                page_group = []
                for page in reader.pages:
                    page_group.append(page)
                    if len(page_group) == 4:
                        writer.add_page(create_4_in_1_page(page_group))
                        page_group = []

                if page_group:
                    while len(page_group) < 4:
                        page_group.append(None)
                    writer.add_page(create_4_in_1_page([p for p in page_group if p]))

                output = io.BytesIO()
                writer.write(output)
                output.seek(0)

                # 保存するファイル名を生成
                output_pdf_path = os.path.join('uploads', 'merged.pdf')
                with open(output_pdf_path, 'wb') as output_pdf:
                    output_pdf.write(output.read())
                
                # ダウンロードURLを生成
                download_url = url_for('uploaded_file', filename='merged.pdf')

                return render_template("upload.html", download_url=download_url)
            except Exception as e:
                return render_template("upload.html", error_message=str(e))

    return render_template("upload.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_file(os.path.join('uploads', filename), as_attachment=True)

@app.route("/index")
def index():
    return render_template("index.html")

@app.after_request
def add_permission_policy_header(response):
    response.headers['Permissions-Policy'] = (
        "geolocation=(), microphone=(), camera=(), fullscreen=(self)"
    )
    return response

if __name__ == "__main__":
    app.run(debug=True)