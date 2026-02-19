"use client";

import React from 'react';
import Layout from '@/components/Layout';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, Save, Globe, Cpu, ShieldCheck } from 'lucide-react';

const Settings = () => {
  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white">Configuration</h2>
        <p className="text-slate-400 mt-1">Personnalisez le comportement de Torrent Factory.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Paths */}
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
              <div className="flex gap-2">
                <Input className="bg-slate-950/50 border-white/10 text-white" defaultValue="/mnt/media/series" />
                <Button variant="outline" className="border-white/10 text-white hover:bg-white/5">Parcourir</Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Séries (Destination)</Label>
              <div className="flex gap-2">
                <Input className="bg-slate-950/50 border-white/10 text-white" defaultValue="/mnt/media/torrents/series" />
                <Button variant="outline" className="border-white/10 text-white hover:bg-white/5">Parcourir</Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Films (Source)</Label>
              <div className="flex gap-2">
                <Input className="bg-slate-950/50 border-white/10 text-white" defaultValue="/mnt/media/movies" />
                <Button variant="outline" className="border-white/10 text-white hover:bg-white/5">Parcourir</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Network & Performance */}
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Globe className="w-5 h-5 text-indigo-400" />
              Réseau & Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-xs text-indigo-400 uppercase font-bold">Tracker URL</Label>
              <Input className="bg-slate-950/50 border-white/10 text-white" placeholder="udp://tracker.example.com:6969/announce" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs text-indigo-400 uppercase font-bold">Max Workers</Label>
                <Input type="number" className="bg-slate-950/50 border-white/10 text-white" defaultValue="2" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs text-indigo-400 uppercase font-bold">Timeout (sec)</Label>
                <Input type="number" className="bg-slate-950/50 border-white/10 text-white" defaultValue="7200" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Options */}
        <Card className="bg-slate-900/50 border-white/10 backdrop-blur-md lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              Options Avancées
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div className="space-y-0.5">
                <Label className="text-white">Analyse Audio</Label>
                <p className="text-xs text-slate-500">Utilise FFprobe pour détecter les langues.</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div className="space-y-0.5">
                <Label className="text-white">Mode Privé</Label>
                <p className="text-xs text-slate-500">Ajoute le flag -P aux torrents.</p>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
              <div className="space-y-0.5">
                <Label className="text-white">Afficher Taille</Label>
                <p className="text-xs text-slate-500">Scan plus lent mais précis.</p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <Button className="w-full py-6 bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-bold shadow-xl shadow-indigo-500/20">
          <Save className="w-5 h-5 mr-2" />
          ENREGISTRER LA CONFIGURATION
        </Button>
      </div>
    </Layout>
  );
};

export default Settings;