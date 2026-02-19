"use client";

import React from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Trash2, XCircle, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { cn } from "@/lib/utils";

const mockTasks = [
  { 
    id: '1', 
    name: 'Series - 4 item(s)', 
    status: 'running', 
    current: 'The Last of Us S01E04', 
    detail: '[1/4] Processing...', 
    progressItem: 65, 
    progressGlobal: 25, 
    eta: '02m 15s',
    time: '14:20'
  },
  { 
    id: '2', 
    name: 'Movies - 1 item(s)', 
    status: 'completed', 
    current: 'Dune Part Two', 
    detail: 'Finished', 
    progressItem: 100, 
    progressGlobal: 100, 
    eta: 'Terminé',
    time: '13:45'
  },
  { 
    id: '3', 
    name: 'Series - 2 item(s)', 
    status: 'error', 
    current: 'Succession S04', 
    detail: 'Timeout error', 
    progressItem: 40, 
    progressGlobal: 0, 
    eta: 'Erreur',
    time: '12:10'
  }
];

const Tasks = () => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'border-indigo-500';
      case 'completed': return 'border-emerald-500';
      case 'error': return 'border-rose-500';
      case 'cancelled': return 'border-amber-500';
      default: return 'border-slate-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Clock className="w-5 h-5 text-indigo-400 animate-pulse" />;
      case 'completed': return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'error': return <AlertCircle className="w-5 h-5 text-rose-400" />;
      default: return null;
    }
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Activités en cours</h2>
          <p className="text-slate-400 mt-1">Suivez la progression de vos créations de torrents.</p>
        </div>
        <Button variant="ghost" className="text-rose-500 hover:text-rose-400 hover:bg-rose-500/10">
          <Trash2 className="w-4 h-4 mr-2" />
          Nettoyer
        </Button>
      </div>

      <div className="space-y-4">
        {mockTasks.map((task) => (
          <div 
            key={task.id} 
            className={cn(
              "bg-slate-900/50 backdrop-blur-md border-l-4 rounded-2xl p-6 transition-all hover:bg-slate-900/70",
              getStatusColor(task.status)
            )}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(task.status)}
                <h3 className="text-lg font-bold text-white">{task.name}</h3>
              </div>
              {task.status === 'running' && (
                <Button size="sm" variant="destructive" className="bg-rose-600/20 text-rose-500 hover:bg-rose-600/30 border-none">
                  <XCircle className="w-4 h-4 mr-2" />
                  STOP
                </Button>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-300">
                  {task.current} <span className="text-indigo-400 ml-2 opacity-70">{task.detail}</span>
                </span>
                <span className="font-mono font-bold text-amber-400">{task.eta}</span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[10px] text-slate-500 uppercase tracking-wider">
                  <span>Fichier actuel</span>
                  <span>{task.progressItem}%</span>
                </div>
                <Progress value={task.progressItem} className="h-2 bg-white/5" />
                
                <div className="flex justify-between text-[10px] text-slate-500 uppercase tracking-wider">
                  <span>Progression globale</span>
                  <span>{task.progressGlobal}%</span>
                </div>
                <Progress value={task.progressGlobal} className="h-1 bg-white/5" />
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-500 mt-4">
                <Clock className="w-3 h-3" />
                <span>Créé à {task.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
};

export default Tasks;