import type {
  CaseDetail, CaseResponse, CodeSearchResult, EscalationResponse,
  IntakeSubmission, QueueResponse, WorkflowResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
}

function get<T>(path: string): Promise<T> {
  return apiFetch<T>(path)
}

export const api = {
  createCase:   (intake: IntakeSubmission) =>
    post<CaseResponse>('/cases', intake),

  runWorkflow:  (caseId: string, n: number) =>
    post<WorkflowResponse>(`/cases/${caseId}/workflow${n}`),

  escalate:     (caseId: string) =>
    post<EscalationResponse>(`/cases/${caseId}/escalate`, { trigger: 'member_initiated' }),

  getCase:      (caseId: string) =>
    get<CaseDetail>(`/cases/${caseId}`),

  getQueue:     () =>
    get<QueueResponse>('/cases/queue'),

  searchCodes:  (q: string, codeType?: string) => {
    const params = new URLSearchParams({ q, limit: '10' })
    if (codeType) params.set('code_type', codeType)
    return get<CodeSearchResult[]>(`/codes/search?${params}`)
  },
}
