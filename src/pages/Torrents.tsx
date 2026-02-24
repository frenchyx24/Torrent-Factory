"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { FileText, RefreshCw, ExternalLink, Loader2, FolderSearch } from 'lucide-react';

const Torrents = () => {
  const [torrents, setTorrents] = useState({ series: [], movies: [] });
  const [loading, setLoading] = useState(true);

  const fetchTorrents = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/torrents/list');
      const data = await res.json();
      setTorrents(data);
    } catch (e) {
      console.error("Erreur lors du chargement des torrents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTorrents();
  }, []);

  const debugUrl = '/api/debug';

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Torrents Créés</h2>
          <p className="text-slate-400 mt-1">Liste des fichiers .torrent réellement présents dans vos dossiers OUT.</p>
        </div>
        <Button 
          onClick={fetchTorrents} 
          disabled={loading}
          variant="outline" 
          className="bg-white/5 border-white/10 hover:bg-white/10 text-white"
        >
          {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
          Actualiser
        </Button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500">
          <Loader2 className="w-12 h-12 animate-spin mb-4 opacity-20" />
          <p>Lecture des répertoires...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Series Torrents */}
          <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
              Séries ({torrents.series.length})
            </h3>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
              {torrents.series.length > 0 ? torrents.series.map((t, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 hover:border-indigo-500/50 transition-all group">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-5 h-5 text-indigo-400 shrink-0" />
                    <div className="truncate">
                      <div className="text-slate-300 truncate text-sm">{t.name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{formatBytes(t.size)} • {formatDate(t.mtime)}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a href={`/api/torrents/download?path=${encodeURIComponent(t.path)}`} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-white">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                    <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 text-rose-400 hover:text-white" onClick={() => handleDelete(t.path)}>
                      Suppr
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-600 text-sm italic">
                  <div>Aucun torrent trouvé.</div>
                  <a className="text-xs text-indigo-400 mt-2 inline-block" href={debugUrl} target="_blank" rel="noreferrer">Voir le debug</a>
                </div>
              )}
            </div>
          </div>

          {/* Movies Torrents */}
          <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              Films ({torrents.movies.length})
            </h3>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
              {torrents.movies.length > 0 ? torrents.movies.map((t, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 hover:border-emerald-500/50 transition-all group">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-5 h-5 text-emerald-400 shrink-0" />
                    <div className="truncate">
                      <div className="text-slate-300 truncate text-sm">{t.name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{formatBytes(t.size)} • {formatDate(t.mtime)}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a href={`/api/torrents/download?path=${encodeURIComponent(t.path)}`} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-white">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                    <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 text-rose-400 hover:text-white" onClick={() => handleDelete(t.path)}>
                      Suppr
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-600 text-sm italic">
                  <div>Aucun torrent trouvé.</div>
                  <a className="text-xs text-emerald-400 mt-2 inline-block" href={debugUrl} target="_blank" rel="noreferrer">Voir le debug</a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

function formatBytes(bytes: number) {
  if (!bytes) return '0 B';
  const sizes = ['B','KB','MB','GB','TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

function formatDate(ts: number) {
  try {
    const d = new Date(ts * 1000);
    return d.toLocaleString();
  } catch (e) { return '' }
}

async function handleDelete(path: string) {
  if (!confirm('Supprimer ce fichier .torrent ?')) return;
  try {
    const res = await fetch('/api/torrents/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) });
    if (res.ok) {
      window.location.reload();
    } else {
      alert('Erreur suppression');
    }
  } catch (e) { alert('Erreur suppression'); }
}

export default Torrents;