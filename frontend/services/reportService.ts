export type ReportResponse = {
  study_id: string;
  status: string;
  summary: string;
};

function apiBase(): string {
  return (import.meta.env && (import.meta.env.VITE_API_BASE as string)) || 'http://localhost:8000';
}

export async function generateReport(studyId: string): Promise<ReportResponse> {
  const res = await fetch(`${apiBase()}/studies/${encodeURIComponent(studyId)}/report`, { method: 'POST' });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`generateReport failed: ${res.status} ${res.statusText} ${txt}`);
  }
  return (await res.json()) as ReportResponse;
}
