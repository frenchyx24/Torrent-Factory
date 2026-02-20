"use client";

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Tv, 
  Film, 
  FolderCheck, 
  Activity, 
  Terminal, 
  Settings, 
  Zap,
  ChevronRight
} from 'lucide-react';
import { cn } from "@/lib/utils";
import { translations, Language } from '@/lib/i18n';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const [lang, setLang] = useState<Language>('fr');

  useEffect(() => {
    fetch('/api/config').then(res => res.json()).then(data => {
      if (data.language) setLang(data.language);
    });
  }, []);

  const t = translations[lang].nav;

  const navItems = [
    { name: t.series, path: '/', icon: Tv },
    { name: t.movies, path: '/movies', icon: Film },
    { name: t.torrents, path: '/torrents', icon: FolderCheck },
    { name: t.tasks, path: '/tasks', icon: Activity },
    { name: t.logs, path: '/logs', icon: Terminal },
    { name: t.settings, path: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-200 overflow-hidden font-sans">
      <aside className="w-64 border-r border-white/10 bg-slate-900/50 backdrop-blur-xl flex flex-col p-6">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-500/20">
            <Zap className="w-6 h-6 text-white fill-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">Torrent Factory</h1>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                  isActive 
                    ? "bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-600" 
                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                )}
              >
                <item.icon className={cn("w-5 h-5", isActive ? "text-indigo-400" : "group-hover:text-white")} />
                <span className="font-medium">{item.name}</span>
                {isActive && <ChevronRight className="ml-auto w-4 h-4 opacity-50" />}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto pt-6 border-t border-white/5">
          <div className="bg-slate-800/50 rounded-xl p-4 text-xs text-slate-500">
            <p>Version v1.0.6</p>
            <p className="mt-1">© 2024 Torrent Factory</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_10%_20%,rgba(99,102,241,0.05)_0%,transparent_40%),radial-gradient(circle_at_90%_80%,rgba(16,185,129,0.03)_0%,transparent_40%)]">
        <div className="max-w-7xl mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;