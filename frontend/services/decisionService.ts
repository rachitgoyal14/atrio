function apiBase(): string {
  return (import.meta.env && (import.meta.env.VITE_API_BASE as string)) || 'http://localhost:8000';
}

export async function acceptStudy(studyId: string): Promise<{ study_id: string; status: string }> {
  const res = await fetch(`${apiBase()}/studies/${encodeURIComponent(studyId)}/accept`, { method: 'POST' });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`acceptStudy failed: ${res.status} ${res.statusText} ${txt}`);
  }
  return (await res.json()) as { study_id: string; status: string };
}

export async function rejectStudy(studyId: string, reason: string): Promise<{ study_id: string; status: string }> {
  const url = `${apiBase()}/studies/${encodeURIComponent(studyId)}/reject?reason=${encodeURIComponent(reason)}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`rejectStudy failed: ${res.status} ${res.statusText} ${txt}`);
  }
  return (await res.json()) as { study_id: string; status: string };
}
