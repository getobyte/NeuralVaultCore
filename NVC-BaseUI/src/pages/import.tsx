import { useState } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Upload, File } from "@phosphor-icons/react"

type ImportResult = { imported: number; total: number } | null

export default function ImportPage() {
  const [mode, setMode] = useState<"file" | "paste">("file")
  const [text, setText] = useState("")
  const [result, setResult] = useState<ImportResult>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const parseAndImport = async (raw: string) => {
    setError("")
    setResult(null)
    setLoading(true)

    try {
      // Try JSON first
      let memories: Array<{ key: string; content: string; title?: string; namespace?: string; tags?: string[] }> = []

      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) {
          memories = parsed
        } else if (parsed.memories && Array.isArray(parsed.memories)) {
          memories = parsed.memories
        } else if (parsed.key && parsed.content) {
          memories = [parsed]
        } else {
          throw new Error("not standard JSON format")
        }
      } catch {
        // Not JSON — treat as plain text
        // Split by separator lines (---, ===, blank lines between blocks)
        const blocks = raw.split(/\n(?:---+|===+)\n/).filter((b) => b.trim())

        if (blocks.length <= 1) {
          // Single block — one memory
          const lines = raw.trim().split("\n")
          const title = lines[0].replace(/^#+\s*/, "").trim()
          const key = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `import-${Date.now()}`
          memories = [{
            key,
            content: raw.trim(),
            title: title.slice(0, 100),
            namespace: "imported",
          }]
        } else {
          // Multiple blocks separated by ---
          memories = blocks.map((block, i) => {
            const lines = block.trim().split("\n")
            const title = lines[0].replace(/^#+\s*/, "").trim()
            const key = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || `import-${Date.now()}-${i}`
            return {
              key,
              content: block.trim(),
              title: title.slice(0, 100),
              namespace: "imported",
            }
          })
        }
      }

      if (memories.length === 0) {
        setError("No memories found in input.")
        return
      }

      // Validate each memory has key and content
      memories = memories.map((m, i) => ({
        key: m.key || `import-${Date.now()}-${i}`,
        content: m.content || "",
        title: m.title,
        namespace: m.namespace || "imported",
        tags: m.tags || ["imported"],
      })).filter((m) => m.content.trim())

      const res = await api.importMemories(memories)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed")
    } finally {
      setLoading(false)
    }
  }

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => {
      const content = reader.result as string
      parseAndImport(content)
    }
    reader.readAsText(file)
  }

  return (
    <div className="max-w-xl space-y-4 animate-fade-in-up">
      <h2 className="text-lg font-semibold">Import Memories</h2>

      <p className="text-xs text-muted-foreground">
        Import from JSON (NVC export format, array of objects, or single object) or plain text
        (separated by <code className="bg-muted px-1 rounded">---</code>). Auto-detected.
      </p>

      <div className="flex gap-2">
        <Button variant={mode === "file" ? "default" : "outline"} size="sm" onClick={() => setMode("file")}>
          <File size={14} data-icon="inline-start" />
          File
        </Button>
        <Button variant={mode === "paste" ? "default" : "outline"} size="sm" onClick={() => setMode("paste")}>
          <Upload size={14} data-icon="inline-start" />
          Paste
        </Button>
      </div>

      {mode === "file" ? (
        <div>
          <input
            type="file"
            accept=".json,.txt,.md,.csv"
            onChange={handleFile}
            className="block w-full text-xs text-muted-foreground file:mr-3 file:rounded file:border-0 file:bg-primary/10 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-primary hover:file:bg-primary/20"
          />
        </div>
      ) : (
        <div className="space-y-2">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            placeholder={'Paste JSON or plain text here...\n\nJSON format:\n[{"key": "...", "content": "...", "title": "..."}]\n\nPlain text (separate with ---):\nFirst memory title\nContent here\n---\nSecond memory title\nMore content'}
          />
          <Button onClick={() => parseAndImport(text)} disabled={loading || !text.trim()}>
            {loading ? "Importing..." : "Import"}
          </Button>
        </div>
      )}

      {error && <p className="text-xs text-destructive">{error}</p>}
      {result && (
        <div className="rounded-md border border-border bg-card p-3 text-xs">
          Imported <strong className="text-primary">{result.imported}</strong> of {result.total} memories.
        </div>
      )}
    </div>
  )
}
