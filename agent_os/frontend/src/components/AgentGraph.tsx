import React, { useMemo, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  Node, 
  Edge,
  Handle,
  Position,
  NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Box, Text, Flex, Icon, Tooltip } from '@chakra-ui/react';
import { Settings, TrendingUp, Clock, Wrench, Brain } from 'lucide-react';
import { AgentEvent } from '../hooks/useAgentStream';

// --- Custom Agent Node Component ---
const AgentNode = ({ data }: NodeProps) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'tool': return Wrench;
      case 'result': return TrendingUp;
      case 'thought': return Brain;
      default: return Settings;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#4fd1c5';
      case 'completed': return '#48bb78';
      case 'tool': return '#b794f4';
      case 'error': return '#fc8181';
      default: return 'rgba(255,255,255,0.4)';
    }
  };

  const statusColor = getStatusColor(data.status);
  
  // Truncate model name to fit
  const shortModel = data.model && data.model !== 'unknown' 
    ? (data.model.length > 18 ? data.model.slice(-18) : data.model)
    : null;

  return (
    <Box 
      bg="rgba(15,23,42,0.95)" 
      border="1px solid" 
      borderColor={statusColor}
      p={3} 
      borderRadius="lg" 
      minW="200px"
      maxW="220px"
      boxShadow={`0 0 12px ${statusColor}33`}
      cursor="pointer"
      _hover={{ 
        boxShadow: `0 0 20px ${statusColor}66`,
        transform: 'scale(1.02)',
      }}
      transition="all 0.2s ease"
      onClick={() => data.onNodeClick?.(data.eventData)}
    >
      <Handle type="target" position={Position.Top} style={{ background: statusColor, width: 6, height: 6 }} />
      
      <Flex direction="column" gap={1.5}>
        <Flex align="center" gap={2}>
          <Icon as={getIcon(data.eventType)} color={statusColor} boxSize={3.5} />
          <Text fontSize="11px" fontWeight="bold" color="white" noOfLines={1}>
            {data.agent}
          </Text>
        </Flex>
        
        <Text fontSize="10px" color="whiteAlpha.500" noOfLines={1}>
          {data.message}
        </Text>
        
        <Box height="1px" bg="whiteAlpha.100" width="100%" />
        
        <Flex justify="space-between" align="center" gap={1}>
          <Flex align="center" gap={1}>
            <Icon as={Clock} boxSize={2.5} color="whiteAlpha.400" />
            <Text fontSize="9px" color="whiteAlpha.500">{data.latency_ms || 0}ms</Text>
          </Flex>
          {shortModel && (
            <Tooltip label={data.model} fontSize="xs" bg="slate.800" placement="top">
              <Text fontSize="8px" color="blue.300" noOfLines={1} maxW="100px" textAlign="right">
                {shortModel}
              </Text>
            </Tooltip>
          )}
        </Flex>
        
        {/* Only show progress bar for 'thought' type (running), NOT for completed results */}
        {data.status === 'running' && data.eventType === 'thought' && (
           <Box width="100%" height="2px" bg="cyan.900" borderRadius="full" overflow="hidden">
              <Box 
                as="div" 
                width="40%" 
                height="100%" 
                bg="cyan.400" 
                sx={{
                  animation: "shimmer 1.5s infinite linear",
                  "@keyframes shimmer": {
                    "0%": { transform: "translateX(-100%)" },
                    "100%": { transform: "translateX(300%)" }
                  }
                }}
              />
           </Box>
        )}
      </Flex>

      <Handle type="source" position={Position.Bottom} style={{ background: statusColor, width: 6, height: 6 }} />
    </Box>
  );
};

const nodeTypes = {
  agentNode: AgentNode,
};

interface AgentGraphProps {
  events: AgentEvent[];
  onNodeClick?: (event: AgentEvent) => void;
}

const COLUMN_WIDTH = 260;
const ROW_HEIGHT = 130;
const BASE_X = 250;
const BASE_Y = 40;

export const AgentGraph: React.FC<AgentGraphProps> = ({ events, onNodeClick }) => {
  const { nodes, edges } = useMemo(() => {
    const graphNodes: Node[] = [];
    const graphEdges: Edge[] = [];
    const nodeIdSet = new Set<string>();
    
    const columnMap = new Map<string, number>();
    let nextColumn = 0;
    const columnRowCount = new Map<string, number>();

    events.forEach((evt) => {
      if (!evt.node_id || nodeIdSet.has(evt.node_id)) return;
      nodeIdSet.add(evt.node_id);

      const baseName = evt.node_id.replace(/_\d+$/, '');
      
      if (!columnMap.has(baseName)) {
        columnMap.set(baseName, nextColumn++);
      }
      const col = columnMap.get(baseName)!;
      
      const row = columnRowCount.get(baseName) || 0;
      columnRowCount.set(baseName, row + 1);

      // Determine status: result = completed, tool = tool, thought = running
      let status = evt.type === 'result' ? 'completed' 
                 : evt.type === 'tool' ? 'tool' 
                 : 'running';

      // Keep thought nodes running until the agent emits a FINAL result
      // A final result has is_tool_call falsy and isn't a tool_execution event
      if (status === 'running') {
        const hasFinalResult = events.some(e => 
            e.node_id &&
            e.node_id.startsWith(baseName) && 
            e.type === 'result' && 
            e.metrics?.model !== 'tool_execution' && 
            !e.details?.is_tool_call
        );
        if (hasFinalResult) {
          status = 'completed';
        }
      }

      graphNodes.push({
        id: evt.node_id,
        type: 'agentNode',
        position: { 
          x: BASE_X + col * COLUMN_WIDTH, 
          y: BASE_Y + row * ROW_HEIGHT 
        },
        data: { 
          agent: evt.agent || 'Unknown',
          status,
          eventType: evt.type,
          message: evt.message,
          model: evt.metrics?.model,
          latency_ms: evt.metrics?.latency_ms || 0,
          onNodeClick,
          eventData: evt,
        },
      });

      if (evt.parent_node_id && evt.parent_node_id !== 'start' && nodeIdSet.has(evt.parent_node_id)) {
        graphEdges.push({
          id: `e-${evt.parent_node_id}-${evt.node_id}`,
          source: evt.parent_node_id,
          target: evt.node_id,
          animated: status === 'running',
          style: { 
            stroke: status === 'tool' ? '#b794f4' : '#4fd1c5',
            strokeWidth: 1.5,
          },
        });
      }
    });

    return { nodes: graphNodes, edges: graphEdges };
  }, [events, onNodeClick]);

  return (
    <Box height="100%" width="100%" bg="rgba(2,6,23,1)">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        nodesDraggable={false}
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls 
          style={{ 
            background: 'rgba(15,23,42,0.9)', 
            borderColor: 'rgba(255,255,255,0.1)',
            borderRadius: '8px',
          }} 
        />
      </ReactFlow>
    </Box>
  );
};
