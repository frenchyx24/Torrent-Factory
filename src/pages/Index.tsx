"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
        body: JSON.stringify({ tasks, type: 'series' })
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

  const toggleSelect = (name: string) => {
    setSelected(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Bibliothèque Séries</h2>
          <p className="text-slate-400 mt-1">Gérez vos séries et générez des torrents.</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchSeries} disabled={loading} variant="outline" className="bg-white/5 border-white/10 text-white">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Scanner
          </Button>
          <Button 
            disabled={selected.length === 0}
            onClick={() => handleGenerate(series.filter(s => selected.includes(s.name)))}
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20"
          >
            <Layers className="w-4 h-4 mr-2" />
            Tout Générer ({selected.length})
          </Button>
        </div>
      </div>

      <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Rechercher une série..." 
            className="pl-10 bg-slate-950/50 border-white/10 text-white"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900/50 border border-white/10 rounded-2xl overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/10">
              <TableHead className="w-12">
                <Checkbox 
                  className="border-white/20" 
                  onCheckedChange={(checked) => setSelected(checked ? filteredSeries.map(s => s.name) : [])}
                />
              </TableHead>
              <TableHead className="text-slate-400">NOM</TableHead>
              <TableHead className="text-slate-400">LANGUE</TableHead>
              <TableHead className="text-slate-400">MODE</TableHead>
              <TableHead className="text-right text-slate-400">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredSeries.map((item, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5 transition-colors">
                <TableCell><Checkbox className="border-white/20" checked={selected.includes(item.name)} onCheckedChange={() => toggleSelect(item.name)}/></TableCell>
                <TableCell>
                  <div className="font-bold text-white">{item.name}</div>
                  <Badge variant="outline" className="mt-1 text-[10px] py-0 border-white/10 text-slate-500">{item.size}</Badge>
                </TableCell>
                <TableCell>
                  <select id={`tag-${item.name}`} className="bg-slate-950/50 border border-white/10 text-white rounded p-1 text-xs">
                    <option value="">Auto</option>
                    <option value="MULTI" selected={item.detected_tag === 'MULTI'}>MULTI</option>
                    <option value="FRENCH" selected={item.detected_tag === 'FRENCH'}>FRENCH</option>
                    <option value="VOSTFR" selected={item.detected_tag === 'VOSTFR'}>VOSTFR</option>
                  </select>
                </TableCell>
                <TableCell>
                  <select id={`mode-${item.name}`} className="bg-slate-950/50 border border-white/10 text-white rounded p-1 text-xs">
                    <option value="complete">Pack</option>
                    <option value="season">Saison</option>
                    <option value="episode">EP</option>
                  </select>
                </TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:bg-amber-500/10" onClick={() => handleGenerate([item])}>
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