import axios from 'axios';
import { SystemStats } from './types';

export interface ITelemetryService {
  getSystemStats(): Promise<SystemStats | null>;
}

const API_BASE_URL = 'http://localhost:8000';

class RestTelemetryService implements ITelemetryService {
  async getSystemStats(): Promise<SystemStats | null> {
    try {
      const response = await axios.get<SystemStats>(`${API_BASE_URL}/system`, { timeout: 4000 });
      return response.data;
    } catch (error) {
      // Return fallback graceful stats if offline/connecting
      return null;
    }
  }
}

export const telemetryService: ITelemetryService = new RestTelemetryService();
