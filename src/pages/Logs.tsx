"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { Eraser, Download, Terminal } from 'lucide-react';

const mockLogs = [
  { id: 1, time: '14:20:05', msg: 'Serveur démarré sur le port 5000', level: 'info' },
  { id: 2, time: '14:20:10', msg: 'Scan de la bibliothèque séries terminé (4 items)', level: 'info' },
  { id: 3, time: '14:21:15', msg: 'Démarrage de la tâche: Series - 4 item(s)', level: 'info' },
  { id: 4, time: '14:21:16', msg: 'Analyse de The Last of Us S01E04...', level: 'info' },
  { id: 5, time: '14:22:30', msg: 'Erreur FFprobe sur Succession S04: Timeout', level: 'error' },
  { id: 6, time: '14:23:00', msg: 'Torrent créé: Dune Part Two.torrent', level: 'success' },
];

const Logs = () => {
  const [logs, setLogs] = useState(mockLogs);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Logs Système</h2>
          <p className="text-slate-400 mt-1">Historique des événements et erreurs.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="bg-white/5 border-white/10 hover:bg-white/10 text-white" onClick={() => setLogs([])}>
            <Eraser className="w-4 h-4 mr-2" />
            Effacer
          </Button>
          <Button variant="outline" className="bg-white/5 border-white/10 hover:bg-white/10 text-white">
            <Download className="w-4 h-4 mr-2" />
            Exporter
          </Button>
        </div>
      </div>

      <div className="bg-slate-950 border border-white/10 rounded-2xl p-6 font-mono text-sm h-[600px] overflow-y-auto shadow-2xl">
        <div className="flex items-center gap-2 text-indigo-400 mb-4 border-b border-white/5 pb-2">
          <Terminal className="w-4 h-4" />
          <span className="uppercase tracking-widest text-[10px] font-bold">Terminal Output</span>
        </div>
        <div className="space-y-1">
          {logs.length > 0 ? logs.map((log) => (
            <div key={log.id} className="group flex gap-4 py-0.5">
              <span className="text-slate-600 shrink-0">[{log.time}]</span>
              <span className={
                log.level === 'error' ? 'text-rose-400' : 
                log.level === 'success' ? 'text-emerald-400' : 
                'text-slate-300'
              }>
                {log.msg}
              </span>
            </div>
          )) : (
            <div className="text-slate-600 italic">Aucun log à afficher...</div>
          )}
          <div className="animate-pulse inline-block w-2 h-4 bg-indigo-500 ml-1 align-middle"></div>
        </div>
      </div>
    </Layout>
  );
};

export default Logs;