import { BrowserRouter, Routes, Route } from "react-router-dom"
import Layout from "@/components/layout"
import DashboardPage from "@/pages/dashboard"
import MemoriesPage from "@/pages/memories"
import MemoryDetailPage from "@/pages/memory-detail"
import SearchPage from "@/pages/search"
import CreatePage from "@/pages/create"
import ImportPage from "@/pages/import"
import ExportPage from "@/pages/export"
import CalendarPage from "@/pages/calendar"

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="memories" element={<MemoriesPage />} />
          <Route path="memories/:key" element={<MemoryDetailPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="new" element={<CreatePage />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="export" element={<ExportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
