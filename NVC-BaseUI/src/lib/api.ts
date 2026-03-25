const API_BASE = "/api"

export interface Memory {
  key: string
  title: string
  content: string
  namespace: string
  tags: string[]
  created_at: string
  updated_at: string
  chars: number
  lines: number
}

export interface StorageStats {
  total_memories: number
  total_chars: number
  namespaces: number
  db_size_kb: number
  db_path: string
}

export interface MemoryListResponse {
  memories: Memory[]
  total: number
}

export interface TimelineEntry {
  key: string
  title: string
  namespace: string
  tags: string[]
  updated_at: string
}

export interface TimelineResponse {
  days: Record<string, TimelineEntry[]>
  total: number
}

function withNamespace(url: string, namespace?: string): string {
  if (!namespace) return url
  const sp = new URLSearchParams({ ns: namespace })
  return `${url}${url.includes("?") ? "&" : "?"}${sp.toString()}`
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const contentType = res.headers.get("content-type") || ""
    if (contentType.includes("application/json")) {
      const payload = await res.json().catch(() => null)
      throw new Error(payload?.error || `HTTP ${res.status}`)
    }
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export function memoryDetailHref(ref: Pick<Memory, "key" | "namespace">): string {
  const sp = new URLSearchParams({ ns: ref.namespace })
  return `/memories/${encodeURIComponent(ref.key)}?${sp.toString()}`
}

export const api = {
  getMemories(params?: { ns?: string; limit?: number; offset?: number }) {
    const sp = new URLSearchParams()
    if (params?.ns) sp.set("ns", params.ns)
    if (params?.limit) sp.set("limit", String(params.limit))
    if (params?.offset) sp.set("offset", String(params.offset))
    const qs = sp.toString()
    return request<MemoryListResponse>(`/memories${qs ? "?" + qs : ""}`)
  },

  getMemory(key: string, namespace = "default") {
    return request<Memory>(withNamespace(`/memories/${encodeURIComponent(key)}`, namespace))
  },

  getStats() {
    return request<StorageStats>("/stats")
  },

  getNamespaces() {
    return request<string[]>("/namespaces")
  },

  search(query: string, ns?: string) {
    const sp = new URLSearchParams({ q: query })
    if (ns) sp.set("ns", ns)
    return request<MemoryListResponse>(`/search?${sp}`)
  },

  createMemory(data: {
    key: string
    content: string
    title?: string
    namespace?: string
    tags?: string
  }) {
    return request<Memory>("/memories", {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  deleteMemory(key: string, namespace = "default") {
    return request<{ ok: boolean }>(withNamespace(`/memories/${encodeURIComponent(key)}`, namespace), {
      method: "DELETE",
    })
  },

  getTimeline(params?: { year?: number; month?: number; ns?: string }) {
    const sp = new URLSearchParams()
    if (params?.year) sp.set("year", String(params.year))
    if (params?.month) sp.set("month", String(params.month))
    if (params?.ns) sp.set("ns", params.ns)
    const qs = sp.toString()
    return request<TimelineResponse>(`/timeline${qs ? "?" + qs : ""}`)
  },

  importMemories(memories: Array<{
    key: string
    content: string
    title?: string
    namespace?: string
    tags?: string[]
  }>) {
    return request<{ imported: number; total: number }>("/import", {
      method: "POST",
      body: JSON.stringify({ memories }),
    })
  },
}
