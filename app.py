from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

import io
import os

app = Flask(__name__)


def create_stamp(
    text,
    width,
    height,
    position="top-left",
    font_size=20,
    padding=6,
    margin=15,
    opacity=0.4
):

    packet = io.BytesIO()

    can = canvas.Canvas(
        packet,
        pagesize=(width, height)
    )

    can.setFont(
        "Helvetica-Bold",
        font_size
    )

    text_width = can.stringWidth(
        text,
        "Helvetica-Bold",
        font_size
    )

    box_width = text_width + (padding * 2)
    box_height = font_size + (padding * 2)

    # POSITIONING
    if position == "top-left":

        x = margin
        y = height - box_height - margin

    elif position == "top-right":

        x = width - box_width - margin
        y = height - box_height - margin

    elif position == "bottom-left":

        x = margin
        y = margin

    elif position == "bottom-right":

        x = width - box_width - margin
        y = margin

    elif position == "center":

        x = (width - box_width) / 2
        y = (height - box_height) / 2

    else:

        x = margin
        y = height - box_height - margin

    # =====================================
    # SIMULATED OPACITY USING LIGHTER COLORS
    # =====================================

    # Background yellow becomes lighter
    bg_blue = 0.4 + (0.6 * (1 - opacity))

    # Text becomes lighter red
    text_green_blue = opacity * 0.2

    # BACKGROUND
    can.setFillColorRGB(
        1,
        1,
        bg_blue
    )

    can.roundRect(
        x,
        y,
        box_width,
        box_height,
        6,
        fill=1,
        stroke=0
    )

    # TEXT
    can.setFillColorRGB(
        1,
        text_green_blue,
        text_green_blue
    )

    can.drawString(
        x + padding,
        y + padding,
        text
    )

    # BORDER
    can.setStrokeColorRGB(
        1,
        0,
        0
    )

    can.setLineWidth(2)

    can.roundRect(
        x,
        y,
        box_width,
        box_height,
        6,
        fill=0,
        stroke=1
    )

    can.save()

    packet.seek(0)

    return PdfReader(packet)


def process_pdf(
    file,
    name,
    position,
    font_size,
    opacity
):

    reader = PdfReader(file)

    writer = PdfWriter()

    for page in reader.pages:

        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        stamp_pdf = create_stamp(
            text=name,
            width=width,
            height=height,
            position=position,
            font_size=font_size,
            opacity=opacity
        )

        stamp_page = stamp_pdf.pages[0]

        page.merge_page(stamp_page)

        writer.add_page(page)

    return writer


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        position = request.form.get(
            "position",
            "top-left"
        )

        font_size = int(
            request.form.get(
                "font_size",
                20
            )
        )

        opacity = float(
            request.form.get(
                "opacity",
                0.4
            )
        )

        final_writer = PdfWriter()

        for file in files:

            if file.filename == "":
                continue

            name = os.path.splitext(
                file.filename
            )[0]

            processed = process_pdf(
                file=file,
                name=name,
                position=position,
                font_size=font_size,
                opacity=opacity
            )

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

    app.run(debug=True)
