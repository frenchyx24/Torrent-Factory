"use client";

import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Save, Globe, Loader2, ChevronRight, HardDrive } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const Settings = () => {
  const [config, setConfig] = useState({
    series_root: "", series_out: "", movies_root: "", movies_out: "",
    tracker_url: "", private: true, piece_size: 0, analyze_audio: true, show_size: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // File Picker State
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerTarget, setPickerTarget] = useState("");
  const [currentPath, setCurrentPath] = useState("/");
  const [folders, setFolders] = useState([]);
  const [drives, setDrives] = useState([]);

  useEffect(() => {
    fetch('/api/config').then(res => res.json()).then(data => {
      setConfig(data);
      setLoading(false);
    });
  }, []);

  const openPicker = async (target: string) => {
    setPickerTarget(target);
    const driveRes = await fetch('/api/drives');
    const driveData = await driveRes.json();
    setDrives(driveData);
    browse(config[target] || "/");
    setPickerOpen(true);
  };

  const browse = async (path: string) => {
    const res = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    setCurrentPath(data.current);
    setFolders(data.items);
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
      if (res.ok) showSuccess("Configuration enregistrée");
    } catch (e) { showError("Erreur de sauvegarde"); }
    finally { setSaving(false); }
  };

  if (loading) return <Layout><div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-10 h-10 text-indigo-500 animate-spin" /></div></Layout>;

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white">Configuration V38</h2>
        <p className="text-slate-400 mt-1">Moteur de création réel avec support FFprobe.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2"><FolderOpen className="w-5 h-5 text-indigo-400" />Chemins</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {['series_root', 'series_out', 'movies_root', 'movies_out'].map((key) => (
              <div key={key} className="space-y-2">
                <Label className="text-xs text-indigo-400 uppercase font-bold">{key.replace('_', ' ')}</Label>
                <div className="flex gap-2">
                  <Input className="bg-slate-950/50 border-white/10 text-white" value={config[key]} readOnly />
                  <Button variant="outline" onClick={() => openPicker(key)} className="border-white/10 text-white hover:bg-white/5">Explorer</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader><CardTitle className="text-white flex items-center gap-2"><Globe className="w-5 h-5 text-indigo-400" />Options</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Tracker URL</Label>
              <Input className="bg-slate-950/50 border-white/10 text-white" value={config.tracker_url} onChange={(e) => setConfig({...config, tracker_url: e.target.value})} />
            </div>
            <div className="grid grid-cols-1 gap-4">
              {[
                { label: "Mode Privé", key: "private", desc: "Ajoute le flag -P" },
                { label: "Analyse Audio", key: "analyze_audio", desc: "Utilise FFprobe pour les langues" },
                { label: "Afficher Taille", key: "show_size", desc: "Scan plus lent mais précis" }
              ].map((opt) => (
                <div key={opt.key} className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                  <div><Label className="text-white">{opt.label}</Label><p className="text-[10px] text-slate-500">{opt.desc}</p></div>
                  <Switch checked={config[opt.key]} onCheckedChange={(val) => setConfig({...config, [opt.key]: val})} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Button onClick={handleSave} disabled={saving} className="w-full mt-8 py-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold shadow-xl shadow-indigo-500/20">
        {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />} ENREGISTRER
      </Button>

      {/* File Picker Dialog */}
      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="bg-slate-900 border-white/10 text-white max-w-2xl">
          <DialogHeader><DialogTitle>Choisir un dossier</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {drives.map(d => (
                <Button key={d.path} size="sm" variant="outline" onClick={() => browse(d.path)} className="border-white/10 text-xs shrink-0">
                  <HardDrive className="w-3 h-3 mr-1" /> {d.name}
                </Button>
              ))}
            </div>
            <div className="bg-slate-950 rounded-lg p-2 text-xs font-mono text-indigo-400 truncate">{currentPath}</div>
            <div className="h-64 overflow-y-auto space-y-1 pr-2">
              <div onClick={() => browse(currentPath.split('/').slice(0, -1).join('/') || '/')} className="flex items-center p-2 hover:bg-white/5 rounded cursor-pointer text-slate-400">
                <ChevronRight className="w-4 h-4 rotate-180 mr-2" /> .. (Parent)
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