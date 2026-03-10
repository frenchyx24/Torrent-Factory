"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, RefreshCw, Zap, Loader2, Layers } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { showSuccess, showError } from '@/utils/toast';
import { useNavigate } from 'react-router-dom';

const Movies = () => {
  const [movies, setMovies] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const navigate = useNavigate();

  const loadLibrary = async () => {
    try {
      const res = await fetch('/api/library/movies');
      const data = await res.json();
      setMovies(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMovies = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/movies', { method: 'POST' });
      const data = await res.json();
      if (Array.isArray(data)) setMovies(data);
      else if (data && Array.isArray(data.items)) setMovies(data.items);
      showSuccess("Scan terminé");
    } catch (e) {
      showError("Erreur scan");
    } finally { setLoading(false); }
  };

  const handleGenerate = async (items: any[]) => {
    const tasks = items.map(item => ({
      ...item,
      mode: 'movie',
      lang_tag: (document.getElementById(`tag-${item.name}`) as HTMLSelectElement)?.value || item.detected_tag || 'MULTI'
    }));

    try {
      const res = await fetch('/api/tasks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks, type: 'movies' })
      });
      if (res.ok) {
        showSuccess("Films envoyés");
        navigate('/tasks');
      }
    } catch (e) { showError("Erreur"); }
  };

  useEffect(() => { loadLibrary(); }, []);

  const filteredMovies = Array.isArray(movies) ? movies.filter(m => (m.name || '').toLowerCase().includes(search.toLowerCase())) : [];

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Bibliothèque Films</h2>
          <p className="text-slate-400 mt-1">Gérez vos films et générez des torrents.</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchMovies} disabled={loading} variant="outline" className="bg-slate-800 border-white/10 text-white">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Scanner
          </Button>
          <Button 
            disabled={selected.length === 0}
            onClick={() => handleGenerate(movies.filter(m => selected.includes(m.name)))}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6"
          >
            <Layers className="w-4 h-4 mr-2" />
            Tout Générer ({selected.length})
          </Button>
        </div>
      </div>

      <div className="bg-slate-900/40 backdrop-blur-xl border border-white/10 rounded-2xl p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Rechercher un film..." 
            className="pl-10 bg-slate-950/50 border-white/10 text-white"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900/30 border border-white/10 rounded-2xl overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="w-12 text-center">
                <Checkbox 
                  className="border-white/20" 
                  onCheckedChange={(checked) => setSelected(checked === true ? filteredMovies.map(m => m.name) : [])}
                />
              </TableHead>
              <TableHead className="text-slate-400 font-semibold py-4">NOM DU FILM</TableHead>
              <TableHead className="text-slate-400 font-semibold">LANGUE</TableHead>
              <TableHead className="text-slate-400 font-semibold">TAILLE</TableHead>
              <TableHead className="text-right text-slate-400 font-semibold pr-6">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredMovies.map((movie, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5 group">
                <TableCell className="text-center">
                  <Checkbox 
                    className="border-white/20" 
                    checked={selected.includes(movie.name)} 
                    onCheckedChange={(checked) => setSelected(prev => checked === true ? [...prev, movie.name] : prev.filter(n => n !== movie.name))}
                  />
                </TableCell>
                <TableCell className="font-semibold text-slate-100">{movie.name}</TableCell>
                <TableCell>
                  <select 
                    id={`tag-${movie.name}`} 
                    defaultValue={movie.detected_tag || "MULTI"}
                    className="bg-slate-950 border border-white/10 text-slate-300 rounded-lg p-1.5 text-xs outline-none"
                  >
                    <option value="MULTI">MULTI</option>
                    <option value="FRENCH">FRENCH</option>
                    <option value="VOSTFR">VOSTFR</option>
                  </select>
                </TableCell>
                <TableCell><Badge variant="outline" className="border-white/10 text-slate-400">{movie.size}</Badge></TableCell>
                <TableCell className="text-right pr-6">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:bg-amber-500/10 rounded-full" onClick={() => handleGenerate([movie])}>
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

export default Movies;