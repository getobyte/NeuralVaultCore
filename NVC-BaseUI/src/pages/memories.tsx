import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { api, memoryDetailHref, type Memory } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { CaretLeft, CaretRight } from "@phosphor-icons/react"

type MemoriesState = {
  queryKey: string
  memories: Memory[]
  total: number
  namespaces: string[]
  error: string | null
}

export default function MemoriesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const ns = searchParams.get("ns") || ""
  const page = Number(searchParams.get("page") || "1")
  const limit = 25
  const queryKey = `${ns}:${page}`

  const [state, setState] = useState<MemoriesState>({
    queryKey: "",
    memories: [],
    total: 0,
    namespaces: [],
    error: null,
  })
  const loading = state.queryKey !== queryKey

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.getMemories({ ns: ns || undefined, limit, offset: (page - 1) * limit }),
      api.getNamespaces(),
    ]).then(([r, nsList]) => {
      if (cancelled) return
      setState({
        queryKey,
        memories: r.memories,
        total: r.total,
        namespaces: nsList,
        error: null,
      })
    }).catch((err: unknown) => {
      if (cancelled) return
      setState((prev) => ({
        ...prev,
        queryKey,
        memories: [],
        total: 0,
        error: err instanceof Error ? err.message : "Failed to load memories.",
      }))
    })
    return () => {
      cancelled = true
    }
  }, [limit, ns, page, queryKey])

  const totalPages = Math.max(1, Math.ceil(state.total / limit))

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Memories ({state.total})</h2>
        <select
          value={ns}
          onChange={(e) => setSearchParams(e.target.value ? { ns: e.target.value } : {})}
          className="rounded-md border border-input bg-transparent px-2 py-1 text-xs"
        >
          <option value="">All namespaces</option>
          {state.namespaces.map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {state.error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {state.error}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : state.memories.length === 0 ? (
        <p className="text-sm text-muted-foreground italic py-8 text-center">No memories found.</p>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Key</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Title</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Namespace</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Tags</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Updated</th>
                </tr>
              </thead>
              <tbody>
                {state.memories.map((m) => (
                  <tr key={`${m.namespace}:${m.key}`} className="border-b border-border last:border-0 transition-colors hover:bg-accent/50">
                    <td className="px-3 py-2">
                      <Link to={memoryDetailHref(m)} className="font-medium text-primary hover:underline">
                        {m.key}
                      </Link>
                    </td>
                    <td className="px-3 py-2 truncate max-w-[200px]">{m.title}</td>
                    <td className="px-3 py-2 text-muted-foreground">{m.namespace}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1 flex-wrap">
                        {m.tags.map((t) => (
                          <span key={t} className="rounded bg-primary/10 px-1.5 py-0.5 text-[0.6rem] text-primary">{t}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{m.updated_at.slice(0, 16)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button variant="outline" size="icon-sm" disabled={page <= 1}
                onClick={() => setSearchParams({ ...(ns ? { ns } : {}), page: String(page - 1) })}>
                <CaretLeft />
              </Button>
              <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
              <Button variant="outline" size="icon-sm" disabled={page >= totalPages}
                onClick={() => setSearchParams({ ...(ns ? { ns } : {}), page: String(page + 1) })}>
                <CaretRight />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
