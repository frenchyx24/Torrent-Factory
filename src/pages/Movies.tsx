"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, RefreshCw, Zap, Film } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';

const Movies = () => {
  const [movies, setMovies] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchMovies = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/movies');
      const data = await res.json();
      setMovies(data);
    } catch (e) {
      showError("Erreur lors du scan des films");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMovies(); }, []);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Bibliothèque Films</h2>
          <p className="text-slate-400 mt-1">Gérez vos films et générez des torrents.</p>
        </div>
        <Button onClick={fetchMovies} disabled={loading} variant="outline" className="bg-white/5 border-white/10 text-white">
          <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
          Scanner
        </Button>
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
              <TableHead className="text-slate-400">NOM</TableHead>
              <TableHead className="text-slate-400">LANGUE</TableHead>
              <TableHead className="text-right text-slate-400">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {movies.filter(m => m.name.toLowerCase().includes(search.toLowerCase())).map((movie, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5">
                <TableCell className="font-bold text-white">{movie.name}</TableCell>
                <TableCell>
                  <Select defaultValue="MULTI">
                    <SelectTrigger className="w-32 bg-slate-950/50 border-white/10 text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-white/10 text-white">
                      <SelectItem value="MULTI">MULTI</SelectItem>
                      <SelectItem value="FRENCH">FRENCH</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="ghost" className="text-amber-500">
                    <Zap className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {movies.length === 0 && !loading && (
              <TableRow><TableCell colSpan={3} className="text-center py-10 text-slate-500">Aucun film trouvé dans le dossier source.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Layout>
  );
};

import { cn } from "@/lib/utils";
export default Movies;