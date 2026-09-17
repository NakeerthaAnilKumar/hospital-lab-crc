"""
=============================================================================
Automated Test Suite for CRC Laboratory Integrity Verification System
=============================================================================
Author: Educational Lab Project
Framework: Python unittest
Covers:
  - CRC Calculation (Manual Modulo-2 Bitwise Division)
  - Test Case 1: Clean transmission (No error -> CRC match -> VERIFIED)
  - Test Case 2: Single character alteration -> CRC mismatch -> CORRUPTED
  - Test Case 3: Multiple characters altered -> CRC mismatch -> CORRUPTED
  - Test Case 4: Data truncated -> CRC mismatch -> CORRUPTED
  - Test Case 5: Extra data appended -> CRC mismatch -> CORRUPTED
  - Test Case 6: Clinical Test Result altered (95 -> 195) -> CORRUPTED
  - Edge Cases: Empty string, special characters, boundary conditions
  - Database Integrity: Insertion, duplicate rejection, verification logging
  - Flask Web Routes: End-to-end HTTP endpoint checks
=============================================================================
"""

import unittest
import os
import json
import sqlite3

# Import application modules
import crc
import database
from app import app, simulate_corruption


class TestCRCCalculation(unittest.TestCase):
    """Unit tests for the manual CRC algorithm implementation in crc.py."""

    def setUp(self):
        self.sample_report = (
            "REPORT_ID:LAB001|PATIENT:Anil Kumar|PAT_ID:PID-9821|"
            "DEPT:Biochemistry|TEST:Blood Glucose|RESULT:95|UNIT:mg/dL|RANGE:70-100|DATE:2026-09-16"
        )

    def test_crc_determinism(self):
        """Test that calculating CRC on identical data produces identical checksums."""
        res1 = crc.calculate_crc(self.sample_report, "CRC-16")
        res2 = crc.calculate_crc(self.sample_report, "CRC-16")
        self.assertEqual(res1["crc_hex"], res2["crc_hex"])
        self.assertEqual(res1["crc_binary"], res2["crc_binary"])
        self.assertEqual(len(res1["crc_binary"]), 16)

    def test_case_1_no_modification_verified(self):
        """
        Test Case 1:
        No modification -> CRC matches -> INTEGRITY VERIFIED (ACCEPTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, _ = simulate_corruption(self.sample_report, "none")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertEqual(self.sample_report, transmitted_data)
        self.assertEqual(original_crc, received_crc)

    def test_case_2_single_character_corrupted(self):
        """
        Test Case 2:
        One character changed -> CRC differs -> INTEGRITY CHECK FAILED (CORRUPTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, desc = simulate_corruption(self.sample_report, "single_char")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertNotEqual(self.sample_report, transmitted_data)
        self.assertNotEqual(original_crc, received_crc)
        self.assertIn("Single Character", desc)

    def test_case_3_multiple_characters_corrupted(self):
        """
        Test Case 3:
        Multiple characters changed -> CRC differs -> INTEGRITY CHECK FAILED (CORRUPTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, desc = simulate_corruption(self.sample_report, "multi_char")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertNotEqual(self.sample_report, transmitted_data)
        self.assertNotEqual(original_crc, received_crc)
        self.assertIn("Burst", desc)

    def test_case_4_data_truncated(self):
        """
        Test Case 4:
        Data truncated -> CRC differs -> INTEGRITY CHECK FAILED (CORRUPTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, desc = simulate_corruption(self.sample_report, "truncate")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertLess(len(transmitted_data), len(self.sample_report))
        self.assertNotEqual(original_crc, received_crc)
        self.assertIn("Truncation", desc)

    def test_case_5_extra_data_added(self):
        """
        Test Case 5:
        Extra data added -> CRC differs -> INTEGRITY CHECK FAILED (CORRUPTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, desc = simulate_corruption(self.sample_report, "append")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertGreater(len(transmitted_data), len(self.sample_report))
        self.assertNotEqual(original_crc, received_crc)
        self.assertIn("Extraneous", desc)

    def test_case_6_clinical_result_altered(self):
        """
        Test Case 6 (Medical Risk Scenario):
        Test Result altered: 95 -> 195 -> CRC differs -> INTEGRITY CHECK FAILED (REJECTED)
        """
        original_crc = crc.calculate_crc(self.sample_report, "CRC-16")["crc_hex"]
        transmitted_data, desc = simulate_corruption(self.sample_report, "change_result")
        received_crc = crc.calculate_crc(transmitted_data, "CRC-16")["crc_hex"]

        self.assertIn("RESULT:195", transmitted_data)
        self.assertNotEqual(original_crc, received_crc)
        self.assertIn("Clinical Value Altered", desc)

    def test_crc_8_implementation(self):
        """Test that CRC-8 yields an 8-bit remainder."""
        res8 = crc.calculate_crc("LAB95", "CRC-8")
        self.assertEqual(len(res8["crc_binary"]), 8)
        self.assertTrue(res8["crc_hex"].startswith("0x"))

    def test_crc_step_trace(self):
        """Test step-by-step division trace generator for visualizer."""
        trace = crc.get_crc_step_trace("TEST", "CRC-8", max_steps=10)
        self.assertIn("steps", trace)
        self.assertGreater(len(trace["steps"]), 0)
        self.assertEqual(trace["degree"], 8)
        self.assertEqual(len(trace["final_remainder_bits"]), 8)

    def test_edge_cases(self):
        """Test empty string and boundary inputs."""
        empty_res = crc.calculate_crc("", "CRC-16")
        self.assertIsNotNone(empty_res["crc_hex"])
        self.assertEqual(len(empty_res["crc_binary"]), 16)

        special_res = crc.calculate_crc("@#$%^&*()_+~`|}{[]:;?><,./", "CRC-16")
        self.assertIsNotNone(special_res["crc_hex"])


class TestDatabaseOperations(unittest.TestCase):
    """Unit tests for SQLite database operations in database.py."""

    def setUp(self):
        database.init_db()

    def test_insert_and_retrieve_report(self):
        """Test inserting a new laboratory report and retrieving it."""
        unique_id = "TEST-LAB-999"
        payload = database.serialize_report_data(
            unique_id, "Test Patient", "PID-999", "Biochemistry",
            "Serum Test", "100", "mg/dL", "80-120", "2026-09-16"
        )
        crc_val = crc.calculate_crc(payload, "CRC-16")["crc_hex"]

        report_data = {
            "report_id": unique_id,
            "patient_name": "Test Patient",
            "patient_id": "PID-999",
            "department": "Biochemistry",
            "test_name": "Serum Test",
            "test_result": "100",
            "unit": "mg/dL",
            "reference_range": "80-120",
            "report_date": "2026-09-16",
            "clinical_notes": "Automated unit test note.",
            "original_data": payload,
            "original_crc": crc_val,
            "crc_polynomial": "CRC-16-CCITT"
        }

        # Clean up any leftover
        database.delete_report(unique_id)

        # Insert
        success = database.insert_report(report_data)
        self.assertTrue(success)

        # Retrieve
        fetched = database.get_report_by_id(unique_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["report_id"], unique_id)
        self.assertEqual(fetched["original_crc"], crc_val)

        # Duplicate insertion should fail safely
        dup_success = database.insert_report(report_data)
        self.assertFalse(dup_success)

        # Cleanup
        database.delete_report(unique_id)

    def test_verification_logging(self):
        """Test logging verification outcomes to SQLite history."""
        v_record = {
            "report_id": "TEST-V-001",
            "patient_name": "Audit Patient",
            "test_name": "HbA1c",
            "original_crc": "0xABCD",
            "received_crc": "0xABCD",
            "transmission_type": "No Error",
            "what_changed": "None",
            "received_data": "REPORT_ID:TEST-V-001",
            "verification_status": "ACCEPTED",
            "is_corrupted": 0
        }
        v_id = database.insert_verification(v_record)
        self.assertIsInstance(v_id, int)
        self.assertGreater(v_id, 0)

        record = database.get_verification_by_id(v_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["verification_status"], "ACCEPTED")


class TestFlaskRoutes(unittest.TestCase):
    """Integration tests for web application HTTP routes and APIs."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard_page(self):
        """Test that the Dashboard (index) loads successfully."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Hospital Pathology & Biochemistry System", res.data)

    def test_create_report_page(self):
        """Test that the Create Report page loads."""
        res = self.client.get("/create-report")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Create Laboratory Report", res.data)

    def test_transmit_page(self):
        """Test that the Transmit page loads."""
        res = self.client.get("/transmit")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Simulated Transmission Channel", res.data)

    def test_crc_demo_page(self):
        """Test that the visual CRC demo page loads and computes trace."""
        res = self.client.get("/crc-demo")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CRC Mathematical Visualizer", res.data)

    def test_history_page(self):
        """Test that the History page loads."""
        res = self.client.get("/history")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Verification History", res.data)

    def test_about_page(self):
        """Test that the About & Viva Guide page loads."""
        res = self.client.get("/about")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"University Lab Viva Questions & Model Answers", res.data)

    def test_api_simulate_channel(self):
        """Test the AJAX simulation endpoint."""
        payload = {
            "original_data": "REPORT_ID:TEST|RESULT:95",
            "mode": "change_result",
            "poly_type": "CRC-16"
        }
        res = self.client.post("/api/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("RESULT:195", data["received_data"])
        self.assertTrue(data["received_crc"].startswith("0x"))


if __name__ == "__main__":
    unittest.main()
