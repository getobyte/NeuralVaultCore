import { useState } from "react"
import { Link } from "react-router-dom"
import { api, memoryDetailHref, type Memory } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { MagnifyingGlass } from "@phosphor-icons/react"

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<Memory[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const r = await api.search(query)
      setResults(r.memories)
    } catch (err: unknown) {
      setResults(null)
      setError(err instanceof Error ? err.message : "Search failed.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4 animate-fade-in-up">
      <h2 className="text-lg font-semibold">Search</h2>

      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories..."
          className="flex-1"
        />
        <Button type="submit" disabled={loading}>
          <MagnifyingGlass size={14} data-icon="inline-start" />
          Search
        </Button>
      </form>

      {loading && <div className="text-sm text-muted-foreground">Searching...</div>}

      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {results !== null && !loading && (
        results.length === 0 ? (
          <p className="text-sm text-muted-foreground italic py-8 text-center">No results for "{query}"</p>
        ) : (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">{results.length} result(s)</p>
            {results.map((m) => (
              <Link
                key={`${m.namespace}:${m.key}`}
                to={memoryDetailHref(m)}
                className="block rounded-md border border-border bg-card px-3 py-2 transition-colors hover:bg-accent hover:-translate-y-0.5 transition-transform duration-200"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-primary">{m.key}</span>
                  <span className="text-muted-foreground">{m.namespace}</span>
                </div>
                <div className="mt-0.5 text-xs">{m.title}</div>
                {m.tags.length > 0 && (
                  <div className="mt-1 flex gap-1">
                    {m.tags.map((t) => (
                      <span key={t} className="rounded bg-primary/10 px-1.5 py-0.5 text-[0.6rem] text-primary">{t}</span>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )
      )}
    </div>
  )
}
