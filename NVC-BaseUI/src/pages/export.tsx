import { useEffect, useState } from "react"
import { api, type Memory } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { DownloadSimple, FileText, Code } from "@phosphor-icons/react"

type ExportFormat = "json" | "text"

function memoriesToJson(memories: Memory[]): string {
  return JSON.stringify(
    {
      memories: memories.map((m) => ({
        key: m.key,
        title: m.title,
        content: m.content,
        namespace: m.namespace,
        tags: m.tags,
        created_at: m.created_at,
        updated_at: m.updated_at,
      })),
      count: memories.length,
      exported_at: new Date().toISOString(),
    },
    null,
    2
  )
}

function memoriesToText(memories: Memory[]): string {
  return memories
    .map((m) => {
      const tags = m.tags.length > 0 ? `Tags: ${m.tags.join(", ")}` : ""
      return [
        `# ${m.title}`,
        `Key: ${m.key} | Namespace: ${m.namespace} | Updated: ${m.updated_at.slice(0, 16)}`,
        tags,
        "",
        m.content,
      ]
        .filter(Boolean)
        .join("\n")
    })
    .join("\n\n---\n\n")
}

function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function ExportPage() {
  const [format, setFormat] = useState<ExportFormat>("json")
  const [ns, setNs] = useState("")
  const [namespaces, setNamespaces] = useState<string[]>([])
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getNamespaces()
      .then((items) => {
        setNamespaces(items)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load namespaces.")
      })
  }, [])

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getMemories({ ns: ns || undefined, limit: 10000 })
      setMemories(res.memories)
      const content = format === "json" ? memoriesToJson(res.memories) : memoriesToText(res.memories)
      setPreview(content)
    } catch (err: unknown) {
      setPreview("")
      setMemories([])
      setError(err instanceof Error ? err.message : "Failed to export memories.")
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!preview) return
    const ext = format === "json" ? "json" : "txt"
    const mime = format === "json" ? "application/json" : "text/plain"
    const timestamp = new Date().toISOString().slice(0, 10)
    const nsLabel = ns ? `-${ns}` : ""
    downloadFile(preview, `nvc-export${nsLabel}-${timestamp}.${ext}`, mime)
  }

  return (
    <div className="max-w-2xl space-y-4 animate-fade-in-up">
      <h2 className="text-lg font-semibold">Export Memories</h2>

      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Format</label>
          <div className="flex gap-2">
            <Button
              variant={format === "json" ? "default" : "outline"}
              size="sm"
              onClick={() => { setFormat("json"); setPreview("") }}
            >
              <Code size={14} data-icon="inline-start" />
              JSON
            </Button>
            <Button
              variant={format === "text" ? "default" : "outline"}
              size="sm"
              onClick={() => { setFormat("text"); setPreview("") }}
            >
              <FileText size={14} data-icon="inline-start" />
              Plain Text
            </Button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Namespace</label>
          <select
            value={ns}
            onChange={(e) => { setNs(e.target.value); setPreview("") }}
            className="flex h-8 rounded-md border border-input bg-transparent px-2 py-1 text-sm"
          >
            <option value="">All</option>
            {namespaces.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div className="pt-4">
          <Button onClick={handleExport} disabled={loading}>
            {loading ? "Loading..." : "Generate"}
          </Button>
        </div>
      </div>

      {preview && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {memories.length} memories — {(preview.length / 1024).toFixed(1)} KB
            </span>
            <Button size="sm" onClick={handleDownload}>
              <DownloadSimple size={14} data-icon="inline-start" />
              Download
            </Button>
          </div>
          <pre className="max-h-[400px] overflow-auto rounded-lg border border-border bg-card p-4 text-[0.65rem] leading-relaxed font-mono whitespace-pre-wrap">
            {preview.slice(0, 5000)}{preview.length > 5000 ? "\n\n... (truncated in preview)" : ""}
          </pre>
        </div>
      )}
    </div>
  )
}
