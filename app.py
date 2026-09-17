"""
=============================================================================
Flask Web Application
Hospital Laboratory Report Integrity Verification Using CRC
=============================================================================
Author: Educational Lab Project
Framework: Flask 3.x (Python)
Database: SQLite3
Purpose: Demonstrates CRC-based error detection and data integrity verification
         between hospital laboratory sender and clinical receiving department.
=============================================================================
"""

import os
import random
import difflib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

import database
import crc

# Initialize Flask application
app = Flask(__name__)
app.secret_key = "hospital-crc-lab-simulation-key-secret-educational"

# Custom template filters
@app.template_filter("ord")
def jinja_ord(char):
    """Returns ASCII code for a character."""
    return ord(char) if char else 0

# Ensure database is initialized on launch
database.init_db()


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS: Data Formatting & Corruption Simulation
# -----------------------------------------------------------------------------

def simulate_corruption(original_data: str, mode: str, custom_text: str = None) -> tuple[str, str]:
    """
    Simulates transmission channel effects on the serialized report string.
    
    Modes:
      - 'none': Intact transmission
      - 'single_char': Single character flip/modification
      - 'multi_char': Multiple characters flipped
      - 'change_result': Alters the numeric clinical test result (e.g., 95 -> 195)
      - 'truncate': Packet truncated prematurely
      - 'append': Rogue data appended
      - 'custom': User-specified manual edit
      
    Returns:
      (received_data, explanation_of_change)
    """
    if mode == "none":
        return original_data, "No transmission errors. Report payload transmitted cleanly through channel."

    if mode == "custom" and custom_text is not None:
        return custom_text, "Manual modifications applied to the laboratory report payload."

    if mode == "change_result":
        # Look for RESULT:<value> in the serialized payload
        if "RESULT:" in original_data:
            parts = original_data.split("RESULT:")
            post = parts[1]
            next_pipe = post.find("|")
            if next_pipe != -1:
                old_val = post[:next_pipe]
                remainder = post[next_pipe:]
            else:
                old_val = post
                remainder = ""

            # Modify the result
            if old_val.isdigit():
                new_val = str(int(old_val) + 100)
            elif old_val.replace(".", "", 1).isdigit():
                new_val = f"{float(old_val) * 2.5:.1f}"
            else:
                new_val = "CRITICAL_HIGH"

            modified_data = f"{parts[0]}RESULT:{new_val}{remainder}"
            return modified_data, f"Clinical Value Altered: Test result '{old_val}' modified to '{new_val}' during transmission."
        else:
            mode = "single_char"  # fallback

    if mode == "single_char":
        if not original_data:
            return original_data, "Empty data."
        # Pick an index in the middle of data to corrupt
        idx = random.randint(len(original_data) // 4, 3 * len(original_data) // 4)
        orig_char = original_data[idx]
        new_char = chr(ord(orig_char) ^ 1) if orig_char.isalnum() else "X"
        if new_char == orig_char:
            new_char = "Z"
        modified_data = original_data[:idx] + new_char + original_data[idx + 1:]
        return modified_data, f"Single Character Error: Character '{orig_char}' at index {idx} corrupted to '{new_char}'."

    if mode == "multi_char":
        if len(original_data) < 5:
            return original_data + "X", "Short data modified."
        chars = list(original_data)
        # Corrupt 3-5 random positions
        count = min(4, len(chars))
        indices = random.sample(range(len(chars)), count)
        for idx in sorted(indices):
            chars[idx] = "#" if chars[idx] != "#" else "@"
        modified_data = "".join(chars)
        return modified_data, f"Burst Noise Error: {count} random characters corrupted at positions {sorted(indices)}."

    if mode == "truncate":
        cut_point = int(len(original_data) * 0.70)
        modified_data = original_data[:cut_point]
        lost_bytes = len(original_data) - cut_point
        return modified_data, f"Packet Truncation: Transmission cut short. Last {lost_bytes} characters were dropped/lost."

    if mode == "append":
        rogue_str = "|CORRUPT_PACKET_OVERFLOW_0xDEADBEEF"
        modified_data = original_data + rogue_str
        return modified_data, f"Extraneous Data Injected: Rogue string '{rogue_str}' appended to payload."

    # Default fallback
    return original_data, "No change."


def generate_diff_html(original: str, modified: str) -> str:
    """
    Produces HTML visualizing differences between original and modified strings
    using color highlights (red for removed/changed, green for added).
    """
    matcher = difflib.SequenceMatcher(None, original, modified)
    html_parts = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            html_parts.append(f"<span class='diff-equal'>{modified[j1:j2]}</span>")
        elif tag == "replace":
            html_parts.append(
                f"<span class='diff-delete' title='Original: {original[i1:i2]}'>{original[i1:i2]}</span>"
                f"<span class='diff-insert' title='Received: {modified[j1:j2]}'>{modified[j1:j2]}</span>"
            )
        elif tag == "delete":
            html_parts.append(f"<span class='diff-delete' title='Deleted: {original[i1:i2]}'>{original[i1:i2]}</span>")
        elif tag == "insert":
            html_parts.append(f"<span class='diff-insert' title='Added: {modified[j1:j2]}'>{modified[j1:j2]}</span>")
            
    return "".join(html_parts)


# -----------------------------------------------------------------------------
# APPLICATION ROUTES
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Dashboard page showing system overview, stats, recent reports & verifications.
    """
    stats = database.get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/create-report", methods=["GET", "POST"])
def create_report():
    """
    Sender Department: Form to input synthetic laboratory report data,
    generate CRC checksum, and save into SQLite database.
    """
    if request.method == "POST":
        report_id = request.form.get("report_id", "").strip().upper()
        patient_name = request.form.get("patient_name", "").strip()
        patient_id = request.form.get("patient_id", "").strip().upper()
        department = request.form.get("department", "").strip()
        test_name = request.form.get("test_name", "").strip()
        test_result = request.form.get("test_result", "").strip()
        unit = request.form.get("unit", "").strip()
        reference_range = request.form.get("reference_range", "").strip()
        report_date = request.form.get("report_date", "").strip()
        clinical_notes = request.form.get("clinical_notes", "").strip()
        poly_type = request.form.get("poly_type", "CRC-16")

        # Validation
        if not (report_id and patient_name and patient_id and department and test_name and test_result):
            flash("All essential report fields must be filled.", "danger")
            return render_template("create_report.html", form_data=request.form)

        # Check for duplicate report ID
        if database.get_report_by_id(report_id):
            flash(f"Report ID '{report_id}' already exists! Please use a unique ID.", "warning")
            return render_template("create_report.html", form_data=request.form)

        # Serialize payload
        payload = database.serialize_report_data(
            report_id, patient_name, patient_id, department,
            test_name, test_result, unit, reference_range, report_date
        )

        # Calculate CRC
        crc_data = crc.calculate_crc(payload, poly_type)

        # Save to database
        new_report = {
            "report_id": report_id,
            "patient_name": patient_name,
            "patient_id": patient_id,
            "department": department,
            "test_name": test_name,
            "test_result": test_result,
            "unit": unit,
            "reference_range": reference_range,
            "report_date": report_date or datetime.now().strftime("%Y-%m-%d"),
            "clinical_notes": clinical_notes,
            "original_data": payload,
            "original_crc": crc_data["crc_hex"],
            "crc_polynomial": crc_data["polynomial"]
        }

        success = database.insert_report(new_report)
        if success:
            flash(f"Report {report_id} successfully created with CRC {crc_data['crc_hex']}!", "success")
            return redirect(url_for("transmit", report_id=report_id))
        else:
            flash("Error saving report to database. Please check values.", "danger")
            return render_template("create_report.html", form_data=request.form)

    # GET request - generate new suggested report ID
    all_reports = database.get_all_reports()
    next_num = len(all_reports) + 1001
    suggested_id = f"LAB-{next_num}"
    suggested_pid = f"SYN-{random.randint(100, 999)}"
    today_date = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "create_report.html",
        suggested_id=suggested_id,
        suggested_pid=suggested_pid,
        today_date=today_date
    )


@app.route("/transmit")
@app.route("/transmit/<report_id>")
def transmit(report_id=None):
    """
    Simulation Channel: Allows user to pick a report and simulate various transmission
    channel conditions (no error, single char corrupt, test result alter, truncate, append).
    """
    all_reports = database.get_all_reports()
    selected_report = None

    if report_id:
        selected_report = database.get_report_by_id(report_id)
    elif all_reports:
        selected_report = all_reports[0]

    return render_template(
        "transmit.html",
        all_reports=all_reports,
        selected_report=selected_report
    )


@app.route("/verify", methods=["POST"])
def verify():
    """
    Receiving Department: Recalculates CRC on the received data, compares
    it with the original CRC, and renders the verification verdict.
    """
    report_id = request.form.get("report_id")
    received_data = request.form.get("received_data", "")
    transmission_type = request.form.get("transmission_type", "Manual Transmission")
    what_changed = request.form.get("what_changed", "Not specified")

    report = database.get_report_by_id(report_id)
    if not report:
        flash(f"Report '{report_id}' not found!", "danger")
        return redirect(url_for("index"))

    original_crc = report["original_crc"]
    poly_name = report.get("crc_polynomial", "CRC-16-CCITT")
    poly_type = "CRC-8" if "8" in poly_name else "CRC-16"

    # Receiver recalculates CRC on the received data
    received_crc_info = crc.calculate_crc(received_data, poly_type)
    received_crc = received_crc_info["crc_hex"]

    # Integrity verification comparison
    is_intact = (original_crc.strip().upper() == received_crc.strip().upper())
    verification_status = "ACCEPTED" if is_intact else "REJECTED"
    is_corrupted = not is_intact

    # Log attempt in SQLite history
    verif_record = {
        "report_id": report_id,
        "patient_name": report["patient_name"],
        "test_name": report["test_name"],
        "original_crc": original_crc,
        "received_crc": received_crc,
        "transmission_type": transmission_type,
        "what_changed": what_changed,
        "received_data": received_data,
        "verification_status": verification_status,
        "is_corrupted": is_corrupted
    }
    v_id = database.insert_verification(verif_record)

    # Generate visual HTML diff between original and received strings
    diff_html = generate_diff_html(report["original_data"], received_data)

    return render_template(
        "verify.html",
        report=report,
        received_data=received_data,
        original_crc=original_crc,
        received_crc=received_crc,
        received_crc_binary=received_crc_info["crc_binary"],
        original_crc_binary=crc.calculate_crc(report["original_data"], poly_type)["crc_binary"],
        verification_status=verification_status,
        is_intact=is_intact,
        transmission_type=transmission_type,
        what_changed=what_changed,
        diff_html=diff_html,
        verification_id=v_id,
        poly_type=poly_type
    )


@app.route("/verify/<int:v_id>")
def view_verification(v_id):
    """
    View a previously saved verification record from history.
    """
    record = database.get_verification_by_id(v_id)
    if not record:
        flash("Verification record not found.", "warning")
        return redirect(url_for("history"))

    report = database.get_report_by_id(record["report_id"])
    original_data = report["original_data"] if report else "Original data unavailable"
    diff_html = generate_diff_html(original_data, record["received_data"])

    return render_template(
        "verify.html",
        report=report or {"report_id": record["report_id"], "patient_name": record["patient_name"], "test_name": record["test_name"], "original_data": original_data},
        received_data=record["received_data"],
        original_crc=record["original_crc"],
        received_crc=record["received_crc"],
        received_crc_binary="N/A",
        original_crc_binary="N/A",
        verification_status=record["verification_status"],
        is_intact=(record["verification_status"] == "ACCEPTED"),
        transmission_type=record["transmission_type"],
        what_changed=record["what_changed"],
        diff_html=diff_html,
        verification_id=record["id"],
        poly_type="CRC-16",
        from_history=True
    )


@app.route("/history")
def history():
    """
    Displays the log of all past simulated transmissions and verification outcomes.
    """
    filter_status = request.args.get("status", "all")
    history_records = database.get_verification_history(limit=100)

    if filter_status == "accepted":
        history_records = [r for r in history_records if r["verification_status"] == "ACCEPTED"]
    elif filter_status == "rejected":
        history_records = [r for r in history_records if r["verification_status"] == "REJECTED"]

    return render_template("history.html", history=history_records, filter_status=filter_status)


@app.route("/history/clear", methods=["POST"])
def clear_history():
    """
    Utility action to clear verification logs for fresh lab demonstrations.
    """
    database.clear_all_history()
    flash("Verification history cleared successfully.", "info")
    return redirect(url_for("history"))


@app.route("/crc-demo", methods=["GET", "POST"])
def crc_demo():
    """
    Interactive visual CRC demonstration sandbox.
    Shows bit-by-bit modulo-2 binary long division with XOR steps.
    """
    sample_text = "LAB95"
    poly_choice = "CRC-8"

    if request.method == "POST":
        sample_text = request.form.get("sample_text", "LAB95").strip() or "LAB95"
        poly_choice = request.form.get("poly_choice", "CRC-8")

    trace_data = crc.get_crc_step_trace(sample_text, poly_choice, max_steps=25)
    full_crc = crc.calculate_crc(sample_text, poly_choice)

    return render_template(
        "crc_demo.html",
        sample_text=sample_text,
        poly_choice=poly_choice,
        trace=trace_data,
        full_crc=full_crc
    )


@app.route("/about")
def about():
    """
    Academic documentation, CRC theory, system architecture,
    and university lab viva Q&A guide.
    """
    return render_template("about.html")


# -----------------------------------------------------------------------------
# REST API ENDPOINTS (For responsive dynamic UI & real-time simulation)
# -----------------------------------------------------------------------------

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    """
    API called asynchronously by frontend to simulate transmission mutations
    and calculate live received CRC and visual diff preview.
    """
    req_json = request.get_json() or {}
    original_data = req_json.get("original_data", "")
    mode = req_json.get("mode", "none")
    custom_text = req_json.get("custom_text")
    poly_type = req_json.get("poly_type", "CRC-16")

    received_data, explanation = simulate_corruption(original_data, mode, custom_text)
    crc_info = crc.calculate_crc(received_data, poly_type)
    diff_html = generate_diff_html(original_data, received_data)

    return jsonify({
        "success": True,
        "mode": mode,
        "received_data": received_data,
        "explanation": explanation,
        "received_crc": crc_info["crc_hex"],
        "received_crc_binary": crc_info["crc_binary"],
        "diff_html": diff_html
    })


@app.route("/api/calculate-crc", methods=["POST"])
def api_calculate_crc():
    """
    API for calculating CRC dynamically from arbitrary user text.
    """
    req_json = request.get_json() or {}
    text = req_json.get("text", "")
    poly = req_json.get("polynomial", "CRC-16")
    res = crc.calculate_crc(text, poly)
    return jsonify(res)


# -----------------------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Host on 127.0.0.1 (localhost) on port 5000
    print("=" * 70)
    print(" Hospital Laboratory Report Integrity Verification System")
    print(" Powered by CRC (Cyclic Redundancy Check) - Python Flask & SQLite")
    print(" Server URL: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=True)
