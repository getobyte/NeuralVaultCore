import { useEffect, useState } from "react"
import { useNavigate, useParams, useSearchParams } from "react-router-dom"
import { api, type Memory } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Trash } from "@phosphor-icons/react"

type MemoryDetailState = {
  requestId: string
  memory: Memory | null
  error: string
}

export default function MemoryDetailPage() {
  const { key } = useParams<{ key: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const namespace = searchParams.get("ns") || "default"
  const requestId = key ? `${namespace}:${key}` : ""
  const [state, setState] = useState<MemoryDetailState>({
    requestId: "",
    memory: null,
    error: "",
  })
  const loading = Boolean(key) && state.requestId !== requestId

  useEffect(() => {
    if (!key) return
    let cancelled = false
    api.getMemory(key, namespace)
      .then((memory) => {
        if (cancelled) return
        setState({ requestId, memory, error: "" })
      })
      .catch((e: unknown) => {
        if (cancelled) return
        setState({ requestId, memory: null, error: e instanceof Error ? e.message : "Failed to load memory" })
      })
    return () => {
      cancelled = true
    }
  }, [key, namespace, requestId])

  const handleDelete = async () => {
    if (!key || !confirm(`Delete "${key}"?`)) return
    try {
      await api.deleteMemory(key, namespace)
      const listHref = namespace === "default" ? "/memories" : `/memories?ns=${encodeURIComponent(namespace)}`
      navigate(listHref)
    } catch (err) {
      setState((current) => ({
        ...current,
        error: err instanceof Error ? err.message : "Failed to delete memory",
      }))
    }
  }

  if (loading) return <div className="text-sm text-muted-foreground">Loading...</div>
  if (state.error) return <div className="text-sm text-destructive">{state.error}</div>
  if (!state.memory) return <div className="text-sm text-muted-foreground">Memory not found.</div>

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon-sm" onClick={() => navigate(-1)}>
            <ArrowLeft />
          </Button>
          <h2 className="text-lg font-semibold">{state.memory.title}</h2>
        </div>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          <Trash size={14} data-icon="inline-start" />
          Delete
        </Button>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
        <span>Key: <strong className="text-foreground">{state.memory.key}</strong></span>
        <span>Namespace: <strong className="text-foreground">{state.memory.namespace}</strong></span>
        <span>Updated: {state.memory.updated_at.slice(0, 16)}</span>
        <span>{state.memory.chars.toLocaleString()} chars, {state.memory.lines} lines</span>
      </div>

      {state.memory.tags.length > 0 && (
        <div className="flex gap-1">
          {state.memory.tags.map((t) => (
            <span key={t} className="rounded bg-primary/10 px-2 py-0.5 text-[0.65rem] text-primary">{t}</span>
          ))}
        </div>
      )}

      <pre className="rounded-lg border border-border bg-card p-4 text-xs leading-relaxed overflow-auto max-h-[60vh] whitespace-pre-wrap font-mono">
        {state.memory.content}
      </pre>
    </div>
  )
}
