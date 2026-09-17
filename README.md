# Hospital Laboratory Report Integrity Verification Using CRC (Cyclic Redundancy Check)

An educational, full-stack laboratory simulation project for Computer Science, Data Structures, and Computer Networks curricula.

> **ACADEMIC & EDUCATIONAL DISCLAIMER**  
> This software is strictly an **educational simulation** designed for academic demonstrations. It uses exclusively **synthetic / fake patient records** and does **not** connect to any real-world hospital or clinical laboratory information system.

---

## Table of Contents
1. [Project Title & Overview](#project-title--overview)
2. [Problem Statement](#problem-statement)
3. [Project Objectives](#project-objectives)
4. [Features](#features)
5. [Technologies Used](#technologies-used)
6. [System Architecture](#system-architecture)
7. [The CRC Algorithm Explained](#the-crc-algorithm-explained)
8. [Database Design](#database-design)
9. [Project Directory Structure](#project-directory-structure)
10. [Installation & Setup](#installation--setup)
11. [How to Run the Application](#how-to-run-the-application)
12. [How to Run Automated Unit Tests](#how-to-run-automated-unit-tests)
13. [Sample Test Cases & Demonstration Scenarios](#sample-test-cases--demonstration-scenarios)
14. [Expected Results & Output](#expected-results--output)
15. [Limitations](#limitations)
16. [Future Enhancements](#future-enhancements)
17. [University Lab Viva Questions & Model Answers](#university-lab-viva-questions--model-answers)
18. [Conclusion](#conclusion)

---

## 1. Project Title & Overview

**Title:** Hospital Laboratory Report Integrity Verification Using CRC  
**Domain:** Data Structures, Computer Networks, and Telemedicine Data Integrity  
**Level:** Undergraduate University Mini Project (Beginner-Friendly)

In modern Hospital Information Systems (HIS), laboratory analyzers (such as automated blood biochemistry or hematology machines) transmit patient diagnostic reports across internal hospital network backbones to Intensive Care Units (ICU), emergency wards, and doctor workstations.

During transmission across physical cabling, Wi-Fi routers, or serial links, packets are susceptible to:
- Electromagnetic interference (EMI) from hospital equipment (MRI, X-ray machines).
- Network packet drops or buffer overruns.
- Hardware port bit-flips.
- Accidental software truncation.

If a diagnostic parameter is corrupted—for example, if a `Blood Glucose: 95 mg/dL` result is altered to `195 mg/dL`—a doctor might prescribe an improper insulin dose, placing patient health at grave risk.

This project implements a complete, manual, pure-Python **Cyclic Redundancy Check (CRC)** error-detection protocol that guarantees mathematical integrity verification between sender and receiver.

---

## 2. Problem Statement

A hospital diagnostic laboratory transmits synthetic laboratory reports to clinical receiving departments. During simulated network transmission, packets may become corrupted, truncated, altered, or injected with rogue data.

The receiving department must verify whether the incoming diagnostic report is **bit-for-bit identical** to the sender's original transmission before accepting it into the clinical database. If any discrepancy is detected, the report must be rejected and quarantined.

---

## 3. Project Objectives

1. **Manual CRC Implementation:** Implement the CRC algorithm from first principles using pure Python modulo-2 binary long division without relying on black-box third-party libraries.
2. **Inter-Departmental Simulation:** Model the sender department (Pathology/Biochemistry), transmission channel, and receiver department (ICU/Ward).
3. **Channel Noise Simulation:** Provide one-click simulation controls to demonstrate:
   - Clean transmission (No error)
   - Single-character bit error
   - Burst noise (multiple corrupted characters)
   - Clinical result tampering (e.g. 95 → 195)
   - Packet truncation / loss
   - Rogue data append
   - Custom manual payload tampering
4. **Visual Diff Inspection:** Display side-by-side color-coded diffs highlighting altered, deleted, or inserted characters.
5. **Interactive Educational Sandbox:** Provide a step-by-step visual trace showing ASCII conversion, zero padding, polynomial alignment, and bitwise XOR division.
6. **Audit Trail & Dashboard:** Maintain an SQLite database logging all reports and verification attempts with metrics.

---

## 4. Features

- **Dashboard:** Real-time statistics on Total Reports, Total Transmissions, Accepted Reports, and Rejected Reports.
- **Laboratory Report Generator:** Create diagnostic reports with realistic presets (Blood Glucose, Hemoglobin, Serum Creatinine, Cholesterol, WBC).
- **Live CRC Preview:** Calculates the CRC checksum and binary remainder in real-time as the user types.
- **Simulated Transmission Channel:** Interactive radio controls to inject different types of channel noise and visualize payloads before dispatch.
- **Receiver Terminal & Verification Verdict:**
  - `INTEGRITY VERIFIED` / `ACCEPTED` (Clinical Green): Original CRC matches Received CRC.
  - `INTEGRITY CHECK FAILED` / `REJECTED` (Alert Red): Checksum mismatch triggers quarantine banner.
- **Verification History:** Searchable and filterable audit trail of all previous verification attempts.
- **Interactive CRC Step-by-Step Visualizer:** Long division table tracking every XOR operation and running remainder.
- **Security & Data Safety:** Parameterized SQLite queries preventing SQL injection, synthetic data only, no passwords required.

---

## 5. Technologies Used

- **Backend:** Python 3.10+ (Flask 3.x)
- **Algorithm:** Pure Python Manual Modulo-2 Bitwise Division (`crc.py`)
- **Database:** SQLite 3 (Zero configuration, file-based)
- **Frontend:** HTML5, CSS3 (Clinical Medical UI theme), Vanilla JavaScript (ES6)
- **Testing:** Python `unittest` framework

---

## 6. System Architecture

```
+-------------------------------------------------------------------+
|                        SENDER DEPARTMENT                          |
|  - User inputs synthetic laboratory parameters                   |
|  - Payload serialization: "REPORT_ID:LAB-1001|PATIENT:...|..."   |
|  - Modulo-2 Division: Appends r zeros -> Divides by G(x)          |
|  - Checksum Generated: e.g. 0x33F7                                |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                   SIMULATED TRANSMISSION CHANNEL                  |
|  - Clean Transmission (No error)                                  |
|  - Single bit/char flip                                           |
|  - Clinical result alter (95 -> 195)                              |
|  - Packet truncation or rogue append                              |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                       RECEIVING DEPARTMENT                        |
|  - Receives payload over channel                                  |
|  - Recalculates CRC using identical generator polynomial G(x)     |
|  - Compares: Original_CRC == Received_CRC                         |
|      * MATCH    --> "INTEGRITY VERIFIED" (Status = ACCEPTED)     |
|      * MISMATCH --> "INTEGRITY CHECK FAILED" (Status = REJECTED)  |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                 AUDIT TRAIL & SQLITE DATABASE                     |
|  - Stores reports in `laboratory_reports`                         |
|  - Logs verification outcome in `verification_history`            |
+-------------------------------------------------------------------+
```

---

## 7. The CRC Algorithm Explained

### What is CRC?
**Cyclic Redundancy Check (CRC)** is an error-detection code based on polynomial division over the Galois Field $GF(2)$. It treats binary data as polynomial coefficients and divides it by a pre-agreed **Generator Polynomial** $G(x)$.

### Modulo-2 Arithmetic & Why XOR is Used
In standard mathematics, addition and subtraction generate carries and borrows. In modulo-2 arithmetic:
- Addition and subtraction are the exact same operation.
- Both correspond to the **bitwise XOR ($\oplus$)** operator:
  - $0 \oplus 0 = 0$
  - $0 \oplus 1 = 1$
  - $1 \oplus 0 = 1$
  - $1 \oplus 1 = 0$ (No carry!)
Because there is no borrowing or carry propagation, CRC can be computed at lightning speed in hardware shift registers or software loops.

### Supported Generator Polynomials
1. **CRC-16-CCITT** (Degree 16):
   - Polynomial: $x^{16} + x^{12} + x^5 + 1$
   - Divisor Bitstring: `10001000000100001` (17 bits)
   - Hex representation: `0x1021`
   - Guarantees detection of all single-bit errors, all double-bit errors, and all burst errors $\le 16$ bits.
2. **CRC-8-ATM** (Degree 8):
   - Polynomial: $x^8 + x^2 + x + 1$
   - Divisor Bitstring: `100000111` (9 bits)
   - Hex representation: `0x07`

### Step-by-Step CRC Calculation Process
1. **Conversion:** Convert ASCII text string to binary bits (e.g. `'A'` $\rightarrow$ `01000001`).
2. **Zero Padding:** Append $r$ zero bits to the message, where $r$ is the polynomial degree ($r=16$ for CRC-16, $r=8$ for CRC-8). Mathematically, this multiplies the message polynomial $M(x)$ by $2^r$.
3. **Modulo-2 Division:** Slide the generator polynomial across the padded bitstream:
   - If the leading bit is `1`, XOR the divisor with the current window.
   - If the leading bit is `0`, shift by 1 bit to the right.
4. **Remainder Extraction:** The final remainder of length $r$ bits is the CRC checksum.

---

## 8. Database Design

The project uses SQLite (`database/hospital_crc.db`) with two main relational tables:

### Table: `laboratory_reports`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Auto-increment unique key |
| `report_id` | TEXT UNIQUE | Synthetic identifier (e.g. `LAB-1001`) |
| `patient_name` | TEXT | Synthetic patient name |
| `patient_id` | TEXT | Synthetic patient ID (e.g. `SYN-501`) |
| `department` | TEXT | Biochemistry, Hematology, Pathology, etc. |
| `test_name` | TEXT | Diagnostic test name |
| `test_result` | TEXT | Measured value (e.g. `95`) |
| `unit` | TEXT | Measurement unit (e.g. `mg/dL`) |
| `reference_range` | TEXT | Normal diagnostic range (e.g. `70 - 100`) |
| `report_date` | TEXT | Date in `YYYY-MM-DD` format |
| `clinical_notes` | TEXT | Clinical observations |
| `original_data` | TEXT | Canonical serialized payload |
| `original_crc` | TEXT | Calculated CRC in Hex (e.g. `0x33F7`) |
| `crc_polynomial`| TEXT | Polynomial used (e.g. `CRC-16-CCITT`) |
| `created_at` | TIMESTAMP | Record creation timestamp |

### Table: `verification_history`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY | Auto-increment verification audit ID |
| `report_id` | TEXT | Foreign reference to report |
| `patient_name` | TEXT | Patient name |
| `test_name` | TEXT | Diagnostic test name |
| `original_crc` | TEXT | Sender's CRC checksum |
| `received_crc` | TEXT | Receiver's calculated CRC checksum |
| `transmission_type` | TEXT | Simulation mode applied |
| `what_changed` | TEXT | Human-readable explanation of channel mutation |
| `received_data`| TEXT | Full received payload |
| `verification_status`| TEXT | `ACCEPTED` or `REJECTED` |
| `is_corrupted` | INTEGER | `0` (clean) or `1` (corrupted) |
| `created_at` | TIMESTAMP | Verification audit timestamp |

---

## 9. Project Directory Structure

```
hospital_crc_project/
│
├── app.py                  # Flask web controller, routes, simulation engine, diff highlighter
├── crc.py                  # Pure-Python manual Modulo-2 binary long division & CRC calculator
├── database.py             # SQLite database manager & parameterized query layer
├── test_crc.py             # Automated unit & integration tests (19 test cases)
├── requirements.txt        # Python package dependencies (Flask)
├── README.md               # Complete lab documentation & viva guide
│
├── database/
│   └── hospital_crc.db     # SQLite database file (auto-generated & auto-seeded)
│
├── templates/
│   ├── base.html           # Master layout with hospital theme & disclaimer notice
│   ├── index.html          # Dashboard with metrics, report list & verification logs
│   ├── create_report.html  # Sender department: Diagnostic entry & live CRC preview
│   ├── transmit.html       # Channel simulation: Error injection workstation & live diff
│   ├── verify.html         # Receiver department: Verdict banner & CRC comparison
│   ├── history.html        # Verification history audit table
│   ├── crc_demo.html       # Interactive step-by-step Modulo-2 division visualizer
│   └── about.html          # Lab problem description, theory & 15 viva Q&As
│
└── static/
    ├── css/
    │   └── style.css       # Clean medical clinical aesthetic stylesheet
    └── js/
        └── script.js       # Dynamic AJAX simulation preview, presets & real-time CRC
```

---

## 10. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Pip package manager installed.

### Step 1: Open Terminal / PowerShell
Navigate to the project workspace directory:
```powershell
cd "C:\Users\aniln\Desktop\operation system\OS project"
```

### Step 2: Install Required Packages
```powershell
python -m pip install -r requirements.txt
```

---

## 11. How to Run the Application

Execute the Flask application using Python:
```powershell
python app.py
```

You will see output indicating the server is live:
```
======================================================================
 Hospital Laboratory Report Integrity Verification System
 Powered by CRC (Cyclic Redundancy Check) - Python Flask & SQLite
 Server URL: http://127.0.0.1:5000
======================================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Open your web browser (Chrome, Edge, Firefox) and navigate to:
```
http://127.0.0.1:5000
```

---

## 12. How to Run Automated Unit Tests

Run the complete 19-test automated test suite:
```powershell
python -m unittest test_crc.py -v
```

### Expected Output:
```
test_case_1_no_modification_verified (test_crc.TestCRCCalculation.test_case_1_no_modification_verified) ... ok
test_case_2_single_character_corrupted (test_crc.TestCRCCalculation.test_case_2_single_character_corrupted) ... ok
test_case_3_multiple_characters_corrupted (test_crc.TestCRCCalculation.test_case_3_multiple_characters_corrupted) ... ok
test_case_4_data_truncated (test_crc.TestCRCCalculation.test_case_4_data_truncated) ... ok
test_case_5_extra_data_added (test_crc.TestCRCCalculation.test_case_5_extra_data_added) ... ok
test_case_6_clinical_result_altered (test_crc.TestCRCCalculation.test_case_6_clinical_result_altered) ... ok
...
Ran 19 tests in 0.165s
OK
```

---

## 13. Sample Test Cases & Demonstration Scenarios

### Scenario A: Clean Transmission (Report Accepted)
1. Navigate to **➕ Create Report**.
2. Select preset **Blood Glucose (95 mg/dL)**. Click **Generate CRC & Store Report**.
3. On the **Simulate Channel** page, select **🟢 Send Without Error (Clean Channel)**.
4. Click **🚀 Transmit to Receiving Department**.
5. **Observed Result:**
   - Original CRC: `0x33F7`
   - Received CRC: `0x33F7`
   - Verdict: **✅ INTEGRITY VERIFIED**
   - Status: **ACCEPTED**

### Scenario B: Medical Risk Scenario (Test Result Alteration)
1. On the **Simulate Channel** page, select **🚨 Alter Clinical Test Result (High Risk)**.
2. Notice the live diff changes `RESULT:95` $\rightarrow$ `RESULT:195`.
3. Click **Transmit to Receiving Department**.
4. **Observed Result:**
   - Original CRC: `0x33F7`
   - Received CRC: Diverges completely (e.g. `0x1B82`)
   - Verdict: **🚨 INTEGRITY CHECK FAILED**
   - Status: **REJECTED**
   - Alert: Report is quarantined to prevent improper insulin dosage!

### Scenario C: Packet Truncation (Data Cutoff)
1. Select **✂️ Truncate / Drop Packet Data**.
2. Notice the last 30% of characters are dropped.
3. Click **Transmit**.
4. **Observed Result:** CRC mismatch, packet rejected immediately.

### Scenario D: Interactive Step-by-Step Trace
1. Navigate to **🔬 CRC Visualizer**.
2. Enter `"LAB95"` with polynomial **CRC-8**.
3. Click **Compute Trace**.
4. Review the ASCII table, padded binary dividend, and the full step-by-step XOR long division trace table.

---

## 14. Expected Results & Output Summary

| Transmission Condition | Original CRC | Received CRC | CRC Comparison | System Verdict | Clinical Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **No Error (Intact)** | `0x33F7` | `0x33F7` | Match (`==`) | `INTEGRITY VERIFIED` | Accepted & Approved |
| **Single Char Corrupted** | `0x33F7` | `0xD1A4` | Mismatch (`!=`) | `INTEGRITY CHECK FAILED` | Rejected & Quarantined |
| **Result Altered (95->195)**| `0x33F7` | `0x1B82` | Mismatch (`!=`) | `INTEGRITY CHECK FAILED` | Rejected & Quarantined |
| **Data Truncated** | `0x33F7` | `0x7C09` | Mismatch (`!=`) | `INTEGRITY CHECK FAILED` | Rejected & Quarantined |
| **Rogue Data Appended** | `0x33F7` | `0x94EF` | Mismatch (`!=`) | `INTEGRITY CHECK FAILED` | Rejected & Quarantined |

---

## 15. Limitations

1. **Error Detection Only:** CRC indicates *whether* an error occurred, not *which* bit flipped. It cannot correct errors automatically.
2. **Not Cryptographically Secure:** An active malicious attacker who intercepts the network could modify the payload and recalculate a matching CRC. For adversarial security, cryptographic message authentication codes (HMAC or digital signatures) are required.
3. **Simulated Networking:** The transmission channel is simulated in software on the local host rather than over physical serial wires or Ethernet hardware.

---

## 16. Future Enhancements

1. **Automatic Repeat Request (ARQ):** Implement Stop-and-Wait or Go-Back-N ARQ to automatically request retransmission when CRC check fails.
2. **Cryptographic Authentication:** Add HMAC-SHA256 signatures to prevent intentional man-in-the-middle tampering.
3. **HL7 / FHIR Standard Compliance:** Format serialized diagnostic reports in HL7 v2.x or FHIR JSON medical telemetry formats.
4. **Forward Error Correction (FEC):** Combine CRC detection with Hamming codes or Reed-Solomon codes to automatically correct 1-bit or 2-bit flips without retransmission.

---

## 17. University Lab Viva Questions & Model Answers

### Q1: What is Cyclic Redundancy Check (CRC)?
**Answer:** CRC is an error-detecting code based on polynomial modulo-2 binary division. It treats input data as coefficients of a polynomial, divides it by a standardized generator polynomial $G(x)$, and appends the division remainder as a checksum.

### Q2: Why is CRC preferred over a simple Parity Bit or Arithmetic Checksum?
**Answer:** A simple parity bit cannot detect an even number of bit errors (e.g., 2 flipped bits). Arithmetic checksums can fail to detect swapped bytes or compensating errors (+1 in one byte and -1 in another). CRC detects all single and double bit errors, all odd numbers of bit errors, and 100% of burst errors up to the degree of the polynomial.

### Q3: What is Modulo-2 Arithmetic?
**Answer:** Modulo-2 arithmetic is binary arithmetic performed on individual bit positions without carries or borrows. Addition and subtraction are identical and equivalent to the bitwise XOR ($\oplus$) operator ($1 \oplus 1 = 0$, $1 \oplus 0 = 1$, $0 \oplus 1 = 1$, $0 \oplus 0 = 0$).

### Q4: What is the significance of the Generator Polynomial $G(x)$?
**Answer:** $G(x)$ is the predetermined divisor polynomial agreed upon by both sender and receiver. The degree of $G(x)$ determines the number of bits in the CRC checksum. Standard polynomials (like CRC-16-CCITT: $x^{16} + x^{12} + x^5 + 1$) are mathematically designed to maximize burst error detection.

### Q5: Can CRC perform error correction?
**Answer:** No. Standard CRC is strictly an **error-detection** mechanism. It detects if data was corrupted, but does not reconstruct the lost data. Upon detecting corruption, the receiving system rejects the packet and requests retransmission.

### Q6: Why do we append $r$ zero bits to the message before division?
**Answer:** Appending $r$ zeros shifts the message to the left by $r$ bit positions ($M(x) \cdot 2^r$), reserving an $r$-bit space at the end of the packet to store the calculated remainder.

### Q7: What is a burst error and how does CRC handle it?
**Answer:** A burst error is a contiguous series of bits where the first and last bits are corrupted, often caused by lightning or electrical noise spikes. A CRC of degree $r$ detects 100% of all burst errors of length $\le r$.

### Q8: How does the application protect against SQL Injection?
**Answer:** All database operations in `database.py` use SQLite parameterized queries with placeholders (`?`) instead of string formatting, ensuring inputs are treated strictly as data values.

---

## 18. Conclusion

The **Hospital Laboratory Report Integrity Verification System** demonstrates how Cyclic Redundancy Check (CRC) mathematically guarantees data integrity in healthcare telemetry. By implementing the bitwise modulo-2 division from scratch in Python, providing realistic error simulation modes, and delivering an intuitive clinical web interface, the project provides a comprehensive, hands-on demonstration suitable for university laboratory examinations and viva presentations.
