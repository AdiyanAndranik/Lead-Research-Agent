import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export const ingestText = (text, config) =>
  client.post('/ingest/text', { text, config })

export const ingestCSV = (file, config) => {
  const form = new FormData()
  form.append('file', file)
  Object.entries(config).forEach(([k, v]) => form.append(k, v))
  return client.post('/ingest/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getPipelineStatus = (runId) =>
  client.get(`/pipeline/${runId}`)

export const getPipelineLeads = (runId) =>
  client.get(`/pipeline/${runId}/leads`)

export const getPipelineScores = (runId) =>
  client.get(`/pipeline/${runId}/scores`)

export const getPipelineEmails = (runId) =>
  client.get(`/pipeline/${runId}/emails`)

export const getLeadEmails = (runId, leadId) =>
  client.get(`/pipeline/${runId}/leads/${leadId}/emails`)

export const updateEmail = (runId, leadId, emailId, data) =>
  client.patch(`/pipeline/${runId}/leads/${leadId}/emails/${emailId}`, data)