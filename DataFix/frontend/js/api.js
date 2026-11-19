// API Client for DataFix Engine

// Automatically detect the correct API Base URL:
// - When deployed (e.g. Render https://*.onrender.com) or served directly via FastAPI, use current origin.
// - When opened via local frontend dev servers (e.g. Live Server on port 5500, 3000, 5173) or file://, point to local backend port 8000.
const isLocalDevPort = window.location.protocol === "file:" || 
  ["5500", "3000", "5173"].includes(window.location.port);

const API_BASE = isLocalDevPort 
  ? "http://127.0.0.1:8000/api" 
  : `${window.location.origin}/api`;

const API = {
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch (e) {
      return { status: "disconnected", error: e.message };
    }
  },

  async uploadDataset(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return await res.json();
  },

  async getDatasetSummary(datasetId) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/summary`);
    if (!res.ok) throw new Error("Failed to load dataset summary");
    return await res.json();
  },

  async getGreenRecords(datasetId) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/records/green`);
    if (!res.ok) throw new Error("Failed to load GREEN records");
    return await res.json();
  },

  async getRedRecords(datasetId) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/records/red`);
    if (!res.ok) throw new Error("Failed to load RED records");
    return await res.json();
  },

  getExportFixedUrl(datasetId) {
    return `${API_BASE}/datasets/${datasetId}/export/fixed`;
  },

  getExportGreenUrl(datasetId) {
    return `${API_BASE}/datasets/${datasetId}/export/green`;
  },

  getExportRedUrl(datasetId, forCorrection = true) {
    return `${API_BASE}/datasets/${datasetId}/export/red?for_correction=${forCorrection}`;
  },

  async addFixDataset(datasetId, file) {
    const formData = new FormData();
    formData.append("file", file);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000); // 90s safeguard timeout

    try {
      const res = await fetch(`${API_BASE}/datasets/${datasetId}/add-fix`, {
        method: "POST",
        body: formData,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Reconciliation failed" }));
        throw new Error(err.detail || "Reconciliation failed");
      }
      return await res.json();
    } catch (e) {
      clearTimeout(timeoutId);
      if (e.name === "AbortError") {
        throw new Error("Reconciliation timed out after 90 seconds. Please check server status.");
      }
      throw e;
    }
  },

  async getAuditHistory(datasetId) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/audit`);
    if (!res.ok) throw new Error("Failed to load audit history");
    return await res.json();
  },

  async rollbackChange(datasetId, auditId) {
    const formData = new FormData();
    formData.append("audit_id", auditId);
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/rollback`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Rollback failed" }));
      throw new Error(err.detail || "Rollback failed");
    }
    return await res.json();
  }
};
