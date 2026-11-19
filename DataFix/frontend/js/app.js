// DataFix Frontend Application Logic

let currentDatasetId = null;
let currentSummary = null;
let chartInstance = null;

// DOM Elements
const el = {
  healthBadge: document.getElementById("health-badge"),
  viewMain: document.getElementById("view-main"),
  viewGreen: document.getElementById("view-green"),
  viewRed: document.getElementById("view-red"),
  emptyState: document.getElementById("empty-state"),
  analysisContainer: document.getElementById("analysis-container"),
  fileInput: document.getElementById("file-input"),
  dropZone: document.getElementById("drop-zone"),
  uploadProgress: document.getElementById("upload-progress"),
  loadSampleBtn: document.getElementById("load-sample-btn"),
  downloadFixedBtn: document.getElementById("btn-download-fixed"),
  datasetInfo: document.getElementById("dataset-info"),
  activityList: document.getElementById("activity-list"),
  aiDiagnosisText: document.getElementById("ai-diagnosis-text"),
  
  // Green page
  greenTableHead: document.getElementById("green-table-head"),
  greenTableBody: document.getElementById("green-table-body"),
  greenCountBadge: document.getElementById("green-count-badge"),
  downloadGreenBtn: document.getElementById("btn-download-green"),
  
  // Red page
  redTableHead: document.getElementById("red-table-head"),
  redTableBody: document.getElementById("red-tree"),
  redCountBadge: document.getElementById("red-count-badge"),
  downloadRedCleanBtn: document.getElementById("btn-download-red-clean"),
  downloadRedTemplateBtn: document.getElementById("btn-download-red-template"),
  openAddFixModalBtn: document.getElementById("btn-open-add-fix"),
  
  // Modals
  addFixModal: document.getElementById("add-fix-modal"),
  addFixFileInput: document.getElementById("add-fix-file-input"),
  submitAddFixBtn: document.getElementById("btn-submit-add-fix"),
  addFixStatus: document.getElementById("add-fix-status"),
  closeAddFixBtn: document.getElementById("btn-close-add-fix"),
  
  auditModal: document.getElementById("audit-modal"),
  auditList: document.getElementById("audit-list"),
  closeAuditBtn: document.getElementById("btn-close-audit"),
  navAuditBtn: document.getElementById("nav-audit-btn"),
  navGreenBtn: document.getElementById("nav-green-btn"),
  navRedBtn: document.getElementById("nav-red-btn")
};

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  setupUpload();
  setupAddFix();
  setupAudit();
});

// Health check
async function checkBackendHealth() {
  const health = await API.checkHealth();
  if (health.status === "healthy") {
    el.healthBadge.innerHTML = `
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        Backend Connected ${health.api_key_configured ? '(AI Ready)' : ''}
      </span>
    `;
  } else {
    el.healthBadge.innerHTML = `
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <span class="w-2 h-2 rounded-full bg-rose-400"></span>
        Backend Disconnected
      </span>
    `;
  }
}

// Navigation & View Routing
function setupNavigation() {
  document.querySelectorAll("[data-nav='home']").forEach(btn => {
    btn.addEventListener("click", () => showView("main"));
  });

  document.getElementById("btn-inspect-green")?.addEventListener("click", () => navigateToInspect("GREEN"));
  document.getElementById("btn-inspect-red")?.addEventListener("click", () => navigateToInspect("RED"));

  el.navGreenBtn?.addEventListener("click", () => navigateToInspect("GREEN"));
  el.navRedBtn?.addEventListener("click", () => navigateToInspect("RED"));

  document.getElementById("btn-expand-red")?.addEventListener("click", () => {
    document.querySelectorAll("#red-tree details").forEach(d => d.open = true);
  });
  document.getElementById("btn-collapse-red")?.addEventListener("click", () => {
    document.querySelectorAll("#red-tree details").forEach(d => d.open = false);
  });

  el.navAuditBtn?.addEventListener("click", () => openAuditModal());
  el.closeAuditBtn?.addEventListener("click", () => {
    el.auditModal.classList.add("hidden");
  });
}

function showView(viewName) {
  el.viewMain.classList.add("hidden");
  el.viewGreen.classList.add("hidden");
  el.viewRed.classList.add("hidden");

  if (viewName === "main") {
    el.viewMain.classList.remove("hidden");
  } else if (viewName === "green") {
    el.viewGreen.classList.remove("hidden");
  } else if (viewName === "red") {
    el.viewRed.classList.remove("hidden");
  }
}

function navigateToInspect(category) {
  if (category === "GREEN") {
    loadGreenView();
    showView("green");
  } else if (category === "RED") {
    loadRedView();
    showView("red");
  }
}

// Upload Setup
function setupUpload() {
  const fileInput = el.fileInput;
  const dropZone = el.dropZone;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-blue-500", "bg-blue-500/5");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-blue-500", "bg-blue-500/5");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-blue-500", "bg-blue-500/5");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  el.loadSampleBtn.addEventListener("click", async () => {
    try {
      showLoading(true, "Loading messy employee sample dataset...");
      // Fetch the sample employee CSV file directly from backend static / samples
      const sampleResp = await fetch("/static/samples/sample_employees.csv");
      let blob;
      if (sampleResp.ok) {
        blob = await sampleResp.blob();
      } else {
        // Fallback: create mock CSV blob
        const sampleCsv = `Employee_ID,Name,Department,Salary,Join_Date,Age,Email
EMP-1001,Alice Walker,Engineering,85000,2021-04-15,29,alice.w@company.com
EMP-1002,  Bob  Smith  ,Marketing,62000,12/05/2020,34,bob.smith@company.com
EMP-1003,Charlie Davis,Finance,91000,2019/11/01,41,charlie.d@company.com
EMP-1004,Diana Prince ,Engineering,105000,2018-08-20,32,diana.p@company.com
EMP-1005,Evan Wright,Sales,,2022-01-10,28,evan.w@company.com
,Fiona Gallagher,HR,54000,2023-03-01,26,fiona.g@company.com
EMP-1007,George Clark,Operations,-45000,2020-09-14,38,george.c@company.com
EMP-1008,Hannah Abbott,Finance,78000,2022-02-31,30,hannah.a@company.com
EMP-1009,Ian Malcolm,Research,95000,2017-06-12,-5,ian.m@company.com
EMP-1010,Julia Roberts,Legal,115000,2016-10-05,45,julia.roberts-company
EMP-1011,Kevin Bacon,Marketing,60000,2021-07-22,33,kevin.b@company.com
EMP-1011,Kevin Bacon,Marketing,60000,2021-07-22,33,kevin.b@company.com`;
        blob = new Blob([sampleCsv], { type: "text/csv" });
      }
      const file = new File([blob], "sample_employees.csv", { type: "text/csv" });
      await handleFileUpload(file);
    } catch (err) {
      showLoading(false);
      alert("Failed to load sample dataset: " + err.message);
    }
  });

  el.downloadFixedBtn.addEventListener("click", () => {
    if (!currentDatasetId) return;
    window.location.href = API.getExportFixedUrl(currentDatasetId);
  });
}

async function handleFileUpload(file) {
  try {
    showLoading(true, `Uploading & analyzing '${file.name}'...`);
    const result = await API.uploadDataset(file);
    currentDatasetId = result.dataset_id;
    await refreshDashboard();
    showLoading(false);
  } catch (err) {
    showLoading(false);
    alert("Upload error: " + err.message);
  }
}

function showLoading(show, message = "Processing...") {
  if (show) {
    el.uploadProgress.classList.remove("hidden");
    document.getElementById("upload-status-text").innerText = message;
  } else {
    el.uploadProgress.classList.add("hidden");
  }
}

// Refresh Dashboard
async function refreshDashboard() {
  if (!currentDatasetId) return;

  const summary = await API.getDatasetSummary(currentDatasetId);
  currentSummary = summary;

  // Show analysis container, hide empty state
  el.emptyState.classList.add("hidden");
  el.analysisContainer.classList.remove("hidden");
  el.navGreenBtn?.classList.remove("hidden");
  el.navRedBtn?.classList.remove("hidden");

  // Update 3D Chart
  if (!chartInstance) {
    chartInstance = new DoughnutChart3D("chart-canvas-container", {
      onNavigate: (type) => navigateToInspect(type),
    });
  }
  chartInstance.updateData(summary.green_percentage, summary.red_percentage);
  chartInstance.setDefaultStat(summary.green_percentage);

  // Update Percentages and Counts in Legend
  document.getElementById("legend-green-pct").innerText = `${summary.green_percentage}%`;
  document.getElementById("legend-green-count").innerText = `${summary.green_count} records`;
  document.getElementById("legend-red-pct").innerText = `${summary.red_percentage}%`;
  document.getElementById("legend-red-count").innerText = `${summary.red_count} records`;

  // Update Download Fixed Button status
  if (summary.green_count === 0) {
    el.downloadFixedBtn.disabled = true;
    el.downloadFixedBtn.classList.add("opacity-50", "cursor-not-allowed");
    document.getElementById("fixed-btn-subtext").innerText = "No validated records available yet";
  } else {
    el.downloadFixedBtn.disabled = false;
    el.downloadFixedBtn.classList.remove("opacity-50", "cursor-not-allowed");
    document.getElementById("fixed-btn-subtext").innerText = `Download ${summary.green_count} clean validated records (Original format)`;
  }

  // Update Dataset Information Card (Section 3.6)
  el.datasetInfo.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">Dataset Filename</span>
        <span class="text-slate-200 font-semibold truncate block mt-0.5" title="${summary.filename}">${summary.filename}</span>
      </div>
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">File Type</span>
        <span class="text-slate-200 font-semibold uppercase block mt-0.5">${summary.file_type}</span>
      </div>
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">Total Records</span>
        <span class="text-slate-200 font-semibold font-mono block mt-0.5">${summary.total_records}</span>
      </div>
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">Total Columns</span>
        <span class="text-slate-200 font-semibold font-mono block mt-0.5">${summary.total_columns}</span>
      </div>
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">Analysis Status</span>
        <span class="text-emerald-400 font-semibold capitalize block mt-0.5 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          ${summary.analysis_status}
        </span>
      </div>
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
        <span class="text-xs text-slate-400 font-medium block">Last Analysis Time</span>
        <span class="text-slate-200 font-semibold text-xs font-mono block mt-0.5">${summary.upload_time}</span>
      </div>
    </div>
  `;

  // Update Recent Activity Panel (Section 3.7)
  const activities = summary.activities || [];
  if (activities.length === 0) {
    el.activityList.innerHTML = `<li class="text-xs text-slate-500 italic py-2">No activity logged yet.</li>`;
  } else {
    el.activityList.innerHTML = activities.map(act => `
      <li class="flex items-start gap-3 py-2 border-b border-slate-800/60 last:border-0 text-xs">
        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${getActivityBadge(act.event_type)}">
          ${act.event_type}
        </span>
        <div class="flex-1 text-slate-300">
          ${act.event_type === "SAFE_REPAIR" ? renderRulesDropdown(act.description) : `<div>${act.description}</div>`}
          <div class="text-[10px] text-slate-500 font-mono mt-0.5">${act.timestamp}</div>
        </div>
      </li>
    `).join("");
  }

  // Load the rule breakdown only when a SAFE_REPAIR dropdown is opened
  el.activityList.querySelectorAll(".rules-dropdown").forEach(d => {
    d.addEventListener("toggle", () => { if (d.open) loadRepairRules(d); });
  });

  // Update AI Diagnosis
  if (summary.ai_diagnosis) {
    el.aiDiagnosisText.innerText = summary.ai_diagnosis;
  }
}

function getActivityBadge(type) {
  switch (type) {
    case "UPLOAD": return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
    case "SAFE_REPAIR": return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    case "HUMAN_CORRECTION": return "bg-purple-500/10 text-purple-400 border border-purple-500/20";
    case "ROLLBACK": return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    default: return "bg-slate-800 text-slate-400";
  }
}

// GREEN Inspection View
async function loadGreenView() {
  if (!currentDatasetId) return;

  const data = await API.getGreenRecords(currentDatasetId);
  el.greenCountBadge.innerText = `${data.total_count} Validated Records`;

  // Table Headers (Original columns only, NO serials)
  el.greenTableHead.innerHTML = `
    <tr>
      <th class="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">#</th>
      ${data.columns.map(c => `
        <th class="px-4 py-3 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">${c}</th>
      `).join("")}
      <th class="px-4 py-3 text-right text-xs font-bold text-emerald-400 uppercase tracking-wider">Status</th>
    </tr>
  `;

  // Table Rows
  if (data.records.length === 0) {
    el.greenTableBody.innerHTML = `
      <tr>
        <td colspan="${data.columns.length + 2}" class="text-center py-12 text-slate-500">
          No records currently qualify as Correct Data. Complete corrections on Action Required! records to validate them.
        </td>
      </tr>
    `;
  } else {
    el.greenTableBody.innerHTML = data.records.map((r, i) => `
      <tr class="hover:bg-slate-800/40 border-b border-slate-800/50 transition">
        <td class="px-4 py-3 text-xs text-slate-500 font-mono">${i + 1}</td>
        ${data.columns.map(c => `
          <td class="px-4 py-3 text-sm text-slate-200">${r[c] !== null && r[c] !== undefined ? r[c] : '<span class="text-slate-600">-</span>'}</td>
        `).join("")}
        <td class="px-4 py-3 text-right">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            ✓ Clean
          </span>
        </td>
      </tr>
    `).join("");
  }

  el.downloadGreenBtn.onclick = () => {
    window.location.href = API.getExportGreenUrl(currentDatasetId);
  };
}

// RED Inspection View (folder-style dropdown explorer)
const CHEV = `<svg class="chev w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>`;

function escHtml(v) {
  return String(v ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

let currentRedRecords = [];
let currentAllIssues = [];
let selectedReasonFilter = "all";

function formatReasonTitle(type) {
  const map = {
    missing_value: "Missing Value",
    date_format: "Date Format",
    suspicious_numeric: "Suspicious Numeric",
    invalid_format: "Invalid Format",
    duplicate: "Duplicate Record",
    invalid_range: "Out of Range",
    whitespace: "Whitespace Issue",
    anomaly: "Data Anomaly"
  };
  return map[type] || String(type || "Other Error").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function getReasonDescription(type) {
  const map = {
    missing_value: "Blank or empty cells requiring user input",
    date_format: "Unrecognized or invalid calendar dates",
    suspicious_numeric: "Negative or unexpected numbers requiring review",
    invalid_format: "Values not matching required format (e.g., email syntax)",
    duplicate: "Identical or repeating records in dataset",
    invalid_range: "Values outside acceptable boundaries",
    whitespace: "Irregular spacing or formatting",
    anomaly: "Statistical outliers or irregularities"
  };
  return map[type] || "Values requiring manual verification";
}

async function loadRedView() {
  if (!currentDatasetId) return;

  selectedReasonFilter = "all";
  const data = await API.getRedRecords(currentDatasetId);
  currentRedRecords = data.records || [];
  
  currentAllIssues = currentRedRecords.flatMap(r => 
    (r.issues || []).map(iss => ({
      serial: r.datafix_serial,
      recordIndex: r.record_index,
      iss,
      value: r.data ? r.data[iss.column] : ""
    }))
  );

  const totalErrors = currentAllIssues.length;
  const totalRecords = currentRedRecords.length;
  el.redCountBadge.innerText = `${totalErrors} Error${totalErrors === 1 ? '' : 's'}`;

  // 1. Render Total Errors Section
  renderTotalErrorsSection(totalErrors, totalRecords);

  // 2. Render Errors by Reason Breakdown Section
  renderErrorReasonsBreakdown(currentAllIssues);

  // 3. Render Dropdown for Errors list
  renderErrorsDropdownList();

  el.downloadRedCleanBtn.onclick = () => {
    window.location.href = API.getExportRedUrl(currentDatasetId, false);
  };

  el.downloadRedTemplateBtn.onclick = () => {
    window.location.href = API.getExportRedUrl(currentDatasetId, true);
  };
}

function renderTotalErrorsSection(totalErrors, totalRecords) {
  const container = document.getElementById("red-total-errors-content");
  if (!container) return;

  if (totalErrors === 0) {
    container.innerHTML = `
      <div class="flex items-center gap-4 text-emerald-400 py-3">
        <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-xl font-bold">✓</div>
        <div>
          <div class="text-base font-bold text-white">All Records Clean!</div>
          <div class="text-xs text-slate-400 mt-0.5">All records have been validated. There are 0 Action Required records remaining.</div>
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
      <div class="flex items-start sm:items-center gap-4">
        <div class="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center flex-shrink-0 text-rose-400">
          <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400">Total Errors Overview</div>
          <div class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-0.5 font-mono">
            ${totalErrors} <span class="text-base font-normal text-slate-400 font-sans">total error${totalErrors === 1 ? '' : 's'}</span>
            <span class="text-slate-600 font-light mx-2">•</span>
            ${totalRecords} <span class="text-base font-normal text-slate-400 font-sans">affected record${totalRecords === 1 ? '' : 's'}</span>
          </div>
          <p class="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            These records contain values that require human verification. They cannot be automatically guessed without risking incorrect data. Review each error reason below, then use the Correction Template to make your fixes.
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3 w-full md:w-auto justify-end">
        <div class="px-5 py-3 rounded-xl bg-slate-900 border border-slate-800 text-center flex-1 md:flex-initial shadow-inner">
          <div class="text-[11px] text-slate-400 font-medium">Total Errors</div>
          <div class="text-2xl font-bold font-mono text-rose-400 mt-0.5">${totalErrors}</div>
        </div>
        <div class="px-5 py-3 rounded-xl bg-slate-900 border border-slate-800 text-center flex-1 md:flex-initial shadow-inner">
          <div class="text-[11px] text-slate-400 font-medium">Records to Fix</div>
          <div class="text-2xl font-bold font-mono text-white mt-0.5">${totalRecords}</div>
        </div>
      </div>
    </div>
  `;
}

function renderErrorReasonsBreakdown(allIssues) {
  const grid = document.getElementById("red-reasons-grid");
  const select = document.getElementById("red-reason-filter");
  if (!grid) return;

  const reasonCounts = {};
  allIssues.forEach(({ iss }) => {
    const type = iss.issue_type || "other";
    reasonCounts[type] = (reasonCounts[type] || 0) + 1;
  });

  const sortedReasons = Object.entries(reasonCounts).sort((a, b) => b[1] - a[1]);

  if (select) {
    select.innerHTML = `
      <option value="all">All Errors (${allIssues.length})</option>
      ${sortedReasons.map(([type, count]) => `
        <option value="${type}" ${selectedReasonFilter === type ? 'selected' : ''}>
          ${escHtml(formatReasonTitle(type))} (${count})
        </option>
      `).join("")}
    `;

    select.onchange = (e) => {
      selectedReasonFilter = e.target.value;
      updateReasonCardsSelection();
      renderErrorsDropdownList();
    };
  }

  if (sortedReasons.length === 0) {
    grid.innerHTML = `<div class="text-xs text-slate-500 col-span-full py-4 text-center">No error categories detected.</div>`;
    return;
  }

  grid.innerHTML = sortedReasons.map(([type, count]) => {
    const title = formatReasonTitle(type);
    const desc = getReasonDescription(type);
    const isSelected = selectedReasonFilter === type;
    return `
      <div class="reason-card p-4 rounded-xl border transition cursor-pointer group select-none ${isSelected ? 'bg-rose-500/10 border-rose-500/60 shadow-lg shadow-rose-500/10 ring-1 ring-rose-500/40' : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'}"
           data-reason="${type}">
        <div class="flex items-center justify-between gap-2">
          <div class="font-bold text-sm text-slate-200 group-hover:text-white transition flex items-center gap-2">
            <span class="w-2 h-2 rounded-full ${count > 0 ? 'bg-rose-400' : 'bg-slate-500'}"></span>
            <span>${escHtml(title)}</span>
          </div>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-white/10 text-white border border-white/20">
            ${count}
          </span>
        </div>
        <div class="text-[11px] text-slate-400 mt-1.5 leading-snug">${escHtml(desc)}</div>
        <div class="text-[10px] text-blue-400 group-hover:text-blue-300 font-medium mt-2.5 flex items-center gap-1">
          <span>${isSelected ? 'Active Filter (click to show all)' : 'Click to filter →'}</span>
        </div>
      </div>
    `;
  }).join("");

  grid.querySelectorAll(".reason-card").forEach(card => {
    card.addEventListener("click", () => {
      const reason = card.getAttribute("data-reason");
      if (selectedReasonFilter === reason) {
        selectedReasonFilter = "all";
      } else {
        selectedReasonFilter = reason;
      }
      if (select) select.value = selectedReasonFilter;
      updateReasonCardsSelection();
      renderErrorsDropdownList();
    });
  });
}

function updateReasonCardsSelection() {
  const cards = document.querySelectorAll("#red-reasons-grid .reason-card");
  cards.forEach(card => {
    const reason = card.getAttribute("data-reason");
    const isSelected = selectedReasonFilter === reason;
    if (isSelected) {
      card.className = "reason-card p-4 rounded-xl border transition cursor-pointer group select-none bg-rose-500/10 border-rose-500/60 shadow-lg shadow-rose-500/10 ring-1 ring-rose-500/40";
      const hint = card.querySelector(".text-\\[10px\\]");
      if (hint) hint.innerHTML = "<span>Active Filter (click to show all)</span>";
    } else {
      card.className = "reason-card p-4 rounded-xl border transition cursor-pointer group select-none bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900";
      const hint = card.querySelector(".text-\\[10px\\]");
      if (hint) hint.innerHTML = "<span>Click to filter →</span>";
    }
  });
}

function renderErrorsDropdownList() {
  const container = document.getElementById("red-tree");
  const filterStatus = document.getElementById("red-filter-status");
  if (!container) return;

  const filtered = selectedReasonFilter === "all"
    ? currentAllIssues
    : currentAllIssues.filter(item => item.iss.issue_type === selectedReasonFilter);

  if (filterStatus) {
    if (selectedReasonFilter === "all") {
      filterStatus.innerText = `Showing all ${filtered.length} errors`;
    } else {
      filterStatus.innerHTML = `Showing <strong class="text-rose-400">${escHtml(formatReasonTitle(selectedReasonFilter))}</strong> (${filtered.length}) &mdash; <button class="underline text-blue-400 hover:text-blue-300 ml-1 font-medium" id="btn-clear-reason-filter">Clear filter</button>`;
      document.getElementById("btn-clear-reason-filter")?.addEventListener("click", () => {
        selectedReasonFilter = "all";
        const sel = document.getElementById("red-reason-filter");
        if (sel) sel.value = "all";
        updateReasonCardsSelection();
        renderErrorsDropdownList();
      });
    }
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 text-slate-500 text-sm">
        No errors found matching the current filter.
      </div>
    `;
    return;
  }

  // Group by reason type so each reason has its own clean expandable dropdown
  const groups = {};
  filtered.forEach(item => {
    const type = item.iss.issue_type || "other";
    if (!groups[type]) groups[type] = [];
    groups[type].push(item);
  });

  const groupKeys = Object.keys(groups);

  container.innerHTML = groupKeys.map(type => {
    const items = groups[type];
    const title = formatReasonTitle(type);
    const count = items.length;

    const listHtml = items.map(({ serial, iss, value }) => {
      const isMissing = value === "" || value === null || value === undefined;
      return `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 hover:bg-slate-900/60 transition text-xs border-b border-slate-800/60 last:border-b-0">
          <div class="flex items-center gap-3 flex-wrap sm:flex-nowrap">
            <span class="font-mono font-bold text-white bg-slate-800 px-2 py-1 rounded border border-slate-700 flex-shrink-0">
              ${escHtml(serial)}
            </span>
            <div class="flex items-center gap-1.5 font-semibold text-slate-200">
              <span class="text-slate-500 font-normal">Column:</span>
              <span class="text-blue-300">${escHtml(iss.column)}</span>
            </div>
            <div class="text-slate-400 flex items-center gap-1.5">
              <span class="text-slate-500">Current value:</span>
              ${isMissing 
                ? '<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Empty / Missing</span>' 
                : `<span class="font-mono text-amber-300 font-medium bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">${escHtml(value)}</span>`
              }
            </div>
          </div>
          <div class="text-slate-300 text-left sm:text-right sm:max-w-md">
            <div>${escHtml(iss.description)}</div>
            ${iss.suggested_action ? `<div class="text-[11px] text-slate-400 mt-0.5 italic">Action: ${escHtml(iss.suggested_action)}</div>` : ''}
          </div>
        </div>
      `;
    }).join("");

    return `
      <details open class="rounded-xl border border-slate-800 bg-black/60 overflow-hidden shadow-lg transition">
        <summary class="flex items-center gap-3 px-4 py-3.5 cursor-pointer hover:bg-slate-900 transition select-none bg-slate-900/40">
          ${CHEV}
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-white">${escHtml(title)}</span>
            <span class="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              ${count} ${count === 1 ? 'error' : 'errors'}
            </span>
          </div>
          <span class="ml-auto text-xs text-slate-500">Click to expand / collapse</span>
        </summary>
        <div class="border-t border-slate-800 max-h-[460px] overflow-y-auto divide-y divide-slate-800/40">
          ${listHtml}
        </div>
      </details>
    `;
  }).join("");
}

// Recent Activity: "applied N safe rule repairs" becomes a dropdown of the rules used
function renderRulesDropdown(description) {
  return `
    <details class="rules-dropdown w-full">
      <summary class="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white">
        ${CHEV}
        <span>${escHtml(description)}</span>
      </summary>
      <div class="rules-body mt-2 ml-5 space-y-2 text-xs">
        <div class="text-slate-500 italic">Loading applied rules...</div>
      </div>
    </details>`;
}

function ruleLabel(reason) {
  const r = (reason || "").toLowerCase();
  if (r.includes("whitespace")) return "Whitespace cleanup (extra spaces removed)";
  if (r.includes("date")) return "Date standardization (unambiguous dates only)";
  return (reason || "").replace("Safe AI repair: ", "");
}

async function loadRepairRules(detailsEl) {
  if (detailsEl.dataset.loaded) return;
  const body = detailsEl.querySelector(".rules-body");
  try {
    const data = await API.getAuditHistory(currentDatasetId);
    const repairs = data.audit_logs.filter(l => l.actor === "AI" && (l.reason || "").startsWith("Safe AI repair"));
    if (repairs.length === 0) {
      body.innerHTML = `<div class="text-slate-500">No rule details found.</div>`;
      return;
    }

    const groups = {};
    repairs.forEach(l => { (groups[l.reason] = groups[l.reason] || []).push(l); });

    body.innerHTML = Object.entries(groups).map(([reason, items]) => `
      <details>
        <summary class="flex items-center gap-2 cursor-pointer text-slate-200 hover:text-white">
          ${CHEV}
          <span class="font-semibold">${escHtml(ruleLabel(reason))}</span>
          <span class="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full bg-white text-black">${items.length}</span>
        </summary>
        <div class="ml-5 mt-1.5 space-y-1 max-h-48 overflow-y-auto">
          ${items.map(l => `
            <div class="font-mono text-[11px] text-slate-400 py-0.5">
              <span class="text-white">${escHtml(l.datafix_serial)}</span> · ${escHtml(l.column_name)}:
              <span class="line-through">"${escHtml(l.old_value)}"</span> → <span class="text-white">"${escHtml(l.new_value)}"</span>
            </div>`).join("")}
        </div>
      </details>`).join("");

    detailsEl.dataset.loaded = "1";
  } catch (err) {
    body.innerHTML = `<div class="text-slate-400">Failed to load rules: ${escHtml(err.message)}</div>`;
  }
}

function getIssueBadge(type) {
  switch (type) {
    case "missing_value": return "bg-rose-500/20 text-rose-300 border border-rose-500/30";
    case "suspicious_numeric": return "bg-amber-500/20 text-amber-300 border border-amber-500/30";
    case "anomaly": return "bg-orange-500/20 text-orange-300 border border-orange-500/30";
    case "duplicate": return "bg-purple-500/20 text-purple-300 border border-purple-500/30";
    case "date_format": return "bg-blue-500/20 text-blue-300 border border-blue-500/30";
    default: return "bg-slate-700 text-slate-300";
  }
}

// Add Fixed Dataset Reconciliation (Section 5)
function setupAddFix() {
  el.openAddFixModalBtn.addEventListener("click", () => {
    el.addFixModal.classList.remove("hidden");
    el.addFixStatus.classList.add("hidden");
    el.addFixFileInput.value = "";
  });

  el.closeAddFixBtn.addEventListener("click", () => {
    el.addFixModal.classList.add("hidden");
  });

  el.submitAddFixBtn.addEventListener("click", async () => {
    const file = el.addFixFileInput.files[0];
    if (!file) {
      alert("Please select a corrected file to upload.");
      return;
    }

    el.submitAddFixBtn.disabled = true;
    el.submitAddFixBtn.classList.add("opacity-50", "cursor-not-allowed");

    try {
      el.addFixStatus.classList.remove("hidden");
      el.addFixStatus.innerHTML = `
        <div class="text-blue-400 text-sm font-semibold flex items-center gap-2">
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
          Reconciling corrected records & revalidating dataset...
        </div>
      `;

      const res = await API.addFixDataset(currentDatasetId, file);

      el.addFixStatus.innerHTML = `
        <div class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-sm text-emerald-300">
          <div class="font-bold">✓ Reconciliation Complete</div>
          <div class="mt-1 text-xs">
            Accepted changes: <strong>${res.accepted_changes}</strong> | 
            Rejected invalid: <strong>${res.rejected_changes}</strong> | 
            Now Correct Data: <strong>${res.green_count} (${res.green_percentage}%)</strong>
          </div>
        </div>
      `;

      // Wait 1.5 seconds, then close modal and return user to Main Dashboard
      setTimeout(async () => {
        el.addFixModal.classList.add("hidden");
        el.submitAddFixBtn.disabled = false;
        el.submitAddFixBtn.classList.remove("opacity-50", "cursor-not-allowed");
        await refreshDashboard();
        showView("main");
      }, 1500);

    } catch (err) {
      el.submitAddFixBtn.disabled = false;
      el.submitAddFixBtn.classList.remove("opacity-50", "cursor-not-allowed");
      el.addFixStatus.innerHTML = `
        <div class="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-sm text-rose-300">
          <div class="font-bold">Reconciliation Safeguard Error</div>
          <div class="mt-1 text-xs leading-relaxed">${err.message}</div>
        </div>
      `;
    }
  });
}

// Audit Trail & Rollback (Section 6 & 8 Stage 12)
function setupAudit() {
  // Handled in openAuditModal
}

async function openAuditModal() {
  if (!currentDatasetId) {
    alert("Please upload and analyze a dataset first.");
    return;
  }

  el.auditModal.classList.remove("hidden");
  el.auditList.innerHTML = `<div class="text-slate-400 text-sm py-4">Loading audit trail...</div>`;

  try {
    const data = await API.getAuditHistory(currentDatasetId);
    if (data.audit_logs.length === 0) {
      el.auditList.innerHTML = `<div class="text-slate-500 text-sm py-8 text-center">No modifications recorded yet.</div>`;
      return;
    }

    el.auditList.innerHTML = data.audit_logs.map(log => `
      <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-mono font-bold text-amber-400">${log.datafix_serial}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${log.actor === 'AI' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-purple-500/20 text-purple-300'}">
              ${log.actor}
            </span>
            <span class="text-slate-400 font-mono text-[11px]">${log.timestamp}</span>
          </div>
          <div class="text-slate-300">
            Column <strong>${log.column_name}</strong>: 
            <span class="text-rose-400 line-through">${log.old_value || '[blank]'}</span> 
            → 
            <span class="text-emerald-400 font-semibold">${log.new_value || '[blank]'}</span>
          </div>
          <div class="text-[11px] text-slate-500 mt-0.5">${log.reason || ''}</div>
        </div>
        <div>
          <button class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-semibold transition"
            onclick="handleRollback(${log.id})">
            ↺ Rollback
          </button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    el.auditList.innerHTML = `<div class="text-rose-400 text-sm">Failed to load audit history: ${err.message}</div>`;
  }
}

window.handleRollback = async function(auditId) {
  if (!confirm("Are you sure you want to rollback this change? The record will be reverted to its previous value and revalidated.")) {
    return;
  }
  try {
    const res = await API.rollbackChange(currentDatasetId, auditId);
    alert(res.message);
    await refreshDashboard();
    await openAuditModal();
  } catch (err) {
    alert("Rollback failed: " + err.message);
  }
};
