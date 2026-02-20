export const translations = {
  fr: {
    nav: { series: "Séries", movies: "Films", torrents: "Torrents", tasks: "Tâches", logs: "Logs", settings: "Réglages" },
    index: { title: "Bibliothèque Séries", subtitle: "Génération intelligente par packs ou saisons.", scan: "Scanner", generate: "Tout Générer", search: "Rechercher une série...", table: { name: "NOM DE LA SÉRIE", lang: "LANGUE", mode: "MODE", action: "ACTION" }, modes: { complete: "Pack Complet", season: "Par Saison", episode: "Par Épisode" } },
    movies: { title: "Bibliothèque Films", subtitle: "Gérez vos films et générez des torrents.", scan: "Scanner", generate: "Tout Générer", search: "Rechercher un film...", table: { name: "NOM DU FILM", lang: "LANGUE", size: "TAILLE", action: "ACTION" } },
    tasks: { title: "Activités en cours", subtitle: "Progression globale et par fichier.", clear: "Nettoyer", empty: "Aucune tâche en cours d'exécution.", global: "Progression Globale", status: { running: "EN COURS", completed: "TERMINÉ", cancelled: "ANNULÉ", pending: "EN ATTENTE" } },
    torrents: { title: "Torrents Créés", subtitle: "Liste des fichiers .torrent réellement présents dans vos dossiers OUT.", refresh: "Actualiser", empty: "Aucun torrent trouvé.", reading: "Lecture des répertoires..." },
    logs: { title: "Logs Système", clear: "Effacer" },
    settings: { title: "Configuration V1.0.4", subtitle: "Moteur de création réel avec toutes les options activées.", save: "ENREGISTRER LA CONFIGURATION", sections: { dirs: "Répertoires", torrent: "Paramètres Torrent", system: "Options & Performance", language: "Langue de l'interface" }, fields: { tracker: "Tracker URL", piece: "Taille Pièces (0=auto)", timeout: "Timeout (sec)", exclude: "Fichiers à exclure", comment: "Commentaire", workers: "Workers Max", lang: "Choisir la langue" }, options: { private: "Mode Privé", audio: "Analyse Audio", size: "Afficher Taille", reset: "Reset Tâches" } }
  },
  en: {
    nav: { series: "Series", movies: "Movies", torrents: "Torrents", tasks: "Tasks", logs: "Logs", settings: "Settings" },
    index: { title: "Series Library", subtitle: "Smart generation by packs or seasons.", scan: "Scan", generate: "Generate All", search: "Search for a series...", table: { name: "SERIES NAME", lang: "LANGUAGE", mode: "MODE", action: "ACTION" }, modes: { complete: "Complete Pack", season: "By Season", episode: "By Episode" } },
    movies: { title: "Movies Library", subtitle: "Manage your movies and generate torrents.", scan: "Scan", generate: "Generate All", search: "Search for a movie...", table: { name: "MOVIE NAME", lang: "LANGUAGE", size: "SIZE", action: "ACTION" } },
    tasks: { title: "Current Activities", subtitle: "Global and per-file progress.", clear: "Clear", empty: "No tasks currently running.", global: "Global Progress", status: { running: "RUNNING", completed: "COMPLETED", cancelled: "CANCELLED", pending: "PENDING" } },
    torrents: { title: "Created Torrents", subtitle: "List of .torrent files actually present in your OUT folders.", refresh: "Refresh", empty: "No torrents found.", reading: "Reading directories..." },
    logs: { title: "System Logs", clear: "Clear" },
    settings: { title: "Configuration V1.0.4", subtitle: "Real creation engine with all options enabled.", save: "SAVE CONFIGURATION", sections: { dirs: "Directories", torrent: "Torrent Settings", system: "Options & Performance", language: "Interface Language" }, fields: { tracker: "Tracker URL", piece: "Piece Size (0=auto)", timeout: "Timeout (sec)", exclude: "Files to exclude", comment: "Comment", workers: "Max Workers", lang: "Choose language" }, options: { private: "Private Mode", audio: "Audio Analysis", size: "Show Size", reset: "Reset Tasks" } }
  },
  de: {
    nav: { series: "Serien", movies: "Filme", torrents: "Torrents", tasks: "Aufgaben", logs: "Protokolle", settings: "Einstellungen" },
    index: { title: "Serienbibliothek", subtitle: "Intelligente Generierung nach Paketen oder Staffeln.", scan: "Scannen", generate: "Alle generieren", search: "Suche nach einer Serie...", table: { name: "SERIENNAME", lang: "SPRACHE", mode: "MODUS", action: "AKTION" }, modes: { complete: "Komplettes Paket", season: "Nach Staffel", episode: "Nach Episode" } },
    movies: { title: "Filmbibliothek", subtitle: "Verwalten Sie Ihre Filme und generieren Sie Torrents.", scan: "Scannen", generate: "Alle generieren", search: "Suche nach einem Film...", table: { name: "FILMNAME", lang: "SPRACHE", size: "GRÖSSE", action: "AKTION" } },
    tasks: { title: "Aktuelle Aktivitäten", subtitle: "Globaler und dateibezogener Fortschritt.", clear: "Löschen", empty: "Derzeit laufen keine Aufgaben.", global: "Globaler Fortschritt", status: { running: "LÄUFT", completed: "ABGESCHLOSSEN", cancelled: "ABGEBROCHEN", pending: "AUSSTEHEND" } },
    torrents: { title: "Erstellte Torrents", subtitle: "Liste der .torrent-Dateien, die tatsächlich in Ihren OUT-Ordnern vorhanden sind.", refresh: "Actualisieren", empty: "Keine Torrents gefunden.", reading: "Verzeichnisse lesen..." },
    logs: { title: "Systemprotokolle", clear: "Löschen" },
    settings: { title: "Konfiguration V1.0.4", subtitle: "Echte Erstellungs-Engine mit allen aktivierten Optionen.", save: "KONFIGURATION SPEICHERN", sections: { dirs: "Verzeichnisse", torrent: "Torrent-Einstellungen", system: "Optionen & Leistung", language: "Oberflächensprache" }, fields: { tracker: "Tracker-URL", piece: "Stückgröße (0=auto)", timeout: "Timeout (Sek.)", exclude: "Auszuschließende Dateien", comment: "Kommentar", workers: "Max. Arbeiter", lang: "Sprache wählen" }, options: { private: "Privater Modus", audio: "Audio-Analyse", size: "Größe anzeigen", reset: "Aufgaben zurücksetzen" } }
  }
};

export type Language = keyof typeof translations;