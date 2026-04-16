/**
 * BidSentry API Client
 * Centralized API communication layer — all backend calls go through here.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min timeout for LLM calls
  headers: {
    'Accept': 'application/json',
  }
});

// --- Dashboard ---
export const fetchDashboardStats = () => api.get('/dashboard/stats').then(r => r.data);

// --- Tenders ---
export const fetchTenders = (skip = 0, limit = 50) =>
  api.get(`/tenders?skip=${skip}&limit=${limit}`).then(r => r.data);

export const fetchTender = (id) => api.get(`/tenders/${id}`).then(r => r.data);

export const uploadTender = (title, file) => {
  const formData = new FormData();
  formData.append('title', title);
  formData.append('file', file);
  return api.post('/tenders/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data);
};

export const extractCriteria = (tenderId) =>
  api.post(`/tenders/${tenderId}/extract`).then(r => r.data);

export const deleteTender = (id) => api.delete(`/tenders/${id}`).then(r => r.data);

// --- Bidders ---
export const fetchBidders = (tenderId = null, skip = 0, limit = 50) => {
  let url = `/bidders?skip=${skip}&limit=${limit}`;
  if (tenderId) url += `&tender_id=${tenderId}`;
  return api.get(url).then(r => r.data);
};

export const fetchBidder = (id) => api.get(`/bidders/${id}`).then(r => r.data);

export const uploadBidder = (name, tenderId, files) => {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('tender_id', tenderId);
  files.forEach(file => formData.append('files', file));
  return api.post('/bidders/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data);
};

export const deleteBidder = (id) => api.delete(`/bidders/${id}`).then(r => r.data);

// --- Evaluations ---
export const runEvaluation = (tenderId, bidderIds = null) => {
  let url = `/evaluations/run?tender_id=${tenderId}`;
  if (bidderIds) url += `&bidder_ids=${bidderIds}`;
  return api.post(url).then(r => r.data);
};

export const fetchEvaluations = (tenderId) =>
  api.get(`/evaluations/${tenderId}`).then(r => r.data);

export const fetchEvaluationDetail = (tenderId, bidderId) =>
  api.get(`/evaluations/${tenderId}/${bidderId}`).then(r => r.data);

export const exportEvaluationCSV = (tenderId) =>
  api.get(`/evaluations/${tenderId}/export/csv`, { responseType: 'blob' }).then(r => {
    const url = window.URL.createObjectURL(new Blob([r.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `evaluation_${tenderId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

export const exportEvaluationJSON = (tenderId) =>
  api.get(`/evaluations/${tenderId}/export/json`, { responseType: 'blob' }).then(r => {
    const url = window.URL.createObjectURL(new Blob([r.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `evaluation_${tenderId}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

// --- Audit ---
export const fetchAuditLogs = (entityType = null, entityId = null, skip = 0, limit = 50) => {
  let url = `/audit?skip=${skip}&limit=${limit}`;
  if (entityType) url += `&entity_type=${entityType}`;
  if (entityId) url += `&entity_id=${entityId}`;
  return api.get(url).then(r => r.data);
};

export const verifyAuditChain = () => api.get('/audit/verify').then(r => r.data);

export default api;
