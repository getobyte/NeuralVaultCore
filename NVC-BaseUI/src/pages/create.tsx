import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api, memoryDetailHref } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"

export default function CreatePage() {
  const navigate = useNavigate()
  const [namespaces, setNamespaces] = useState<string[]>([])
  const [form, setForm] = useState({ key: "", title: "", namespace: "default", tags: "", content: "" })
  const [customNs, setCustomNs] = useState("")
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getNamespaces()
      .then((items) => {
        setNamespaces(items)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load namespaces")
      })
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSaving(true)
    try {
      const ns = customNs.trim() || form.namespace
      await api.createMemory({ ...form, namespace: ns })
      navigate(memoryDetailHref({ key: form.key, namespace: ns }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to store")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-xl space-y-4 animate-fade-in-up">
      <h2 className="text-lg font-semibold">New Memory</h2>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Key</label>
          <Input value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} required placeholder="my-memory-key" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Title</label>
          <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Optional title" />
        </div>
        <div className="flex gap-2">
          <div className="flex-1">
            <label className="mb-1 block text-xs font-medium text-muted-foreground">Namespace</label>
            <select
              value={form.namespace}
              onChange={(e) => setForm({ ...form, namespace: e.target.value })}
              className="flex h-8 w-full rounded-md border border-input bg-transparent px-2 py-1 text-sm"
            >
              <option value="default">default</option>
              {namespaces.filter((n) => n !== "default").map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="mb-1 block text-xs font-medium text-muted-foreground">...or new</label>
            <Input value={customNs} onChange={(e) => setCustomNs(e.target.value)} placeholder="new-namespace" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Tags (comma-separated)</label>
          <Input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="tag1, tag2" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Content</label>
          <Textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} required rows={10} placeholder="Memory content..." />
        </div>

        {error && <p className="text-xs text-destructive">{error}</p>}

        <Button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Store Memory"}
        </Button>
      </form>
    </div>
  )
}
