import os
import unittest
import pandas as pd
from app.models.db import init_db
from app.api.endpoints import (
    health_check, get_dataset_summary, get_green_records,
    get_red_records, export_fixed_data, export_red_dataset,
    rollback_change
)
from app.services.profiling import analyze_dataset_pipeline
from app.services.reconciliation import reconcile_fixed_dataset

class TestAllEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.sample_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "sample_employees.csv")

    def test_complete_lifecycle(self):
        # 1. Health
        h = health_check()
        self.assertEqual(h["status"], "healthy")

        # 2. Ingest Dataset
        test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        os.makedirs(test_dir, exist_ok=True)
        ds_id = "test_lifecycle_001"
        working_csv = os.path.join(test_dir, f"{ds_id}_working.csv")

        df = pd.read_csv(self.sample_csv, dtype=object)
        df.to_csv(working_csv, index=False)

        from app.models.db import insert_dataset
        insert_dataset({
            "id": ds_id,
            "filename": "sample_employees.csv",
            "file_type": "csv",
            "upload_time": "2026-11-19 12:00:00",
            "total_records": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "original_file_path": working_csv,
            "working_file_path": working_csv
        })

        # 3. Analyze
        res_analysis = analyze_dataset_pipeline(ds_id, working_csv)
        self.assertEqual(res_analysis["total_records"], 12)
        # 3 records are clean or cleanly repaired: Alice, Charlie, Diana
        # (Bob's Join_Date 12/05/2020 is now correctly flagged as ambiguous - could be Dec-05 or May-12)
        self.assertEqual(res_analysis["green_count"], 3)
        self.assertEqual(res_analysis["red_count"], 9)

        # 4. Summary Endpoint
        summary = get_dataset_summary(ds_id)
        self.assertEqual(summary["id"], ds_id)
        self.assertEqual(summary["green_count"], 3)
        self.assertEqual(summary["red_count"], 9)
        self.assertTrue(len(summary["activities"]) > 0)
        self.assertTrue(len(summary["ai_diagnosis"]) > 0)

        # 5. GREEN Records Endpoint (Original columns only)
        green_res = get_green_records(ds_id)
        self.assertEqual(green_res["total_count"], 3)
        self.assertEqual(green_res["category"], "GREEN")
        # Ensure DataFix_Serial is NOT in GREEN table
        for r in green_res["records"]:
            self.assertNotIn("DataFix_Serial", r)

        # 6. RED Records Endpoint (Contains DataFix Serial and Issues metadata)
        red_res = get_red_records(ds_id)
        self.assertEqual(red_res["total_count"], 9)
        self.assertEqual(red_res["category"], "RED")
        for r in red_res["records"]:
            self.assertIn("datafix_serial", r)
            self.assertIn("issues", r)
            self.assertTrue(len(r["issues"]) > 0)

        # 7. Exports
        fixed_export = export_fixed_data(ds_id)
        self.assertTrue(os.path.exists(fixed_export.path))

        red_template_export = export_red_dataset(ds_id, for_correction=True)
        self.assertTrue(os.path.exists(red_template_export.path))
        template_df = pd.read_csv(red_template_export.path, dtype=object)
        self.assertIn("DataFix_Serial", template_df.columns)

        red_clean_export = export_red_dataset(ds_id, for_correction=False)
        self.assertTrue(os.path.exists(red_clean_export.path))
        clean_df = pd.read_csv(red_clean_export.path, dtype=object)
        self.assertNotIn("DataFix_Serial", clean_df.columns)

        # 8. Add Fixed Dataset Reconciliation
        # Correct Evan Wright (DFX-000005) missing salary -> 72000
        template_df.loc[template_df["DataFix_Serial"] == "DFX-000005", "Salary"] = "72000"
        # Correct Fiona Gallagher (DFX-000006) missing ID -> EMP-1006
        template_df.loc[template_df["DataFix_Serial"] == "DFX-000006", "Employee_ID"] = "EMP-1006"
        
        correction_file = os.path.join(test_dir, f"{ds_id}_correction.csv")
        template_df.to_csv(correction_file, index=False)

        recon_res = reconcile_fixed_dataset(ds_id, correction_file)
        self.assertEqual(recon_res["accepted_changes"], 2)
        self.assertEqual(recon_res["green_count"], 5, "Both Evan and Fiona should now be GREEN!")
        self.assertEqual(recon_res["red_count"], 7)

        # 9. Rollback Change
        from app.models.db import get_audit_trail
        audit_trail = get_audit_trail(ds_id)
        latest_audit = audit_trail[0]
        rb_res = rollback_change(ds_id, audit_id=latest_audit["id"])
        self.assertIn("Successfully rolled back", rb_res["message"])

if __name__ == "__main__":
    unittest.main()
