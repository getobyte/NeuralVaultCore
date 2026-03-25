import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api, memoryDetailHref, type TimelineEntry, type TimelineResponse } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { CaretLeft, CaretRight, X } from "@phosphor-icons/react"

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
]

interface CalendarDay {
  date: number
  dateStr: string
  currentMonth: boolean
}

function buildCalendarGrid(year: number, month: number): CalendarDay[] {
  const firstDay = new Date(year, month - 1, 1)
  // getDay() returns 0=Sun, we want 0=Mon
  let startOffset = firstDay.getDay() - 1
  if (startOffset < 0) startOffset = 6

  const daysInMonth = new Date(year, month, 0).getDate()
  const daysInPrevMonth = new Date(year, month - 1, 0).getDate()

  const grid: CalendarDay[] = []

  // Previous month fill
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = daysInPrevMonth - i
    const prevMonth = month - 1 < 1 ? 12 : month - 1
    const prevYear = month - 1 < 1 ? year - 1 : year
    grid.push({
      date: d,
      dateStr: `${prevYear}-${String(prevMonth).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
      currentMonth: false,
    })
  }

  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    grid.push({
      date: d,
      dateStr: `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
      currentMonth: true,
    })
  }

  // Next month fill to complete grid (6 rows max)
  const totalCells = Math.ceil(grid.length / 7) * 7
  const nextMonth = month + 1 > 12 ? 1 : month + 1
  const nextYear = month + 1 > 12 ? year + 1 : year
  for (let d = 1; grid.length < totalCells; d++) {
    grid.push({
      date: d,
      dateStr: `${nextYear}-${String(nextMonth).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
      currentMonth: false,
    })
  }

  return grid
}

function todayStr(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`
}

export default function CalendarPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [ns, setNs] = useState("")
  const [namespaces, setNamespaces] = useState<string[]>([])
  const [data, setData] = useState<TimelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDay, setSelectedDay] = useState<string | null>(null)

  useEffect(() => {
    api.getNamespaces().then(setNamespaces).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    api
      .getTimeline({ year, month, ns: ns || undefined })
      .then((r) => {
        setData(r)
        setLoading(false)
      })
      .catch(() => {
        setData({ days: {}, total: 0 })
        setLoading(false)
      })
  }, [year, month, ns])

  const grid = buildCalendarGrid(year, month)
  const today = todayStr()

  function prevMonth() {
    if (month === 1) {
      setYear(year - 1)
      setMonth(12)
    } else {
      setMonth(month - 1)
    }
    setSelectedDay(null)
  }

  function nextMonth() {
    if (month === 12) {
      setYear(year + 1)
      setMonth(1)
    } else {
      setMonth(month + 1)
    }
    setSelectedDay(null)
  }

  const selectedEntries: TimelineEntry[] =
    selectedDay && data?.days[selectedDay] ? data.days[selectedDay] : []

  return (
    <div className="animate-fade-in-up flex gap-6">
      {/* Calendar grid */}
      <div className="flex-1 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon-sm" onClick={prevMonth}>
              <CaretLeft />
            </Button>
            <h2 className="text-lg font-semibold min-w-[180px] text-center">
              {MONTH_NAMES[month - 1]} {year}
            </h2>
            <Button variant="outline" size="icon-sm" onClick={nextMonth}>
              <CaretRight />
            </Button>
          </div>

          <select
            value={ns}
            onChange={(e) => setNs(e.target.value)}
            className="rounded-md border border-input bg-transparent px-2 py-1 text-xs"
          >
            <option value="">All namespaces</option>
            {namespaces.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : (
          <div className="rounded-lg border border-border overflow-hidden">
            {/* Weekday headers */}
            <div className="grid grid-cols-7 bg-muted/50 border-b border-border">
              {WEEKDAYS.map((d) => (
                <div key={d} className="px-2 py-1.5 text-center text-xs font-medium text-muted-foreground">
                  {d}
                </div>
              ))}
            </div>

            {/* Day cells */}
            <div className="grid grid-cols-7">
              {grid.map((day, i) => {
                const count = data?.days[day.dateStr]?.length ?? 0
                const isToday = day.dateStr === today
                const isSelected = day.dateStr === selectedDay

                return (
                  <button
                    key={i}
                    onClick={() => setSelectedDay(day.dateStr)}
                    className={`
                      relative flex flex-col items-center justify-start gap-1 p-2 min-h-[72px]
                      border-b border-r border-border text-xs transition-all
                      ${!day.currentMonth ? "text-muted-foreground/40 bg-muted/20" : ""}
                      ${day.currentMonth && !count ? "text-muted-foreground" : ""}
                      ${day.currentMonth && count ? "text-foreground" : ""}
                      ${isToday ? "ring-1 ring-primary ring-inset" : ""}
                      ${isSelected ? "bg-accent" : ""}
                      ${day.currentMonth ? "hover:shadow-[0_0_12px_rgba(0,255,255,0.1)]" : ""}
                      hover:bg-accent/50 cursor-pointer
                    `}
                  >
                    <span className={`text-sm font-medium ${isToday ? "text-primary" : ""}`}>
                      {day.date}
                    </span>
                    {count > 0 && (
                      <span className="rounded-full bg-primary/20 text-primary px-1.5 py-0.5 text-[0.6rem] font-medium">
                        {count}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {data && (
          <div className="text-xs text-muted-foreground">
            {data.total} {data.total === 1 ? "memory" : "memories"} this month
          </div>
        )}
      </div>

      {/* Side panel */}
      {selectedDay && (
        <div className="w-80 shrink-0 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">{selectedDay}</h3>
            <Button variant="ghost" size="icon-sm" onClick={() => setSelectedDay(null)}>
              <X size={14} />
            </Button>
          </div>

          {selectedEntries.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">No memories on this day.</p>
          ) : (
            <div className="space-y-2">
              {selectedEntries.map((m) => (
                <Link
                  key={`${m.namespace}:${m.key}`}
                  to={memoryDetailHref(m)}
                  className="block rounded-lg border border-border p-3 transition-colors hover:bg-accent/50"
                >
                  <div className="text-sm font-medium text-primary truncate">{m.title || m.key}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{m.namespace}</div>
                  {m.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mt-1.5">
                      {m.tags.map((t) => (
                        <span
                          key={t}
                          className="rounded bg-primary/10 px-1.5 py-0.5 text-[0.6rem] text-primary"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="text-[0.6rem] text-muted-foreground mt-1">
                    {m.updated_at.slice(0, 16)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
