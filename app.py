from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)

# Create the text stamp
def create_stamp(text, width, height):
    packet = io.BytesIO()

    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont("Helvetica", 10)
    can.drawString(10, height - 20, text)
    can.save()

    packet.seek(0)
    return PdfReader(packet)


# Process each uploaded PDF
def process_pdf(file, name):
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        stamp_pdf = create_stamp(name, width, height)
        stamp_page = stamp_pdf.pages[0]

        page.merge_page(stamp_page)
        writer.add_page(page)

    return writer


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded"

        final_writer = PdfWriter()

        for file in files:

            name = os.path.splitext(file.filename)[0]

            processed = process_pdf(file, name)

            for page in processed.pages:
                final_writer.add_page(page)

        output = io.BytesIO()
        final_writer.write(output)
        output.seek(0)

        return send_file(
            output,
            download_name="merged.pdf",
            as_attachment=True
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
