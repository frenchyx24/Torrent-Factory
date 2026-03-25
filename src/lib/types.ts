export interface LibraryItem {
  name: string;
  size: string;
  detected_tag?: string;
}

export interface Task {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'completed' | 'cancelled' | 'pending';
  progress_item: number;
  progress_global?: number;
  created_at: string;
  current_item_name?: string;
  current_item_index?: string;
  lang_tag?: string;
}

export interface TorrentFile {
  name: string;
  path: string;
  size: number;
  mtime: number;
}

export interface TorrentList {
  series: TorrentFile[];
  movies: TorrentFile[];
}