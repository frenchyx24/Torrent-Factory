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
  const [movies, setMovies] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const navigate = useNavigate();

  const loadLibrary = async () => {
    try {
      const res = await fetch('/api/library/movies');
      const data = await res.json();
      setMovies(data);
    } catch (e) {
      console.error("Erreur chargement bibliothèque");
    }
  };

  const fetchMovies = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/movies', { method: 'POST' });
      if (!res.ok) {
        showError("Erreur serveur pendant le scan des films");
      } else {
        const payload = await res.json();
        if (payload.status !== 'ok') {
          showError("Scan films retourné avec erreurs");
        } else {
          if (Array.isArray(payload.items)) setMovies(payload.items);
          else await loadLibrary();
          showSuccess("Scan des films terminé");
        }
      }
    } catch (e) {
      showError("Erreur lors du scan");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (items: any[]) => {
    const tasks = items.map(item => ({
      ...item,
      mode: 'movie',
      lang_tag: (document.getElementById(`tag-${item.name}`) as HTMLSelectElement)?.value || item.detected_tag
    }));

    try {
      const res = await fetch('/api/tasks/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks, type: 'movies' })
      });
      if (!res.ok) {
        showError('Erreur lors de l\'ajout des tâches');
        return;
      }
      const payload = await res.json();
      const added = Array.isArray(payload.added) ? payload.added : [];
      if (added.length === 0) {
        showError('Aucune tâche ajoutée (vérifiez que les sources existent)');
        return;
      }
      showSuccess(`${added.length} film(s) envoyé(s)`);
      navigate('/tasks');
    } catch (e) {
      showError("Erreur lors du lancement");
    }
  };

  useEffect(() => {
    loadLibrary();
  }, []);

  const filteredMovies = movies.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));

  const debugUrl = '/api/debug';

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight">Bibliothèque Films</h2>
          <p className="text-slate-400 mt-1">Gérez vos films et générez des torrents.</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={fetchMovies} disabled={loading} variant="outline" className="bg-slate-800 border-white/10 text-white hover:bg-slate-700">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Scanner
          </Button>
          <Button 
            disabled={selected.length === 0}
            onClick={() => handleGenerate(movies.filter(m => selected.includes(m.name)))}
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
            placeholder="Rechercher un film..." 
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
                  onCheckedChange={(checked) => setSelected(checked ? filteredMovies.map(m => m.name) : [])}
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
              <TableRow key={i} className="border-white/5 hover:bg-white/5 transition-all group">
                <TableCell className="text-center">
                  <Checkbox 
                    className="border-white/20 data-[state=checked]:bg-indigo-600" 
                    checked={selected.includes(movie.name)} 
                    onCheckedChange={(checked) => setSelected(prev => checked ? [...prev, movie.name] : prev.filter(n => n !== movie.name))}
                  />
                </TableCell>
                <TableCell className="font-semibold text-slate-100 group-hover:text-white transition-colors">{movie.name}</TableCell>
                <TableCell>
                  <select id={`tag-${movie.name}`} className="bg-slate-950 border border-white/10 text-slate-300 rounded-lg p-1.5 text-xs focus:ring-1 focus:ring-indigo-500 outline-none">
                    <option value="MULTI" selected={movie.detected_tag === 'MULTI'}>MULTI</option>
                    <option value="FRENCH" selected={movie.detected_tag === 'FRENCH'}>FRENCH</option>
                    <option value="VOSTFR" selected={movie.detected_tag === 'VOSTFR'}>VOSTFR</option>
                    <option value="VO" selected={movie.detected_tag === 'VO'}>VO</option>
                  </select>
                </TableCell>
                <TableCell><Badge variant="outline" className="border-white/10 text-slate-400">{movie.size}</Badge></TableCell>
                <TableCell className="text-right pr-6">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:bg-amber-500/10 hover:text-amber-400 transition-all rounded-full" onClick={() => handleGenerate([movie])}>
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