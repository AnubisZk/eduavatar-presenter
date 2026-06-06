// Shared application frame with compact navigation between the requested pages.
import { Clapperboard, Home, MonitorPlay, Sparkles } from "lucide-react";

const navItems = [
  { id: "home", label: "Home", icon: Home },
  { id: "create", label: "Create", icon: Sparkles },
  { id: "preview", label: "Preview", icon: MonitorPlay },
  { id: "output", label: "Output", icon: Clapperboard },
];

export default function Layout({ activePage, setActivePage, children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <button
            className="flex items-center gap-3 text-left"
            onClick={() => setActivePage("home")}
            type="button"
          >
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-blue-700 text-white">
              <MonitorPlay size={22} />
            </span>
            <span>
              <span className="block text-base font-semibold text-slate-950">EduAvatar Presenter Studio</span>
              <span className="block text-sm text-slate-500">Consent-first presentation avatar workflow</span>
            </span>
          </button>
          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                    isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100"
                  }`}
                  type="button"
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
