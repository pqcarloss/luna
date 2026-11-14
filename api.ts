import axios from 'axios';
import type {Site, Result} from './types';
const api = axios.create({baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'});
export async function getSites(): Promise<Site[]> { return (await api.get('/api/sites')).data; }
export async function getHealth() { return (await api.get('/api/health')).data; }
export async function analyze(payload: unknown): Promise<Result[]> { return (await api.post('/api/analyze', payload)).data.results; }
export async function getDemSources() { return (await api.get('/api/nasa/dem-sources')).data; }
