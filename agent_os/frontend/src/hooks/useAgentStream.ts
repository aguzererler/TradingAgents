import { useState, useEffect, useRef, useCallback } from 'react';

export interface AgentEvent {
  id: string;
  timestamp: string;
  agent: string;
  tier: 'quick' | 'mid' | 'deep';
  type: 'thought' | 'tool' | 'result' | 'system';
  message: string;
  node_id?: string;
  parent_node_id?: string;
  metrics?: {
    model: string;
    tokens_in?: number;
    tokens_out?: number;
    latency_ms?: number;
    raw_json_response?: string;
  };
  details?: {
    model_used: string;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    request_content: string;
    response_content: string;
    is_tool_call?: boolean;
  };
}

type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'error';

export const useAgentStream = (runId: string | null) => {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<StreamStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const statusRef = useRef<StreamStatus>('idle');
  const socketRef = useRef<WebSocket | null>(null);

  // Keep statusRef in sync so callbacks always read the latest value
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    if (!runId) return;

    // Close any existing socket before opening a new one
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    setStatus('connecting');
    setError(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = '127.0.0.1:8088';
    const socket = new WebSocket(`${protocol}//${host}/ws/stream/${runId}`);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus('streaming');
      console.log(`Connected to run: ${runId}`);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'system' && data.message === 'Run completed.') {
        setStatus('completed');
      } else if (data.type === 'system' && data.message.startsWith('Error:')) {
        setStatus('error');
        setError(data.message);
      } else {
        setEvents((prev) => [...prev, data as AgentEvent]);
      }
    };

    socket.onclose = () => {
      // Use the ref to read the latest status (avoids stale closure)
      if (statusRef.current !== 'completed' && statusRef.current !== 'error') {
        setStatus('idle');
      }
      console.log(`Disconnected from run: ${runId}`);
    };

    socket.onerror = (err) => {
      setStatus('error');
      setError('WebSocket error occurred');
      console.error(err);
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [runId]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, status, error, clearEvents };
};
