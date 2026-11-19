# DataFix --- Autonomous Data Quality & Repair Engine

> **Hackathon project \| INNOVEDGE Innovation & Entrepreneurship
> Development Club**
>
> DataFix inspects uploaded datasets, identifies data-quality problems,
> safely repairs issues that can be corrected with reliable rules, and
> routes uncertain or business-critical corrections to a human. It
> validates the result and exports the usable, cleaned dataset without
> adding DataFix-only metadata to the user's final file.

------------------------------------------------------------------------

## 1. Project vision

Real-world datasets can contain missing values, duplicate records,
invalid formats, inconsistent entries and anomalies. These problems
reduce the reliability of analytics and downstream systems. DataFix is
designed to make the repair process safer, explainable and traceable.

**Product principle**

> AI should repair what it can reliably determine, explain what it
> changes, and leave information it cannot safely infer to a human.

DataFix is not intended to invent facts. For example, if an employee's
salary is blank, the system must not guess a salary. It should flag the
missing value for human intervention.

### Goals

-   Accept CSV and Excel datasets.
-   Profile the dataset and detect data-quality issues.
-   Classify records using a simple RED/GREEN Boolean workflow.
-   Automatically repair only issues covered by safe, deterministic or
    otherwise well-supported rules.
-   Keep human-required records unchanged until a person supplies a
    correction.
-   Validate uploaded corrections before accepting them.
-   Preserve the original dataset and maintain an audit trail.
-   Export validated data in the user's original column structure,
    without DataFix-only columns.

------------------------------------------------------------------------

## 2. Core RED/GREEN model

The user-facing workflow deliberately has only two categories.

  ------------------------------------------------------------------------
  Category                                   Boolean Meaning
  --------------------- ---------------------------- ---------------------
  **GREEN**                 `human_required = false` The record is valid,
                                                     or its safely
                                                     repairable issues
                                                     have been corrected
                                                     and validation has
                                                     passed.

  **RED**                    `human_required = true` At least one issue
                                                     needs human input or
                                                     a human decision.
  ------------------------------------------------------------------------

The Boolean is best stored at the **record level for the dashboard**,
while the issue metadata identifies the exact column(s) and problem(s).
A record remains RED if any unresolved human-required issue remains.

### Examples

  -----------------------------------------------------------------------
  Issue                               Expected handling
  ----------------------------------- -----------------------------------
  Extra whitespace                    May be automatically trimmed under
                                      a defined rule, then validated.

  Consistent date-format conversion   May be automatically standardized
                                      when the interpretation is
                                      unambiguous.

  Missing employee salary             RED; never invent a salary.

  Missing employee/customer           RED; do not fabricate a real-world
  identifier                          identifier.

  Ambiguous department or city        RED if the correct value cannot be
                                      established reliably.

  Suspicious numeric value            Flag for review; do not silently
                                      overwrite it.

  Potential duplicate records         Detect and explain; do not
                                      merge/delete automatically when
                                      identity is uncertain.
  -----------------------------------------------------------------------

**Important:** A high model confidence score alone does not make an
unsupported value safe to invent. Repair permissions must be enforced by
backend rules, not left entirely to an AI model.

------------------------------------------------------------------------

## 3. Main dashboard --- Page 1

The main page is the starting point of the application. Its primary jobs
are to let the user upload a dataset, understand its RED/GREEN
distribution, inspect either category, and download the validated
portion.

### 3.1 Header and navigation

Recommended header:

-   **DATAFIX**
-   Subtitle: *Autonomous Data Quality & Repair Engine*
-   Home
-   Repair History (can be implemented as a supporting page/panel)

Keep the header compact so the upload control and chart remain the
visual focus.

### 3.2 Upload Dataset --- primary action

The upload area is the most prominent action on the initial screen.

Suggested content:

**UPLOAD YOUR DATASET**

-   Drag and drop a file, or choose **Browse Files**.
-   Initial supported formats: `.csv`, `.xlsx`, `.xls` (confirm library
    support and test each format in implementation).
-   Show the selected filename and upload/analysis status.
-   Validate the file before processing.
-   Start profiling and issue detection after a successful upload.

The upload area should remain available on the main dashboard so a user
can start a new analysis. Before a file is uploaded, do not show
fabricated percentages or a misleading empty RED/GREEN chart.

### 3.3 Empty state

Before a dataset is loaded, show a clean empty state, for example:

> **Your data journey starts here.**\
> Upload a CSV or Excel dataset to begin data-quality analysis.

Show the main **Upload Dataset** button. Do not display fake chart
values.

### 3.4 Interactive 3D doughnut chart

After analysis, show a 3D-style doughnut chart with two slices:

-   GREEN --- valid or successfully repaired records.
-   RED --- records requiring human intervention.

The centre of the doughnut is intentionally left empty when the user is
not hovering over a slice.

**Interaction specification**

  -----------------------------------------------------------------------
  User action                         UI behaviour
  ----------------------------------- -----------------------------------
  Hover over GREEN                    Display the GREEN percentage as
                                      large text in the empty centre,
                                      plus the instruction **"Double
                                      Click to Inspect"**.

  Hover over RED                      Display the RED percentage as large
                                      text in the empty centre, plus the
                                      instruction **"Double Click to
                                      Inspect"**.

  Move pointer away                   Return the centre to its empty
                                      state.

  Single-click a slice                Slightly separate/extrude the
                                      selected slice as visual feedback.

  Double-click GREEN                  Navigate to the GREEN read-only
                                      dataset page.

  Double-click RED                    Navigate to the RED read-only
                                      dataset page.
  -----------------------------------------------------------------------

A small visible legend should identify GREEN and RED, so users do not
have to discover the meaning through hovering. Keep the chart
uncluttered: no separate quality-score card and no separate before/after
comparison.

**Percentage definition:** Calculate percentages using record counts,
not cell counts:

-   `green_percentage = green_record_count / total_record_count * 100`
-   `red_percentage = red_record_count / total_record_count * 100`

The two categories must be mutually exclusive and collectively cover all
records in the analysed dataset. Handle an empty dataset safely (do not
divide by zero).

The chart's percentage and the RED/GREEN counts should be calculated
from the same current analysis state.

### 3.5 Main-page Download Fixed Data button

Place **Download Fixed Data** on the main dashboard, below or near the
chart.

It downloads only records that are currently GREEN and have passed
validation.

The export must:

-   Include original records that were already valid.
-   Include records successfully repaired by AI.
-   Include records successfully corrected by a human and revalidated.
-   Exclude unresolved RED records.
-   Preserve the user's original column names and structure.
-   Exclude DataFix serial numbers, issue descriptions, confidence
    scores and other internal metadata.

If there are no GREEN records, disable the button or explain that no
validated records are currently available. If RED records remain,
clearly communicate that the download contains only validated records;
do not imply that it is the complete original dataset.

### 3.6 Dataset information

After analysis, show a compact information area:

-   Dataset filename
-   File type
-   Number of records
-   Number of columns
-   Analysis status
-   Last analysis time

Do not add a separate Dataset Quality Score. The chart's RED/GREEN
percentages are the chosen summary visual.

### 3.7 Recent activity

A small, optional activity panel can show concise events such as:

-   Dataset uploaded.
-   Analysis completed.
-   Safe formatting repair applied.
-   Human correction received.
-   Record revalidated.

This is useful context, but it should not compete visually with the
upload area or chart.

------------------------------------------------------------------------

## 4. Dataset inspection pages --- Page 2 behaviour

The detailed layout of the second page can be finalized separately. The
agreed behaviour is as follows.

### 4.1 GREEN read-only page

Opened by double-clicking the GREEN chart slice.

-   Display only GREEN records.
-   Use a read-only table.
-   Show the user's original columns and values.
-   Do not show DataFix Serial Numbers in the GREEN table.
-   Provide a **Download Green Dataset** button.
-   The download contains only the original dataset columns, without
    DataFix metadata.

### 4.2 RED read-only page

Opened by double-clicking the RED chart slice.

-   Display only RED records.
-   Use a read-only table; users do not edit values inside the website.
-   Show the original columns and values.
-   Show a DataFix-generated serial number for each RED record.
-   Show an additional website-only **Issues** column describing the
    detected issue and affected field.
-   Highlight problematic cells where practical.
-   Provide **Download Red Dataset** and **Add Fixed Dataset** actions.

The `Issues` information and DataFix serial number are application
metadata. They must not be inserted into the user's original data
columns.

### 4.3 Download Red Dataset

The downloaded RED file should contain the selected RED records with the
user's original columns and original values. It must omit the DataFix
Serial Number and Issues metadata.

This allows the user to correct the downloaded file in a spreadsheet
editor of their choice. DataFix does not need to build a full
spreadsheet editor for the first version.

### 4.4 DataFix serial numbers

Generate stable internal identifiers during initial dataset ingestion.
Example:

  DataFix Serial Number   Internal record reference
  ----------------------- ---------------------------
  `DFX-000001`            Record 1 in this dataset
  `DFX-000002`            Record 2 in this dataset

Rules:

-   Serial numbers are generated by DataFix, not supplied by the user.
-   They are not editable in the UI or in the correction workflow.
-   They are used to match RED records when a corrected file is
    uploaded.
-   They are shown in the RED inspection table and included in the RED
    correction file so the application can reconcile the upload.
-   They are not shown in the GREEN inspection table.
-   They are never included in **Download Fixed Data** or other clean
    user-facing exports.
-   Keep the serial-to-record mapping internally even after a record
    becomes GREEN, so audit history and rollback remain possible.

Use a dataset identifier together with the serial number internally. Do
not overwrite a user's own employee/customer ID. If a source file
already has a unique key, it may be retained as source data, but
DataFix's internal serial remains a separate application identifier.

------------------------------------------------------------------------

## 5. ADD FIX --- human correction and reconciliation

The **Add Fixed Dataset** action is available on the RED inspection
page.

### Intended workflow

1.  User downloads the RED dataset.
2.  User edits the relevant values outside DataFix, using a spreadsheet
    editor.
3.  User uploads the corrected file using **Add Fixed Dataset**.
4.  Backend checks the file structure and DataFix serial numbers.
5.  Backend matches uploaded rows to the corresponding RED records.
6.  Backend identifies which values changed.
7.  Backend validates the proposed corrections.
8.  Only valid, permitted corrections are applied to the working
    dataset.
9.  Records with no remaining human-required issues move to GREEN.
10. Records with unresolved or invalid issues remain RED.
11. Return the user to the main dashboard and recalculate the chart.

### Reconciliation safeguards

Do not merge by row position. Use DataFix serial numbers for matching.

Reject or quarantine uploads with:

-   Missing serial numbers.
-   Duplicate serial numbers.
-   Unknown serial numbers.
-   Unexpected records not belonging to the current dataset.
-   Missing required columns or incompatible headers.
-   Changes to protected fields that the correction workflow should not
    modify.
-   Values that fail validation.

The user must not be able to change the serial number to make a
correction apply to a different record.

The uploaded file is a **correction submission**, not a replacement for
the entire master dataset. Apply only approved changes to the
corresponding records and preserve all other values.

### Partial corrections

A correction upload may fix some issues but not all of them. Re-run
validation after applying accepted changes.

For example, if a RED record has two issues and only one is corrected,
it stays RED. It becomes GREEN only after all human-required issues for
that record are resolved and validation passes.

------------------------------------------------------------------------

## 6. Backend data integrity and file lifecycle

The backend should keep three conceptual versions of the data:

  -----------------------------------------------------------------------
  Version                             Purpose
  ----------------------------------- -----------------------------------
  **Original dataset**                Immutable source copy used for
                                      recovery and comparison.

  **Working dataset**                 Current values after accepted AI
                                      and human repairs.

  **Final export**                    Validated GREEN records in the
                                      user's original schema, without
                                      DataFix metadata.
  -----------------------------------------------------------------------

Keep issue details and identifiers in separate application metadata
rather than adding them to the source columns.

### Recommended internal record metadata

A record can have metadata such as:

``` json
{
  "dataset_id": "dataset-unique-id",
  "datafix_serial": "DFX-000102",
  "human_required": true,
  "issues": [
    {
      "column": "Salary",
      "issue_type": "missing_value",
      "description": "Salary is missing and cannot be safely inferred.",
      "repair_method": "human"
    }
  ],
  "validation_status": "needs_human_review"
}
```

This is an internal example. The metadata should be stored separately
from the user's dataset.

### Suggested status logic

-   `human_required = true` if at least one unresolved issue requires
    human input.
-   `human_required = false` only when the record is valid and all
    applied repairs pass validation.
-   Do not change a record to GREEN merely because a file was uploaded.
-   Record each accepted change with the old value, new value, actor
    (`AI` or `Human`), reason and timestamp.

### Audit log and rollback

Maintain an audit log for traceability:

-   Dataset and record reference.
-   Column changed.
-   Previous value.
-   New value.
-   Who/what made the change.
-   Reason for the change.
-   Timestamp.
-   Validation result.

Rollback should restore a prior working value without changing the
immutable original upload.

### Excluding unresolved records

If a user later chooses to omit unresolved RED records from a final
export, prefer an **exclude from export** operation rather than
permanently deleting the original records. Keep the original dataset and
audit history recoverable. This action should require explicit
confirmation and should be clearly distinguished from a fully validated
export.

------------------------------------------------------------------------

## 7. Suggested technology stack

The following is a recommended implementation stack, not a requirement
stated by the hackathon brief.

  -----------------------------------------------------------------------
  Layer                   Suggested tool          Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React                   Build the dashboard and
                                                  inspection pages.

  Frontend language       TypeScript              Safer component and
                                                  data typing.

  Styling                 Tailwind CSS            Consistent responsive
                                                  UI styling.

  3D chart                Three.js with React     Interactive 3D doughnut
                          Three Fiber             visual.

  Data tables             AG Grid Community or    Read-only tables,
                          another suitable table  sorting, filtering and
                          library                 pagination.

  Backend                 Python + FastAPI        API endpoints and
                                                  application logic.

  Data processing         Pandas                  Read, inspect,
                                                  transform and export
                                                  tabular data.

  Excel support           openpyxl                Read/write `.xlsx`
                                                  workbooks.

  Validation              Pandera plus custom     Validate schema, types,
                          business rules          ranges and domain
                                                  constraints.

  Database                SQLite for prototype;   Store dataset metadata,
                          PostgreSQL if           IDs, issues and audit
                          deployment needs it     events.

  Testing                 pytest                  Test detection,
                                                  repairs, reconciliation
                                                  and exports.

  API testing             Swagger UI / Postman    Exercise backend
                                                  endpoints.

  Version control         Git and GitHub          Track code and
                                                  collaborate.
  -----------------------------------------------------------------------

Choose library editions and licenses that are compatible with the
project. Verify the current feature/licensing terms before relying on a
particular table component.

------------------------------------------------------------------------

## 8. Backend implementation plan --- from setup to completion

This section gives a practical order for building the backend. Build and
test each stage before connecting the full UI.

### Stage 1 --- Set up the development environment

Install:

-   Python (use a currently supported version).
-   Node.js and npm for the React frontend.
-   Git.
-   A code editor such as Visual Studio Code.

Create a project structure similar to:

``` text
datafix/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── utils/
│   ├── tests/
│   ├── uploads/
│   ├── exports/
│   └── requirements.txt
├── README.md
└── .gitignore
```

Create a Python virtual environment and install the backend packages.
Keep secrets, local uploads and generated exports out of version
control.

### Stage 2 --- Build the FastAPI application

-   Create the FastAPI application entry point.
-   Add a health-check endpoint.
-   Configure CORS for the frontend development origin.
-   Add consistent error responses.
-   Enable the built-in API documentation during development.

First milestone: the frontend or API client can reach the backend and
receive a successful health-check response.

### Stage 3 --- Implement dataset upload

Create an upload endpoint that:

-   Accepts the supported file types.
-   Checks file extension and actual content where possible.
-   Enforces configurable file-size and row-count limits.
-   Generates a unique `dataset_id`.
-   Stores the original file safely.
-   Reads the dataset with Pandas.
-   Reports parsing errors clearly.

Do not trust the filename or MIME type alone. Treat uploaded files as
untrusted input.

### Stage 4 --- Profile the dataset

Inspect:

-   Row and column counts.
-   Column names.
-   Inferred data types.
-   Missing values.
-   Duplicate rows and candidate duplicate keys.
-   Invalid formats.
-   Inconsistent categories.
-   Basic numeric and date distributions.

Do not automatically assume that every blank cell is an error; rules may
depend on the column and dataset context. Allow the detection layer to
distinguish required and optional fields.

### Stage 5 --- Build the issue detection engine

Create modular detectors, for example:

-   Missing-value detector.
-   Duplicate/candidate-duplicate detector.
-   Format detector.
-   Category consistency detector.
-   Range and type validation.
-   Anomaly detector.

Each detector should return structured issue metadata: record reference,
column, issue type, explanation and proposed handling.

### Stage 6 --- Implement repair permissions and safe repairs

Create a repair-policy layer separate from detection.

For each issue, decide whether it is:

-   Safe to repair automatically using a deterministic, unambiguous
    rule; or
-   Human-required because the correct value cannot be established
    safely.

Examples of safe operations may include trimming whitespace or
normalizing an unambiguous date representation. Examples requiring a
human include a missing salary or an ambiguous identity.

Apply repairs to the **working dataset**, never overwrite the immutable
original. Record every applied change.

### Stage 7 --- Generate stable DataFix serial numbers

At initial ingestion:

-   Create a unique internal serial for each record, scoped to its
    dataset.
-   Store the mapping in the database or metadata store.
-   Keep the serial stable across analysis runs and correction cycles.
-   Do not add it to the original source columns.
-   Expose it only in the RED inspection/correction workflow.

For reliable reconciliation, the backend should also protect against
duplicate or altered serials in uploaded correction files.

### Stage 8 --- Validate the working dataset and calculate RED/GREEN

Run schema and business-rule validation after safe repairs.

For each record:

1.  Gather its unresolved issues.
2.  Determine whether any issue requires human input.
3.  Set `human_required` accordingly.
4.  Mark it GREEN only when all applicable validation checks pass.
5.  Otherwise keep it RED.

Calculate the record counts and percentages returned to the frontend.
Ensure RED plus GREEN equals the total number of in-scope records.

### Stage 9 --- Build the read-only dataset APIs

Provide endpoints to retrieve:

-   Dataset summary and chart counts.
-   GREEN records, with original columns only.
-   RED records, with original columns plus website-only issue metadata
    and DataFix serials.
-   Paginated/searchable records where appropriate.

The API response may contain metadata for the UI, but export endpoints
must explicitly select the correct columns.

### Stage 10 --- Build the export endpoints

Implement separate exports:

-   **Download Fixed Data:** all validated GREEN records, original
    columns only.
-   **Download Green Dataset:** GREEN records, original columns only.
-   **Download Red Dataset:** RED records, original columns only; omit
    DataFix serial and Issues metadata.

Use the original column order and preserve data types/formats as far as
the chosen file format and processing libraries allow. Test CSV and
Excel exports separately.

### Stage 11 --- Implement Add Fixed Dataset reconciliation

Create an endpoint for a corrected RED file.

The backend should:

1.  Check that the correction upload belongs to the active dataset.
2.  Validate required columns and DataFix serials.
3.  Reject duplicate, unknown or missing serials.
4.  Match each row to its original internal record.
5.  Compare proposed changes with the current working values.
6.  Enforce allowed-field and repair policies.
7.  Validate proposed values.
8.  Apply only accepted corrections.
9.  Keep invalid or unresolved records RED.
10. Write audit events for accepted and rejected changes.
11. Recalculate RED/GREEN counts and percentages.

Never merge by row index or assume that every uploaded value is correct.

### Stage 12 --- Add audit history and rollback

Store each change as a separate event. Include enough information to
explain and reverse a change.

Test that rollback restores the previous working value and that the
original upload remains unchanged.

### Stage 13 --- Test the backend end to end

Create sample datasets containing:

-   Missing values.
-   Duplicate records.
-   Invalid and inconsistent formats.
-   Ambiguous values that must remain RED.
-   Rows with multiple simultaneous issues.
-   Records with no pre-existing unique business key.

Test these scenarios:

-   Upload valid and invalid files.
-   Analyze a dataset with zero RED records.
-   Analyze a dataset with zero GREEN records.
-   Download each export and inspect its columns.
-   Upload a corrected RED file with valid fixes.
-   Upload a file with an invalid or duplicated serial.
-   Upload a correction that fixes only one of multiple issues.
-   Confirm unresolved records remain RED.
-   Confirm successfully validated records become GREEN.
-   Confirm the chart counts update correctly.
-   Confirm audit history and rollback work.

### Stage 14 --- Connect frontend and backend

Once the backend endpoints work independently:

-   Connect the upload area to the upload API.
-   Show processing and error states.
-   Render the chart from backend counts.
-   Connect double-click navigation to the RED/GREEN data endpoints.
-   Connect download buttons to their export endpoints.
-   Connect Add Fixed Dataset to the reconciliation endpoint.
-   Refresh the main dashboard after successful reconciliation.

### Stage 15 --- Finalize and prepare the demo

-   Test with more than one dataset.
-   Test large files within configured limits.
-   Verify that user data and metadata do not get mixed.
-   Verify that clean exports contain no DataFix-only columns.
-   Verify that RED records never enter the validated export.
-   Verify that every applied repair is explainable and traceable.
-   Prepare one deliberately messy sample dataset for the demonstration.

------------------------------------------------------------------------

## 9. Suggested API endpoint map

A possible first API design:

  ----------------------------------------------------------------------------------------
  Method                  Endpoint                                 Purpose
  ----------------------- ---------------------------------------- -----------------------
  `GET`                   `/health`                                Backend health check.

  `POST`                  `/datasets/upload`                       Upload and register a
                                                                   dataset.

  `POST`                  `/datasets/{dataset_id}/analyze`         Profile, detect and
                                                                   process safe repairs.

  `GET`                   `/datasets/{dataset_id}/summary`         Return counts,
                                                                   percentages and dataset
                                                                   details.

  `GET`                   `/datasets/{dataset_id}/records/green`   Read-only GREEN
                                                                   records.

  `GET`                   `/datasets/{dataset_id}/records/red`     RED records with issue
                                                                   metadata and DataFix
                                                                   serials.

  `GET`                   `/datasets/{dataset_id}/export/fixed`    Download validated
                                                                   GREEN records.

  `GET`                   `/datasets/{dataset_id}/export/green`    Download GREEN records
                                                                   without app metadata.

  `GET`                   `/datasets/{dataset_id}/export/red`      Download RED records
                                                                   without app metadata.

  `POST`                  `/datasets/{dataset_id}/add-fix`         Upload and reconcile
                                                                   corrected RED records.

  `GET`                   `/datasets/{dataset_id}/audit`           Retrieve modification
                                                                   history.

  `POST`                  `/datasets/{dataset_id}/rollback`        Restore a prior
                                                                   accepted change, with
                                                                   appropriate
                                                                   authorization.
  ----------------------------------------------------------------------------------------

This is a suggested API contract; request/response schemas and
authentication should be finalized during implementation.

------------------------------------------------------------------------

## 10. Security, privacy and reliability checklist

-   Treat uploaded files as untrusted input.
-   Set file-size, row-count and processing-time limits.
-   Validate file content and reject unsupported or malformed files.
-   Store uploads and exports outside publicly served frontend
    directories.
-   Use generated filenames rather than trusting user-provided paths.
-   Avoid logging sensitive cell contents.
-   Keep original uploads immutable.
-   Prevent a correction file from changing record identity.
-   Do not expose internal metadata in clean exports.
-   Use access controls if the application supports multiple users.
-   Define a retention/deletion policy for uploaded datasets.
-   Make processing failures visible and recoverable.
-   Do not claim a dataset is fully clean while unresolved RED records
    remain.

------------------------------------------------------------------------

## 11. Definition of done

The first complete version of DataFix is ready when a user can:

1.  Upload a CSV or Excel dataset.
2.  See the analysis status and RED/GREEN 3D doughnut chart.
3.  Hover over a slice to see its percentage and **Double Click to
    Inspect**.
4.  Double-click GREEN or RED to open the corresponding read-only page.
5.  Download the validated dataset from the main dashboard.
6.  Download GREEN or RED records from their respective inspection
    pages, without DataFix metadata in those downloads.
7.  Download RED records, correct them externally and upload them using
    **Add Fixed Dataset**.
8.  Have corrections matched by stable DataFix serial numbers and
    validated.
9.  See corrected records move to GREEN and unresolved records remain
    RED.
10. Download the final validated dataset with the original user columns.
11. Review an audit trail of accepted modifications.

------------------------------------------------------------------------

## 12. Product decisions currently agreed

-   The main page has a prominent **Upload Dataset** action.
-   The main page has **Download Fixed Data**, which exports validated
    GREEN records only.
-   The main visualization is a RED/GREEN 3D doughnut chart.
-   The centre is empty by default; hovering a slice shows its
    percentage and **Double Click to Inspect**.
-   No separate Dataset Quality Score.
-   No Before/After comparison panel.
-   RED and GREEN open separate read-only inspection pages.
-   GREEN inspection shows original columns only and has a **Download
    Green Dataset** action.
-   RED inspection shows original columns plus website-only issue
    information and DataFix serial numbers.
-   RED inspection has **Download Red Dataset** and **Add Fixed
    Dataset** actions.
-   RED downloads omit DataFix-only metadata.
-   DataFix serial numbers are generated internally, stable, uneditable
    and used for reconciliation. They are exposed in the RED workflow,
    not the GREEN UI or clean exports.
-   Human corrections are validated before records become GREEN.
-   Original data is preserved; the working dataset receives accepted
    repairs.
-   Audit history is retained for traceability.

## 13. Hackathon problem-statement alignment

The INNOVEDGE DataFix problem statement asks for a working prototype
that accepts a dataset, presents detected issues, demonstrates safe
repairs, and exports a cleaned dataset with a quality report and
modification log. It highlights detection, diagnosis, repair,
validation, explanation and tracking.

DataFix's planned capabilities map to those expectations:

  -----------------------------------------------------------------------
  Problem-statement expectation       DataFix approach
  ----------------------------------- -----------------------------------
  Detect missing values, duplicates,  Modular profiling and detection
  invalid formats, inconsistencies    engine.
  and anomalies                       

  Diagnose likely causes              Issue explanations and contextual
                                      diagnostics.

  Repair while preserving valid       Repair permissions, immutable
  values and relationships            original data and ID-based
                                      reconciliation.

  Validate repaired data              Revalidation before a record
                                      becomes GREEN.

  Explain changes and confidence      Repair reason, method and optional
                                      confidence where meaningful.

  Track modifications                 Audit log with old/new values,
                                      actor and timestamp.

  Export cleaned dataset              Download Fixed Data with validated
                                      records and original columns.
  -----------------------------------------------------------------------

The final implementation should also produce a clear quality report and
modification log, as requested in the problem statement.

------------------------------------------------------------------------

**Build priority:** Complete upload, profiling, detection, RED/GREEN
classification, safe repairs, Add Fixed Dataset reconciliation and clean
export before spending significant time on advanced 3D effects. The
visual design attracts attention; a reliable end-to-end repair cycle
proves the product works.
