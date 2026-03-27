"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Save, Loader2, HardDrive, Languages, Info, Zap, Key } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { translations, Language } from '@/lib/i18n';
import { cn } from "@/lib/utils";

const Settings = () => {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerTarget, setPickerTarget] = useState("");
  const [currentPath, setCurrentPath] = useState("/");
  const [folders, setFolders] = useState<any[]>([]);
  const [drives, setDrives] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setConfig(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const openPicker = async (target: string) => {
    setPickerTarget(target);
    try {
      const driveRes = await fetch('/api/drives');
      const driveData = await driveRes.json();
      setDrives(driveData);
      browse(config[target] || "/");
      setPickerOpen(true);
    } catch (e) { showError("Erreur serveur"); }
  };

  const browse = async (path: string) => {
    try {
      const res = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      setCurrentPath(data.current);
      setFolders(data.items);
    } catch (e) { showError("Erreur de navigation"); }
  };

  const selectFolder = () => {
    setConfig({ ...config, [pickerTarget]: currentPath });
    setPickerOpen(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        showSuccess(config.language === 'fr' ? "Configuration V1.1 enregistrée" : "V1.1 Configuration saved");
        setTimeout(() => window.location.reload(), 500);
      }
    } catch (e) { showError("Erreur de sauvegarde"); }
    finally { setSaving(false); }
  };

  if (loading || !config) return <Layout><div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-10 h-10 text-indigo-500 animate-spin" /></div></Layout>;

  const currentLang = (config.language as Language) || 'fr';
  const t = translations[currentLang]?.settings || translations['fr'].settings;

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white tracking-tight">Configuration V1.1 Pro</h2>
        <p className="text-slate-400 mt-1">Gérez vos paramètres avancés et votre moteur NFO haute précision.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md lg:col-span-2">
          <CardHeader><CardTitle className="text-white flex items-center gap-2 text-lg"><Languages className="w-5 h-5 text-indigo-400" />{t.sections.language}</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {['fr', 'en', 'de'].map((code) => (
                <Button 
                  key={code}
                  variant={config.language === code ? "default" : "outline"}
                  className={cn(
                    "flex-1 py-6 border-white/10 text-sm font-semibold",
                    config.language === code ? "bg-indigo-600 hover:bg-indigo-700 text-white border-transparent" : "bg-slate-800/50 text-slate-400 hover:bg-slate-700 hover:text-white"
                  )}
                  onClick={() => setConfig({...config, language: code})}
                >
                  {code === 'fr' ? 'Français' : code === 'en' ? 'English' : 'Deutsch'}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md lg:col-span-2">
          <CardHeader><CardTitle className="text-white flex items-center gap-2 text-lg"><Key className="w-5 h-5 text-indigo-400" />Intégration TMDb (Metadata Pro)</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider opacity-70">Clé API The Movie Database</Label>
              <Input 
                placeholder="Ex: 56f6... (Laissez vide pour désactiver)" 
                className="bg-slate-950/50 border-white/10 text-white h-11" 
                value={config.tmdb_api_key} 
                onChange={(e) => setConfig({...config, tmdb_api_key: e.target.value})}
              />
              <p className="text-[11px] text-slate-500 mt-2">Permet d'extraire Genre, Synopsis, Année et Note IMDb pour vos fichiers .nfo</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2 text-lg"><FolderOpen className="w-5 h-5 text-indigo-400" />{t.sections.dirs}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {['series_root', 'series_out', 'movies_root', 'movies_out'].map((key) => (
              <div key={key} className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider opacity-70">{key.replace('_', ' ')}</Label>
                <div className="flex gap-2">
                  <Input className="bg-slate-950/50 border-white/10 text-white text-xs h-9" value={config[key]} readOnly />
                  <Button variant="outline" size="sm" onClick={() => openPicker(key)} className="bg-slate-800 border-white/10 text-white hover:bg-slate-700 shrink-0">Explorer</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2 text-lg"><Zap className="w-5 h-5 text-indigo-400" />Moteur Pro V1.1</CardTitle></CardHeader>
          <CardContent className="space-y-4">
             <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider opacity-70">Parallel Workers</Label>
                <Input type="number" min="1" max="10" className="bg-slate-950/50 border-white/10 text-white h-9" value={config.max_workers} onChange={(e) => setConfig({...config, max_workers: parseInt(e.target.value) || 2})} />
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider opacity-70">Génération NFO</Label>
                <div className="flex items-center h-9">
                  <Switch 
                    checked={config.enable_nfo} 
                    onCheckedChange={(val) => setConfig({...config, enable_nfo: val})}
                    className="data-[state=checked]:bg-emerald-600"
                  />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider opacity-70">{t.fields.tracker}</Label>
              <Input className="bg-slate-950/50 border-white/10 text-white h-9" value={config.tracker_url} onChange={(e) => setConfig({...config, tracker_url: e.target.value})} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Button onClick={handleSave} disabled={saving} className="w-full mt-8 py-7 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-lg shadow-2xl shadow-indigo-500/20 rounded-2xl transition-all">
        {saving ? <Loader2 className="w-6 h-6 animate-spin mr-2" /> : <Save className="w-6 h-6 mr-2" />} 
        APPLIQUER LA MISE À JOUR V1.1
      </Button>

      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="bg-[#0f172a] border-white/10 text-white max-w-2xl rounded-3xl overflow-hidden p-0">
          <DialogHeader className="p-6 border-b border-white/5">
            <DialogTitle className="flex items-center gap-2"><FolderOpen className="w-5 h-5 text-indigo-400" /> Explorer le serveur</DialogTitle>
          </DialogHeader>
          <div className="p-6 space-y-4">
            <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
              {drives.map(d => (
                <Button key={d.path} size="sm" variant="outline" onClick={() => browse(d.path)} className="bg-slate-800 border-white/10 text-xs shrink-0 rounded-full hover:bg-indigo-600">
                  <HardDrive className="w-3 h-3 mr-1" /> {d.name}
                </Button>
              ))}
            </div>
            <div className="bg-slate-950/50 rounded-xl p-3 text-xs font-mono text-indigo-400 truncate flex items-center gap-2">
              <Info className="w-3.5 h-3.5 opacity-50" /> {currentPath}
            </div>
            <div className="h-64 overflow-y-auto space-y-1 pr-2 custom-scrollbar">
              <div onClick={() => browse(currentPath.split('/').slice(0, -1).join('/') || '/')} className="flex items-center p-3 hover:bg-white/5 rounded-xl cursor-pointer text-slate-400 transition-colors">
                .. (Parent)
              </div>
              {folders.map(f => (
                <div key={f.path} onClick={() => browse(f.path)} className="flex items-center p-3 hover:bg-indigo-600/10 hover:text-white rounded-xl cursor-pointer transition-all">
                  <FolderOpen className="w-4 h-4 mr-3 text-indigo-400" />
                  <span className="text-sm font-medium">{f.name}</span>
                </div>
              ))}
            </div>
            <Button onClick={selectFolder} className="w-full bg-indigo-600 hover:bg-indigo-700 py-6 rounded-2xl font-bold">Sélectionner ce répertoire</Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Settings;