/**
 * API service for Resume Optimizer
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

/**
 * Submit resume optimization job
 */
export async function submitOptimization(resumeFile, jobDescription, template) {
  const formData = new FormData();
  formData.append('resume', resumeFile);
  formData.append('job_description', jobDescription);
  formData.append('template', template);
  
  const response = await api.post('/api/optimize-resume', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
}

/**
 * Get job status (polling fallback)
 */
export async function getJobStatus(jobId) {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
}

/**
 * List all jobs
 */
export async function listJobs(status = null, limit = 50) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (limit) params.append('limit', limit.toString());
  
  const response = await api.get(`/api/jobs?${params.toString()}`);
  return response.data;
}

/**
 * Delete a job
 */
export async function deleteJob(jobId) {
  const response = await api.delete(`/api/jobs/${jobId}`);
  return response.data;
}

/**
 * Health check
 */
export async function healthCheck() {
  const response = await api.get('/api/');
  return response.data;
}

export default api;
