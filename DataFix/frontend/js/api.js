// API Client for DataFix Engine

// Automatically detect the correct API Base URL:
// - When deployed (e.g. Render https://*.onrender.com) or served directly via FastAPI, use current origin.
// - When opened via local frontend-only dev servers (e.g. Live Server on port 5500, 3000, 5173, etc.) or file://, point to local backend port 8000.
const isLocalFrontendOnly = 
  window.location.protocol === "file:" || 
  ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.port !== "8000");

const API_BASE = isLocalFrontendOnly 
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
    let res;
    try {
      res = await fetch(`${API_BASE}/datasets/upload`, {
        method: "POST",
        body: formData,
      });
    } catch (networkErr) {
      throw new Error(`Unable to reach server at ${API_BASE} (${networkErr.message}). If your Render server was sleeping, please give it 20-30 seconds to wake up and retry.`);
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Upload failed (HTTP ${res.status})` }));
      throw new Error(err.detail || `Upload failed (HTTP ${res.status})`);
    }
    return await res.json();
  },

  async getDatasetSummary(datasetId) {
    let res;
    try {
      res = await fetch(`${API_BASE}/datasets/${datasetId}/summary`);
    } catch (networkErr) {
      throw new Error(`Unable to load dataset summary from server: ${networkErr.message}`);
    }
    if (!res.ok) throw new Error("Failed to load dataset summary");
    return await res.json();
  },

  async getGreenRecords(datasetId) {
    let res;
    try {
      res = await fetch(`${API_BASE}/datasets/${datasetId}/records/green`);
    } catch (networkErr) {
      throw new Error(`Unable to load GREEN records: ${networkErr.message}`);
    }
    if (!res.ok) throw new Error("Failed to load GREEN records");
    return await res.json();
  },

  async getRedRecords(datasetId) {
    let res;
    try {
      res = await fetch(`${API_BASE}/datasets/${datasetId}/records/red`);
    } catch (networkErr) {
      throw new Error(`Unable to load RED records: ${networkErr.message}`);
    }
    if (!res.ok) throw new Error("Failed to load RED records");
    return await res.json();
  },
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
