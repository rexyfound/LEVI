import { useState, useEffect } from 'react';
import { SystemStats } from '../services/types';
import { telemetryService } from '../services/TelemetryService';

export function useSystemStats() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    const fetchStats = async () => {
      const data = await telemetryService.getSystemStats();
      if (isMounted) {
        if (data) {
          setStats(data);
          setIsOnline(true);
        } else {
          setIsOnline(false);
        }
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { stats, isOnline };
}
