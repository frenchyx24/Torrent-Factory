"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RefreshCw, Layers, Zap, Search } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { showSuccess, showError } from '@/utils/toast';
import { cn } from "@/lib/utils";

const Index = () => {
  const [series, setSeries] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchSeries = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/scan/series');
      const data = await res.json();
      setSeries(data);
    } catch (e) {
      showError("Erreur lors du scan des séries");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSeries();
  }, []);

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Bibliothèque Séries</h2>
          <p className="text-slate-400 mt-1">Gérez vos séries et générez des torrents en masse.</p>
        </div>
        <div className="flex gap-3">
          <Button 
            onClick={fetchSeries} 
            disabled={loading}
            variant="outline" 
            className="bg-white/5 border-white/10 hover:bg-white/10 text-white"
          >
            <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
            Scanner
          </Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20">
            <Layers className="w-4 h-4 mr-2" />
            Tout Générer
          </Button>
        </div>
      </div>

      <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Rechercher une série..." 
            className="pl-10 bg-slate-950/50 border-white/10 text-white placeholder:text-slate-600"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow className="border-white/10 hover:bg-transparent">
              <TableHead className="w-12"><Checkbox className="border-white/20" /></TableHead>
              <TableHead className="text-slate-400 font-semibold">NOM</TableHead>
              <TableHead className="text-slate-400 font-semibold">LANGUE</TableHead>
              <TableHead className="text-slate-400 font-semibold">TAILLE</TableHead>
              <TableHead className="text-slate-400 font-semibold">MODE</TableHead>
              <TableHead className="text-right text-slate-400 font-semibold">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {series.filter(s => s.name.toLowerCase().includes(search.toLowerCase())).map((item, i) => (
              <TableRow key={i} className="border-white/5 hover:bg-white/5 transition-colors group">
                <TableCell><Checkbox className="border-white/20" /></TableCell>
                <TableCell className="font-bold text-white">{item.name}</TableCell>
                <TableCell>
                  <Select defaultValue="MULTI">
                    <SelectTrigger className="w-32 bg-slate-950/50 border-white/10 text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-white/10 text-white">
                      <SelectItem value="MULTI">MULTI</SelectItem>
                      <SelectItem value="FRENCH">FRENCH</SelectItem>
                      <SelectItem value="VOSTFR">VOSTFR</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 font-mono text-[10px]">
                    {item.size}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Select defaultValue="Pack">
                    <SelectTrigger className="w-32 bg-slate-950/50 border-white/10 text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-white/10 text-white">
                      <SelectItem value="Pack">Pack</SelectItem>
                      <SelectItem value="Saison">Saison</SelectItem>
                      <SelectItem value="EP">EP</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="ghost" className="text-amber-500 hover:text-amber-400 hover:bg-amber-500/10">
                    <Zap className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {series.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-10 text-slate-500">
                  Aucune série trouvée dans /data/series
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Layout>
  );
};

export default Index;