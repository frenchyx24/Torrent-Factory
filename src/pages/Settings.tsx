"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Save, Globe, ShieldCheck, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';

const Settings = () => {
  const [config, setConfig] = useState({
    series_root: "",
    series_out: "",
    movies_root: "",
    movies_out: "",
    tracker: "",
    private: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setConfig(data);
        setLoading(false);
      })
      .catch(() => {
        showError("Impossible de charger la configuration");
        setLoading(false);
      });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        showSuccess("Configuration enregistrée avec succès");
      } else {
        throw new Error();
      }
    } catch (e) {
      showError("Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[60vh]">
          <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white">Configuration</h2>
        <p className="text-slate-400 mt-1">Personnalisez le comportement de Torrent Factory.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-indigo-400" />
              Chemins Système
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Séries (Source)</Label>
              <Input 
                className="bg-slate-950/50 border-white/10 text-white" 
                value={config.series_root}
                onChange={(e) => setConfig({...config, series_root: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Séries (Destination)</Label>
              <Input 
                className="bg-slate-950/50 border-white/10 text-white" 
                value={config.series_out}
                onChange={(e) => setConfig({...config, series_out: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Films (Source)</Label>
              <Input 
                className="bg-slate-950/50 border-white/10 text-white" 
                value={config.movies_root}
                onChange={(e) => setConfig({...config, movies_root: e.target.value})}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Globe className="w-5 h-5 text-indigo-400" />
              Réseau
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Tracker URL</Label>
              <Input 
                className="bg-slate-950/50 border-white/10 text-white" 
                value={config.tracker}
                onChange={(e) => setConfig({...config, tracker: e.target.value})}
              />
            </div>
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div className="space-y-0.5">
                <Label className="text-white">Mode Privé</Label>
                <p className="text-xs text-slate-500">Ajoute le flag privé aux torrents.</p>
              </div>
              <Switch 
                checked={config.private} 
                onCheckedChange={(val) => setConfig({...config, private: val})}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <Button 
          onClick={handleSave}
          disabled={saving}
          className="w-full py-6 bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-bold shadow-xl shadow-indigo-500/20"
        >
          {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />}
          ENREGISTRER LA CONFIGURATION
        </Button>
      </div>
    </Layout>
  );
};

export default Settings;