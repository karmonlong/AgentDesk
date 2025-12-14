/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
export type AspectRatio = '16:9';

export type ComplexityLevel = '通用' | '专业' | '学术' | '行政高管';

export type VisualStyle = '现代简约' | '商务科技' | '创意艺术' | '深色模式' | '自然清新';

export type Language = '简体中文' | 'English' | 'Spanish' | 'French' | 'German' | 'Japanese';

export interface Slide {
  id: string;
  data: string; // Base64 data URL
  title: string;
  speakerNotes: string;
}

export interface Presentation {
  id: string;
  topic: string;
  timestamp: number;
  slides: Slide[];
  level: ComplexityLevel;
  style: VisualStyle;
  sources: SearchResultItem[];
}

export interface SearchResultItem {
  title: string;
  url: string;
}

export interface SlideOutline {
  title: string;
  content: string;
  visualDescription: string;
}

export interface UploadedFile {
  name: string;
  type: string;
  data: string; // Base64 for PDF
}

declare global {
  interface AIStudio {
    hasSelectedApiKey: () => Promise<boolean>;
    openSelectKey: () => Promise<void>;
  }
}