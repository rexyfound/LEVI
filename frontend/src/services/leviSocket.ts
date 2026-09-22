import { LeviEvent } from '../types/events';

type EventListener = (event: LeviEvent) => void;
type ConnectionListener = (connected: boolean) => void;

class LeviSocketService {
  private ws: WebSocket | null = null;
  private eventListeners: Set<EventListener> = new Set();
  private connectionListeners: Set<ConnectionListener> = new Set();
  private reconnectTimer: any = null;
  private isConnected = false;
  private url = 'ws://localhost:8000/ws/agent';

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[LeviSocket] WebSocket connected');
        this.isConnected = true;
        this.notifyConnection(true);
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data: LeviEvent = JSON.parse(event.data);
          this.notifyEvent(data);
        } catch (err) {
          console.error('[LeviSocket] Error parsing WebSocket message:', err);
        }
      };


      this.ws.onclose = () => {
        console.log('[LeviSocket] WebSocket disconnected');
        this.isConnected = false;
        this.notifyConnection(false);
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[LeviSocket] WebSocket error:', err);
        this.ws?.close();
      };
    } catch (e) {
      console.error('[LeviSocket] Failed to create WebSocket connection:', e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }

  onEvent(listener: EventListener): () => void {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  onConnectionChange(listener: ConnectionListener): () => void {
    this.connectionListeners.add(listener);
    // Notify immediate state
    listener(this.isConnected);
    return () => this.connectionListeners.delete(listener);
  }

  private notifyEvent(event: LeviEvent) {
    this.eventListeners.forEach((fn) => fn(event));
  }

  private notifyConnection(connected: boolean) {
    this.connectionListeners.forEach((fn) => fn(connected));
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// Global Singleton Instance
export const leviSocket = new LeviSocketService();
