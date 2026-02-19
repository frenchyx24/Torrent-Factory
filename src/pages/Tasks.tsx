"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Trash2, XCircle, CheckCircle2, Clock, Loader2, AlertCircle } from 'lucide-react';
import { cn } from "@/lib/utils";

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks/list');
      const data = await res.json();
      setTasks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const cancelTask = async (id: string) => {
    await fetch(`/api/tasks/cancel`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    });
    fetchTasks();
  };

  const clearTasks = async () => {
    await fetch('/api/tasks/clear');
    fetchTasks();
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Activités en cours</h2>
          <p className="text-slate-400 mt-1">Progression globale et par fichier.</p>
        </div>
        <Button onClick={clearTasks} variant="ghost" className="text-slate-400 hover:bg-white/5 hover:text-white">
          <Trash2 className="w-4 h-4 mr-2" />
          Nettoyer
        </Button>
      </div>

      <div className="space-y-6">
        {tasks.length > 0 ? tasks.slice().reverse().map((task: any) => (
          <div key={task.id} className={cn(
            "bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-6 transition-all",
            task.status === 'running' ? 'border-l-4 border-l-indigo-500' : 
            task.status === 'completed' ? 'border-l-4 border-l-emerald-500' : 
            task.status === 'cancelled' ? 'border-l-4 border-l-rose-500' : 'border-l-4 border-l-slate-700'
          )}>
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-3">
                {task.status === 'running' ? <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" /> : 
                 task.status === 'completed' ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> :
                 task.status === 'cancelled' ? <AlertCircle className="w-5 h-5 text-rose-400" /> : <Clock className="w-5 h-5 text-slate-500" />}
                <div>
                  <h3 className="text-lg font-bold text-white">{task.name}</h3>
                  <span className="text-xs text-slate-500">{task.created_at} • ID: {task.id}</span>
                </div>
              </div>
              {['running', 'pending'].includes(task.status) && (
                <Button size="sm" variant="destructive" className="bg-rose-600/20 text-rose-500 hover:bg-rose-600/30 border-none" onClick={() => cancelTask(task.id)}>
                  <XCircle className="w-4 h-4 mr-2" />
                  ANNULER
                </Button>
              )}
              {task.status === 'completed' && <Badge className="bg-emerald-500/10 text-emerald-500 border-none">TERMINÉ</Badge>}
            </div>

            <div className="space-y-5">
              {/* Item Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300 font-medium truncate max-w-[70%]">
                    {task.current_item_name}
                  </span>
                  <span className="font-mono text-indigo-400">{task.progress_item}%</span>
                </div>
                <Progress value={task.progress_item} className="h-2 bg-white/5" />
              </div>

              {/* Global Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase tracking-wider text-slate-500">
                  <span>Progression Globale ({task.current_item_index})</span>
                  <span>{task.progress_global}%</span>
                </div>
                <Progress value={task.progress_global} className="h-1 bg-white/5 opacity-50" />
              </div>
            </div>
          </div>
        )) : !loading && (
          <div className="text-center py-20 text-slate-500 italic flex flex-col items-center gap-4">
            <Clock className="w-12 h-12 opacity-20" />
            Aucune tâche en cours d'exécution.
          </div>
        )}
      </div>
    </Layout>
  );
};

const Badge = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <span className={cn("px-2 py-1 rounded text-[10px] font-bold border", className)}>
    {children}
  </span>
);

export default Tasks;