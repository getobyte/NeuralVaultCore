import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api, memoryDetailHref, type StorageStats, type Memory } from "@/lib/api"

export default function DashboardPage() {
  const [stats, setStats] = useState<StorageStats | null>(null)
  const [recent, setRecent] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.getStats(),
      api.getMemories({ limit: 5 }),
    ]).then(([s, r]) => {
      setStats(s)
      setRecent(r.memories)
      setError(null)
    }).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load dashboard.")
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-muted-foreground text-sm">Loading...</div>

  return (
    <div className="space-y-6 animate-fade-in-up">
      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="flex justify-center pb-2">
        <img src="/NVC-logo.png" alt="NeuralVaultCore" className="h-36 drop-shadow-lg" />
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Memories" value={stats.total_memories} />
          <StatCard label="Total chars" value={stats.total_chars.toLocaleString()} />
          <StatCard label="Namespaces" value={stats.namespaces} />
          <StatCard label="DB size" value={`${stats.db_size_kb} KB`} />
        </div>
      )}

      <div>
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">Recent memories</h3>
        {recent.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">No memories yet.</p>
        ) : (
          <div className="space-y-1">
            {recent.map((m) => (
              <Link
                key={`${m.namespace}:${m.key}`}
                to={memoryDetailHref(m)}
                className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-2 text-xs transition-colors hover:bg-accent hover:-translate-y-0.5 transition-transform duration-200"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-medium truncate">{m.title}</span>
                  <span className="text-muted-foreground shrink-0">{m.namespace}</span>
                </div>
                <span className="text-muted-foreground shrink-0 ml-3">{m.updated_at.slice(0, 16)}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 hover:scale-[1.02] hover:-translate-y-0.5 transition-transform duration-200">
      <div className="text-xl font-bold text-primary">{value}</div>
      <div className="text-[0.65rem] text-muted-foreground">{label}</div>
    </div>
  )
}
