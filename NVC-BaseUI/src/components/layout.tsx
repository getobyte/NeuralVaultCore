import { NavLink, Outlet } from "react-router-dom"
import { HardDrives, MagnifyingGlass, Plus, Upload, DownloadSimple, ChartBar, CalendarDots, Moon, Sun } from "@phosphor-icons/react"
import { useTheme } from "@/components/theme-provider"
import { Button } from "@/components/ui/button"

function Layout() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex min-h-svh">
      {/* Sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-sidebar p-4">
        <div className="mb-6 flex items-center gap-3">
          <img src="/logo-64.png" alt="NVC" className="size-10 rounded-lg hover:rotate-3 transition-transform duration-300" />
          <div>
            <h1 className="text-sm font-bold tracking-tight text-sidebar-primary leading-tight">
              NeuralVaultCore
            </h1>
            <p className="text-[0.6rem] text-muted-foreground">v1.0 — Cyber-Draco Legacy</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          <NavItem to="/" icon={<ChartBar weight="duotone" />} label="Dashboard" />
          <NavItem to="/memories" icon={<HardDrives weight="duotone" />} label="Memories" />
          <NavItem to="/calendar" icon={<CalendarDots weight="duotone" />} label="Calendar" />
          <NavItem to="/search" icon={<MagnifyingGlass weight="duotone" />} label="Search" />
          <NavItem to="/new" icon={<Plus weight="bold" />} label="New Memory" />
          <NavItem to="/import" icon={<Upload weight="duotone" />} label="Import" />
          <NavItem to="/export" icon={<DownloadSimple weight="duotone" />} label="Export" />
        </nav>

        <div className="mt-auto pt-4 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-primary"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
            {theme === "dark" ? "Cyan Mode" : "Dark Mode"}
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-200 ${
          isActive
            ? "bg-sidebar-accent text-sidebar-accent-foreground border-l-2 border-l-primary"
            : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
        }`
      }
    >
      {icon}
      {label}
    </NavLink>
  )
}

export default Layout
