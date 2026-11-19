import os
import unittest
import pandas as pd
from app.models.db import init_db, get_dataset, get_records_metadata, get_audit_trail
from app.services.profiling import analyze_dataset_pipeline
from app.services.reconciliation import reconcile_fixed_dataset
from app.api.endpoints import upload_dataset
from app.utils.helpers import generate_serial

class TestDataFixPipeline(unittest.TestCase):
    def setUp(self):
        init_db()
        self.sample_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "sample_employees.csv")

    def test_pipeline_analysis(self):
        # 1. Create a dummy working file
        test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        os.makedirs(test_dir, exist_ok=True)
        test_working = os.path.join(test_dir, "test_working.csv")
        
        df = pd.read_csv(self.sample_csv)
        df.to_csv(test_working, index=False)

        dataset_id = "test_ds_001"
        from app.models.db import insert_dataset
        insert_dataset({
            "id": dataset_id,
            "filename": "sample_employees.csv",
            "file_type": "csv",
            "upload_time": "2026-11-19 12:00:00",
            "total_records": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "original_file_path": test_working,
            "working_file_path": test_working
        })

        # 2. Run analysis pipeline
        result = analyze_dataset_pipeline(dataset_id, test_working)

        # 3. Assertions
        self.assertEqual(result["total_records"], 12)
        # 3 records are clean or cleanly repaired: Alice, Charlie, Diana
        # (Bob's Join_Date 12/05/2020 is now correctly flagged as ambiguous - could be Dec-05 or May-12)
        self.assertEqual(result["green_count"], 3)
        # 9 records had human-required issues
        self.assertEqual(result["red_count"], 9)
        self.assertEqual(result["green_percentage"] + result["red_percentage"], 100.0)

        # 4. Check audit log has AI safe repairs
        audit = get_audit_trail(dataset_id)
        ai_repairs = [a for a in audit if a["actor"] == "AI"]
        self.assertTrue(len(ai_repairs) >= 3, "Safe repairs should have been logged in audit trail")

        # 5. Test Reconciliation
        # Simulate user downloading RED records with serials, fixing Evan Wright's salary and Fiona's ID
        meta = get_records_metadata(dataset_id)
        red_meta = [m for m in meta if m["human_required"]]
        
        # Load working df as string/object to simulate spreadsheet editing
        curr_df = pd.read_csv(test_working, dtype=object)
        red_df = curr_df.iloc[[m["record_index"] for m in red_meta]].copy()
        red_df.insert(0, "DataFix_Serial", [m["datafix_serial"] for m in red_meta])

        # Fix Evan Wright (EMP-1005)'s missing salary -> 68000
        evan_matches = red_df[red_df["Employee_ID"] == "EMP-1005"].index
        self.assertTrue(len(evan_matches) > 0)
        red_df.loc[evan_matches[0], "Salary"] = "68000"

        correction_path = os.path.join(test_dir, "test_correction.csv")
        red_df.to_csv(correction_path, index=False)

        # Reconcile
        recon_result = reconcile_fixed_dataset(dataset_id, correction_path)
        self.assertEqual(recon_result["accepted_changes"], 1)
        self.assertEqual(recon_result["green_count"], 4, "Evan Wright should now be GREEN!")
        self.assertEqual(recon_result["red_count"], 8)

if __name__ == "__main__":
    unittest.main()
