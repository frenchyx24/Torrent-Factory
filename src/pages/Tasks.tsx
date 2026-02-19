"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Trash2, XCircle, CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from "@/lib/utils";

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/library/tasks');
      const data = await res.json();
      setTasks(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const stopTask = async (id: number) => {
    await fetch(`/api/tasks/stop/${id}`, { method: 'POST' });
    fetchTasks();
  };

  const cleanTasks = async () => {
    await fetch('/api/tasks/clean', { method: 'POST' });
    fetchTasks();
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Activités en cours</h2>
          <p className="text-slate-400 mt-1">Suivez la progression en temps réel.</p>
        </div>
        <Button onClick={cleanTasks} variant="ghost" className="text-rose-500 hover:bg-rose-500/10">
          <Trash2 className="w-4 h-4 mr-2" />
          Nettoyer
        </Button>
      </div>

      <div className="space-y-4">
        {tasks.length > 0 ? tasks.map((task: any) => (
          <div key={task.id} className={cn("bg-slate-900/50 backdrop-blur-md border-l-4 rounded-2xl p-6 transition-all", task.status === 'running' ? 'border-indigo-500' : 'border-emerald-500')}>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                {task.status === 'running' ? <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                <h3 className="text-lg font-bold text-white">{task.name}</h3>
              </div>
              {task.status === 'running' && (
                <Button size="sm" variant="destructive" className="bg-rose-600/20 text-rose-500 border-none" onClick={() => stopTask(task.id)}>
                  <XCircle className="w-4 h-4 mr-2" />
                  STOP
                </Button>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-300">{task.current}</span>
                <span className="font-mono text-amber-400">{task.progress}%</span>
              </div>
              <Progress value={task.progress} className="h-2 bg-white/5" />
            </div>
          </div>
        )) : !loading && (
          <div className="text-center py-20 text-slate-500 italic">Aucune tâche en cours d'exécution.</div>
        )}
      </div>
    </Layout>
  );
};

export default Tasks;