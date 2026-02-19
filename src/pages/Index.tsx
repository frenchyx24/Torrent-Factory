"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { RefreshCw, Layers, Zap, Search, Loader2 } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { showSuccess, showError } from '@/utils/toast';
import { useNavigate } from 'react-router-dom';

const Index = () => {
  const [series, setSeries] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const navigate = useNavigate();

  const fetchSeries = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/series', { method: 'POST' });
      const data = await res.json();
      setSeries(data);
      showSuccess("Scan des séries terminé");
    } catch (e) {
      showError("Erreur lors du scan");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (items: any[]) => {
    const tasks = items.map(item => ({
      ...item,
      mode: (document.getElementById(`mode-${item.name}`) as HTMLSelectElement)?.value || 'complete',
      lang_tag: (document.getElementById(`tag-${item.name}`) as HTMLSelectElement)?.value || item.detected_tag
    }));

    try {
      const res = await fetch('/api/tasks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks, type: 'séries' })
      });
      if (res.ok) {
        showSuccess(`${tasks.length} série(s) envoyée(s)`);
        navigate('/tasks');
      }
    } catch (e) {
      showError("Erreur lors du lancement");
    }
  };

  useEffect(() => {
    fetch('/api/library/series').then(res => res.json()).then(setSeries);
  }, []);

  const filteredSeries = series.filter(s => s.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Bibliothèque Séries</h2>
          <p className="text-slate-400 mt-1">Génération intelligente par packs ou saisons.</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchSeries} disabled={loading} variant="outline" className="bg-white/5 border-white/10 hover:bg-white/10 text-white transition-all">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Scanner
          </Button>
          <Button 
            disabled={selected.length === 0}
            onClick={() => handleGenerate(series.filter(s => selected.includes(s.name)))}
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20 px-6"
          >
            <Layers className="w-4 h-4 mr-2" />
            Tout Générer ({selected.length})
          </Button>
        </div>
      </div>

      <div className="bg-slate-900/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 mb-6 ring-1 ring-white/5">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Rechercher une série..." 
            className="pl-10 bg-slate-950/50 border-white/10 text-white placeholder:text-slate-600 focus:ring-indigo-500/50"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900/30 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-sm">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="w-12 text-center">
                <Checkbox 
                  className="border-white/20 data-[state=checked]:bg-indigo-600" 
                  onCheckedChange={(checked) => setSelected(checked ? filteredSeries.map(s => s.name) : [])}
                />
              </TableHead>
              <TableHead className="text-slate-400 font-semibold py-4">NOM DE LA SÉRIE</TableHead>
              <TableHead className="text-slate-400 font-semibold">LANGUE</TableHead>
              <TableHead className="text-slate-400 font-semibold">MODE</TableHead>
              <TableHead className="text-right text-slate-400 font-semibold pr-6">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredSeries.map((item, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5 transition-all group">
                <TableCell className="text-center">
                  <Checkbox 
                    className="border-white/20 data-[state=checked]:bg-indigo-600" 
                    checked={selected.includes(item.name)} 
                    onCheckedChange={(checked) => setSelected(prev => checked ? [...prev, item.name] : prev.filter(n => n !== item.name))}
                  />
                </TableCell>
                <TableCell>
                  <div className="font-semibold text-slate-100 group-hover:text-white transition-colors">{item.name}</div>
                  <Badge variant="outline" className="mt-1 text-[10px] py-0 border-indigo-500/20 text-indigo-400 bg-indigo-500/5">{item.size}</Badge>
                </TableCell>
                <TableCell>
                  <select id={`tag-${item.name}`} className="bg-slate-950 border border-white/10 text-slate-300 rounded-lg p-1.5 text-xs focus:ring-1 focus:ring-indigo-500 outline-none">
                    <option value="MULTI" selected={item.detected_tag === 'MULTI'}>MULTI</option>
                    <option value="FRENCH" selected={item.detected_tag === 'FRENCH'}>FRENCH</option>
                    <option value="VOSTFR" selected={item.detected_tag === 'VOSTFR'}>VOSTFR</option>
                  </select>
                </TableCell>
                <TableCell>
                  <select id={`mode-${item.name}`} className="bg-slate-950 border border-white/10 text-slate-300 rounded-lg p-1.5 text-xs focus:ring-1 focus:ring-indigo-500 outline-none">
                    <option value="complete">Pack Complet</option>
                    <option value="season">Par Saison</option>
                    <option value="episode">Par Épisode</option>
                  </select>
                </TableCell>
                <TableCell className="text-right pr-6">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:bg-amber-500/10 hover:text-amber-400 transition-all rounded-full" onClick={() => handleGenerate([item])}>
                    <Zap className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Layout>
  );
};

export default Index;