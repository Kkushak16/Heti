export enum AppMode {
  MODERNIZE = 'MODERNIZE',
  AUDIT = 'AUDIT',
  DESIGN = 'DESIGN',
  GROWTH = 'GROWTH',
  LANDING = 'LANDING'
}

export interface AnalysisResult {
  markdown: string;
  rawCode?: string;
  score?: number; // 0 to 100
}

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
  timestamp: number;
}

export interface ModernizerState {
  legacyCode: string;
  sourceLang: string;
  modernizedCode: string;
  explanation: string;
  isConverting: boolean;
}
