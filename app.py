"""
DefinitelyNotRockYou - app.py
Localhost web UI:
  1. Upload / paste a filled-in OSINT template (osint_template.txt format)
  2. Generates a personalized password wordlist
  3. Download the wordlist, or immediately test-crack a zip file with it

Run with:  python app.py
Then open: http://127.0.0.1:5000

ETHICS: Only use on data/files you own or are explicitly authorized to test.
"""

import os
import tempfile
from flask import Flask, request, render_template, send_file, redirect, url_for, flash

from generator import parse_osint_file, generate_and_save, FIELD_GROUPS, fields_from_form
from cracker import crack_zip

app = Flask(__name__)
app.secret_key = "dev-only-not-for-production"

WORKDIR = tempfile.mkdtemp(prefix="dnry_")
WORDLIST_PATH = os.path.join(WORKDIR, "wordlist.txt")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", field_groups=FIELD_GROUPS)


SIZE_PRESETS = {
    "quick": 50000,
    "standard": 150000,
    "thorough": 400000,
    "maximum": 800000,
}


@app.route("/generate", methods=["POST"])
def generate():
    input_mode = request.form.get("input_mode", "upload")
    size_preset = request.form.get("wordlist_size", "standard")
    max_size = SIZE_PRESETS.get(size_preset, 150000)
    fields = {}

    if input_mode == "form":
        fields = fields_from_form(request.form)
        if not fields:
            flash("The form's empty - fill in at least a couple of fields, or switch to upload/paste.")
            return redirect(url_for("index"))
    else:
        text_data = request.form.get("osint_text", "").strip()
        uploaded_file = request.files.get("osint_file")

        lines = []
        if uploaded_file and uploaded_file.filename:
            lines = uploaded_file.read().decode("utf-8", errors="ignore").splitlines()
        elif text_data:
            lines = text_data.splitlines()
        else:
            flash("Please upload a file or paste OSINT data first.")
            return redirect(url_for("index"))

        fields = parse_osint_file(lines)
        if not fields:
            flash("No usable fields found - check your template formatting.")
            return redirect(url_for("index"))

    count = generate_and_save(fields, WORDLIST_PATH, max_size=max_size)

    preview = []
    with open(WORDLIST_PATH, "r", encoding="utf-8") as f:
        for _ in range(25):
            line = f.readline()
            if not line:
                break
            preview.append(line.strip())

    return render_template(
        "index.html",
        field_groups=FIELD_GROUPS,
        generated=True,
        count=count,
        preview=preview,
        fields_used=sorted(fields.keys()),
    )


@app.route("/download")
def download():
    if not os.path.exists(WORDLIST_PATH):
        flash("No wordlist generated yet.")
        return redirect(url_for("index"))
    return send_file(WORDLIST_PATH, as_attachment=True, download_name="dnry_wordlist.txt")


@app.route("/crack", methods=["POST"])
def crack():
    if not os.path.exists(WORDLIST_PATH):
        flash("Generate a wordlist first before cracking.")
        return redirect(url_for("index"))

    zip_file = request.files.get("zip_file")
    if not zip_file or not zip_file.filename:
        flash("Please upload a zip file to test.")
        return redirect(url_for("index"))

    zip_path = os.path.join(WORKDIR, "target.zip")
    zip_file.save(zip_path)

    try:
        found, password, attempts = crack_zip(zip_path, WORDLIST_PATH)
    except RuntimeError as e:
        flash(str(e))
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        field_groups=FIELD_GROUPS,
        cracked=True,
        found=found,
        password=password,
        attempts=attempts,
    )


if __name__ == "__main__":
    print("=" * 60)
    print(" DefinitelyNotRockYou running at http://127.0.0.1:5000")
    print(" For authorized security testing / your own files only.")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
