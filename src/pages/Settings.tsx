"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Save, Globe, Loader2, ChevronRight, HardDrive, Cpu, Languages } from 'lucide-react';
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
      if (!driveRes.ok) throw new Error();
      const driveData = await driveRes.json();
      setDrives(driveData);
      browse(config[target] || "/");
      setPickerOpen(true);
    } catch (e) {
      showError("Erreur serveur");
    }
  };

  const browse = async (path: string) => {
    try {
      const res = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      setCurrentPath(data.current);
      setFolders(data.items);
    } catch (e) {
      showError("Erreur de navigation");
    }
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
        showSuccess(config.language === 'fr' ? "Configuration enregistrée" : "Configuration saved");
        setTimeout(() => window.location.reload(), 500);
      }
    } catch (e) { 
      showError("Erreur de sauvegarde"); 
    } finally { 
      setSaving(false); 
    }
  };

  if (loading || !config) return <Layout><div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-10 h-10 text-indigo-500 animate-spin" /></div></Layout>;

  const currentLang = (config.language as Language) || 'fr';
  const t = translations[currentLang]?.settings || translations['fr'].settings;

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white">Configuration V1.0.9</h2>
        <p className="text-slate-400 mt-1">{t.subtitle}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md lg:col-span-2">
          <CardHeader><CardTitle className="text-white flex items-center gap-2"><Languages className="w-5 h-5 text-indigo-400" />{t.sections.language}</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {['fr', 'en', 'de'].map((code) => (
                <Button 
                  key={code}
                  variant={config.language === code ? "default" : "outline"}
                  className={cn(
                    "flex-1 py-6 border-white/10",
                    config.language === code ? "bg-indigo-600 hover:bg-indigo-700 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  )}
                  onClick={() => setConfig({...config, language: code})}
                >
                  {code === 'fr' ? 'Français' : code === 'en' ? 'English' : 'Deutsch'}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2"><FolderOpen className="w-5 h-5 text-indigo-400" />{t.sections.dirs}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {['series_root', 'series_out', 'movies_root', 'movies_out'].map((key) => (
              <div key={key} className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider">{key.replace('_', ' ')}</Label>
                <div className="flex gap-2">
                  <Input className="bg-slate-950/50 border-white/10 text-white text-xs" value={config[key]} readOnly />
                  <Button variant="outline" size="sm" onClick={() => openPicker(key)} className="bg-slate-800 border-white/10 text-white hover:bg-slate-700">Explorer</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2"><Globe className="w-5 h-5 text-indigo-400" />{t.sections.torrent}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider">{t.fields.tracker}</Label>
              <Input className="bg-slate-950/50 border-white/10 text-white" value={config.tracker_url} onChange={(e) => setConfig({...config, tracker_url: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider">Piece (2^x)</Label>
                <Input type="number" className="bg-slate-950/50 border-white/10 text-white" value={config.piece_size} onChange={(e) => setConfig({...config, piece_size: parseInt(e.target.value) || 21})} />
              </div>
              <div className="space-y-2">
                <Label className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider">Mode Privé</Label>
                <div className="flex items-center h-10">
                  <Switch 
                    checked={config.private} 
                    onCheckedChange={(val) => setConfig({...config, private: val})}
                    className="data-[state=checked]:bg-emerald-500"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Button onClick={handleSave} disabled={saving} className="w-full mt-8 py-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold shadow-xl shadow-indigo-500/20">
        {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />} ENREGISTRER V1.0.9
      </Button>

      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="bg-slate-900 border-white/10 text-white max-w-2xl">
          <DialogHeader><DialogTitle>Choisir un dossier</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {drives.map(d => (
                <Button key={d.path} size="sm" variant="outline" onClick={() => browse(d.path)} className="bg-slate-800 border-white/10 text-xs shrink-0">
                  <HardDrive className="w-3 h-3 mr-1" /> {d.name}
                </Button>
              ))}
            </div>
            <div className="bg-slate-950 rounded-lg p-2 text-xs font-mono text-indigo-400 truncate">{currentPath}</div>
            <div className="h-64 overflow-y-auto space-y-1 pr-2">
              <div onClick={() => browse(currentPath.split('/').slice(0, -1).join('/') || '/')} className="flex items-center p-2 hover:bg-white/5 rounded cursor-pointer text-slate-400">
                <ChevronRight className="w-4 h-4 rotate-180 mr-2" /> ..
              </div>
              {folders.map(f => (
                <div key={f.path} onClick={() => browse(f.path)} className="flex items-center p-2 hover:bg-white/5 rounded cursor-pointer group">
                  <FolderOpen className="w-4 h-4 mr-2 text-indigo-400" />
                  <span className="text-sm group-hover:text-white">{f.name}</span>
                </div>
              ))}
            </div>
            <Button onClick={selectFolder} className="w-full bg-indigo-600 hover:bg-indigo-700">Utiliser ce dossier</Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Settings;