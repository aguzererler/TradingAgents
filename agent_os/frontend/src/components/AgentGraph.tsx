import React, { useEffect, useRef, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  Handle,
  Position,
  NodeProps,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Box, Text, Flex, Icon, Badge, IconButton, Tooltip } from '@chakra-ui/react';
import { Cpu, Settings, Database, TrendingUp, Clock, RefreshCw } from 'lucide-react';
import { AgentEvent } from '../hooks/useAgentStream';

// --- Custom Agent Node Component ---
const AgentNode = ({ data }: NodeProps) => {
  const getIcon = (agent: string) => {
    switch (agent.toUpperCase()) {
      case 'ANALYST': return Cpu;
      case 'RESEARCHER': return Database;
      case 'TRADER': return TrendingUp;
      default: return Settings;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'cyan.400';
      case 'completed': return 'green.400';
      case 'error': return 'red.400';
      default: return 'whiteAlpha.500';
    }
  };

  const getIdentifierColor = (identifier: string) => {
    if (!identifier || identifier === 'MARKET') return 'cyan';
    const palette = ['blue', 'purple', 'orange', 'teal', 'pink', 'yellow'];
    let hash = 0;
    for (let i = 0; i < identifier.length; i++) hash = (hash * 31 + identifier.charCodeAt(i)) & 0xffff;
    return palette[hash % palette.length];
  };

  const canRerun = data.status === 'completed' || data.status === 'error';

  return (
    <Box
      bg="slate.900"
      border="1px solid"
      borderColor={getStatusColor(data.status)}
      p={3}
      borderRadius="lg"
      minW="180px"
      boxShadow="0 0 15px rgba(0,0,0,0.5)"
      cursor="pointer"
      _hover={{ borderColor: 'cyan.300', boxShadow: '0 0 20px rgba(79,209,197,0.3)' }}
    >
      <Handle type="target" position={Position.Top} />

      <Flex direction="column" gap={2}>
        <Flex align="center" gap={2}>
          <Icon as={getIcon(data.agent)} color={getStatusColor(data.status)} boxSize={4} />
          <Text fontSize="sm" fontWeight="bold" color="white">{data.agent}</Text>
          {data.status === 'completed' && (
            <Badge colorScheme="green" fontSize="2xs" ml="auto">Done</Badge>
          )}
          {data.status === 'error' && (
            <Badge colorScheme="red" fontSize="2xs" ml="auto">Error</Badge>
          )}
        </Flex>

        {/* Identifier badge (ticker / MARKET / portfolio) */}
        {data.identifier && (
          <Badge
            colorScheme={getIdentifierColor(data.identifier)}
            fontSize="2xs"
            alignSelf="flex-start"
            px={1.5}
          >
            {data.identifier}
          </Badge>
        )}

        <Box height="1px" bg="whiteAlpha.200" width="100%" />

        <Flex justify="space-between" align="center">
          <Flex align="center" gap={1}>
            <Icon as={Clock} boxSize={3} color="whiteAlpha.500" />
            <Text fontSize="2xs" color="whiteAlpha.600">{data.metrics?.latency_ms || 0}ms</Text>
          </Flex>
          {data.metrics?.model && data.metrics.model !== 'unknown' && (
            <Badge variant="outline" fontSize="2xs" colorScheme="blue">{data.metrics.model}</Badge>
          )}
        </Flex>

        {data.status === 'running' && (
           <Box width="100%" height="2px" bg="cyan.400" borderRadius="full" overflow="hidden">
              <Box
                as="div"
                width="40%"
                height="100%"
                bg="white"
                sx={{
                  animation: "shimmer 2s infinite linear",
                  "@keyframes shimmer": {
                    "0%": { transform: "translateX(-100%)" },
                    "100%": { transform: "translateX(300%)" }
                  }
                }}
              />
           </Box>
        )}

        {/* Re-run button — visible on completed/error nodes */}
        {canRerun && data.onRerun && (
          <Tooltip label={`Re-run${data.identifier ? ` for ${data.identifier}` : ''}`} placement="bottom" hasArrow>
            <IconButton
              aria-label="Re-run this analysis"
              icon={<RefreshCw size={12} />}
              size="xs"
              variant="ghost"
              colorScheme="cyan"
              alignSelf="flex-end"
              onClick={(e) => {
                e.stopPropagation();
                data.onRerun();
              }}
            />
          </Tooltip>
        )}
      </Flex>

      <Handle type="source" position={Position.Bottom} />
    </Box>
  );
};

const nodeTypes = {
  agentNode: AgentNode,
};

interface AgentGraphProps {
  events: AgentEvent[];
  onNodeClick?: (nodeId: string, identifier?: string) => void;
  /** Called when the user clicks Re-run on a completed/error node. */
  onNodeRerun?: (identifier: string, nodeId: string) => void;
}

export const AgentGraph: React.FC<AgentGraphProps> = ({ events, onNodeClick, onNodeRerun }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  // Track which scoped IDs we have already added so we never duplicate
  const seenNodeIds = useRef(new Set<string>());
  const seenEdgeIds = useRef(new Set<string>());
  // Track how many unique nodes exist for vertical layout
  const nodeCount = useRef(0);
  // Track the last processed event index to only process new events
  const processedCount = useRef(0);

  useEffect(() => {
    // Only process newly arrived events
    const newEvents = events.slice(processedCount.current);
    if (newEvents.length === 0) return;
    processedCount.current = events.length;

    const addedNodes: Node[] = [];
    const addedEdges: Edge[] = [];
    const updatedNodeData: Map<string, Partial<Node['data']>> = new Map();

    for (const evt of newEvents) {
      if (!evt.node_id || evt.node_id === '__system__') continue;

      // Scope the node ID by identifier so each ticker gets its own graph node
      const identifier = evt.identifier || '';
      const scopedId = identifier ? `${evt.node_id}:${identifier}` : evt.node_id;

      // Determine if this event means the node is completed
      const isCompleted = evt.type === 'result' || evt.type === 'tool_result';

      if (!seenNodeIds.current.has(scopedId)) {
        // New node — create it
        seenNodeIds.current.add(scopedId);
        nodeCount.current += 1;

        addedNodes.push({
          id: scopedId,
          type: 'agentNode',
          position: { x: 250, y: nodeCount.current * 150 + 50 },
          data: {
            agent: evt.agent,
            identifier,
            node_id: evt.node_id,    // raw LangGraph node name (for event drawer filtering)
            status: isCompleted ? 'completed' : 'running',
            metrics: evt.metrics,
            onRerun: onNodeRerun
              ? () => onNodeRerun(identifier, evt.node_id!)
              : undefined,
          },
        });

        // Add edge from parent (scope parent to same identifier)
        if (evt.parent_node_id && evt.parent_node_id !== 'start') {
          const parentScopedId = identifier ? `${evt.parent_node_id}:${identifier}` : evt.parent_node_id;
          const edgeId = `e-${parentScopedId}-${scopedId}`;
          if (!seenEdgeIds.current.has(edgeId)) {
            seenEdgeIds.current.add(edgeId);
            addedEdges.push({
              id: edgeId,
              source: parentScopedId,
              target: scopedId,
              animated: true,
              style: { stroke: '#4fd1c5' },
            });
          }
        }
      } else {
        // Existing node — queue a status/metrics update
        const prev = updatedNodeData.get(scopedId);
        const currentlyCompleted = prev?.status === 'completed';
        updatedNodeData.set(scopedId, {
          status: currentlyCompleted || isCompleted ? 'completed' : 'running',
          metrics: evt.metrics,
        });
      }
    }

    // Batch state updates
    if (addedNodes.length > 0) {
      setNodes((prev) => [...prev, ...addedNodes]);
    }
    if (addedEdges.length > 0) {
      setEdges((prev) => [...prev, ...addedEdges]);
    }
    if (updatedNodeData.size > 0) {
      setNodes((prev) =>
        prev.map((n) => {
          const patch = updatedNodeData.get(n.id);
          if (!patch) return n;
          const finalStatus = n.data.status === 'completed' ? 'completed' : patch.status;
          return {
            ...n,
            data: { ...n.data, ...patch, status: finalStatus, metrics: patch.metrics ?? n.data.metrics },
          };
        }),
      );
    }
  }, [events, setNodes, setEdges, onNodeRerun]);

  // Reset tracked state when the events array is cleared (new run)
  useEffect(() => {
    if (events.length === 0) {
      seenNodeIds.current.clear();
      seenEdgeIds.current.clear();
      nodeCount.current = 0;
      processedCount.current = 0;
      setNodes([]);
      setEdges([]);
    }
  }, [events.length, setNodes, setEdges]);

  const handleNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    // Pass raw node_id and identifier so the drawer can filter events correctly
    onNodeClick?.(node.data.node_id as string, node.data.identifier as string);
  }, [onNodeClick]);

  return (
    <Box height="100%" width="100%" bg="slate.950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#333" gap={16} />
        <Controls />
      </ReactFlow>
    </Box>
  );
};
