"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Button } from "@/components/ui/button";
import { Eraser, Terminal } from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      const data = await res.json();
      setLogs(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div><h2 className="text-3xl font-bold text-white">Logs Système</h2></div>
        <Button variant="outline" className="text-white border-white/10" onClick={() => setLogs([])}><Eraser className="w-4 h-4 mr-2"/>Effacer</Button>
      </div>
      <div className="bg-black border border-white/10 rounded-2xl p-6 font-mono text-xs h-[600px] overflow-y-auto">
        {logs.map((l: any) => (
          <div key={l.id} className="flex gap-4 mb-1">
            <span className="text-slate-600">[{l.time}]</span>
            <span className={l.level === 'error' ? 'text-rose-400' : l.level === 'success' ? 'text-emerald-400' : 'text-slate-300'}>{l.msg}</span>
          </div>
        ))}
        <div className="animate-pulse w-2 h-4 bg-indigo-500 inline-block ml-1"></div>
      </div>
    </Layout>
  );
};

export default Logs;