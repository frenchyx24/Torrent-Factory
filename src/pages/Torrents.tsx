"use client";

import React from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { FileText, RefreshCw, ExternalLink } from 'lucide-react';

const mockTorrents = {
  series: [
    "The Last of Us S01 MULTI.torrent",
    "Shogun S01 MULTI.torrent",
    "The Bear S02 FRENCH.torrent"
  ],
  movies: [
    "Dune Part Two MULTI.torrent",
    "Oppenheimer VOSTFR.torrent"
  ]
};

const Torrents = () => {
  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Torrents Créés</h2>
          <p className="text-slate-400 mt-1">Liste des fichiers .torrent générés.</p>
        </div>
        <Button variant="outline" className="bg-white/5 border-white/10 hover:bg-white/10 text-white">
          <RefreshCw className="w-4 h-4 mr-2" />
          Actualiser
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Series Torrents */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
            Séries
          </h3>
          <div className="space-y-2">
            {mockTorrents.series.map((t, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 hover:border-indigo-500/50 transition-all group">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileText className="w-5 h-5 text-indigo-400 shrink-0" />
                  <span className="text-slate-300 truncate text-sm">{t}</span>
                </div>
                <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-white">
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>

        {/* Movies Torrents */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            Films
          </h3>
          <div className="space-y-2">
            {mockTorrents.movies.map((t, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5 hover:border-emerald-500/50 transition-all group">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileText className="w-5 h-5 text-emerald-400 shrink-0" />
                  <span className="text-slate-300 truncate text-sm">{t}</span>
                </div>
                <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-white">
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Torrents;