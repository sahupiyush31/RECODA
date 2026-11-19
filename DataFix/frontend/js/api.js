// API Client for DataFix Engine

const API_BASE = window.location.origin.includes(":8000") 
  ? `${window.location.origin}/api` 
  : "http://127.0.0.1:8000/api";

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
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/add-fix`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Reconciliation failed" }));
      throw new Error(err.detail || "Reconciliation failed");
    }
    return await res.json();
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
