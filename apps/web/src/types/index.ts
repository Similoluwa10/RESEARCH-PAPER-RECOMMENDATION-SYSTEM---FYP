/**
 * Shared TypeScript types for the frontend
 */

export interface Paper {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  year: number;
  venue?: string;
  keywords: string[];
  doi?: string;
  url?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Recommendation {
  paper: Paper;
  score: number;
  explanation: RecommendationExplanation;
}

export interface RecommendationExplanation {
  summary: string;
  keyTerms: string[];
  similarityBreakdown: {
    semantic: number;
    keyword: number;
    overall: number;
  };
}

export interface SearchResult {
  papers: Paper[];
  total: number;
  page: number;
  pageSize: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
}
