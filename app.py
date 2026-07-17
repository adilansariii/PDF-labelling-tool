from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

import io
import os
import re
import json
from datetime import datetime

app = Flask(__name__)



def clean_label(filename):
    name = os.path.splitext(filename)[0]

    name = re.sub(r"[_\-]+", " ", name)

    name = re.sub(
        r"\b(final|copy|v\d+)\b",
        "",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(r"\s+", " ", name)

    return name.strip()


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

    try:
        can.setFillAlpha(opacity)
        can.setStrokeAlpha(opacity)
    except Exception:
        pass

    # Background
    can.setFillColorRGB(
        1,
        1,
        0.8
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

    # Text
    can.setFillColorRGB(
        1,
        0,
        0
    )

    can.drawString(
        x + padding,
        y + padding,
        text
    )

    # Border
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

        # Blank label = no stamp
        if not name:

            writer.add_page(page)

            continue

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

        page.merge_page(
            stamp_pdf.pages[0]
        )

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

        order_json = request.form.get(
            "file_order",
            "[]"
        )

        try:
            order = json.loads(order_json)
        except Exception:
            order = []

        final_writer = PdfWriter()

        ordered_files = []

        # Reordered PDFs + labels stay linked
        for item in order:

            idx = item.get("index")

            label = item.get(
                "label",
                ""
            ).strip()

            if idx is None:
                continue

            if idx >= len(files):
                continue

            file = files[idx]

            ordered_files.append(
                (
                    file,
                    label
                )
            )

        # Fallback
        if not ordered_files:

            for file in files:

                ordered_files.append(
                    (
                        file,
                        clean_label(
                            file.filename
                        )
                    )
                )

        # Process PDFs
        for file, label in ordered_files:

            if file.filename == "":
                continue

            processed = process_pdf(
                file=file,
                name=label,
                position=position,
                font_size=font_size,
                opacity=opacity
            )

            for page in processed.pages:
                final_writer.add_page(page)

        output = io.BytesIO()

        final_writer.write(output)

        output.seek(0)

        filename = (
            "Freespace_Labelled_PDF_"
            + datetime.now().strftime("%Y-%m-%d")
            + ".pdf"
        )

        return send_file(
            output,
            download_name=filename,
            as_attachment=True
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
