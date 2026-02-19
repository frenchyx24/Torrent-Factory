"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, RefreshCw, Zap, Loader2, Play } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { showSuccess, showError } from '@/utils/toast';
import { useNavigate } from 'react-router-dom';

const Movies = () => {
  const [movies, setMovies] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const navigate = useNavigate();

  const fetchMovies = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/movies', { method: 'POST' });
      const data = await res.json();
      setMovies(data);
    } catch (e) {
      showError("Erreur lors du scan");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (items: any[]) => {
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items, type: 'Film' })
      });
      if (res.ok) {
        showSuccess(`${items.length} film(s) ajouté(s)`);
        navigate('/tasks');
      }
    } catch (e) {
      showError("Erreur lors du lancement");
    }
  };

  useEffect(() => {
    fetch('/api/library/movies').then(res => res.json()).then(setMovies);
  }, []);

  const filteredMovies = movies.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Bibliothèque Films</h2>
          <p className="text-slate-400 mt-1">Gérez vos films et générez des torrents.</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchMovies} disabled={loading} variant="outline" className="bg-white/5 border-white/10 text-white">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Scanner
          </Button>
          <Button 
            disabled={selected.length === 0}
            onClick={() => handleGenerate(movies.filter(m => selected.includes(m.name)))}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Play className="w-4 h-4 mr-2" />
            Lancer ({selected.length})
          </Button>
        </div>
      </div>

      <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-4 mb-6">
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

      <div className="bg-slate-900/50 border border-white/10 rounded-2xl overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/10">
              <TableHead className="w-12"><Checkbox className="border-white/20" onCheckedChange={(checked) => setSelected(checked ? filteredMovies.map(m => m.name) : [])}/></TableHead>
              <TableHead className="text-slate-400">NOM</TableHead>
              <TableHead className="text-slate-400">TAILLE</TableHead>
              <TableHead className="text-right text-slate-400">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredMovies.map((movie, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5">
                <TableCell><Checkbox className="border-white/20" checked={selected.includes(movie.name)} onCheckedChange={(checked) => setSelected(prev => checked ? [...prev, movie.name] : prev.filter(n => n !== movie.name))}/></TableCell>
                <TableCell className="font-bold text-white">{movie.name}</TableCell>
                <TableCell><Badge variant="outline" className="border-white/10 text-slate-400">{movie.size}</Badge></TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:bg-amber-500/10" onClick={() => handleGenerate([movie])}>
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