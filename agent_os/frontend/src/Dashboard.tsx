import React, { useState, useRef, useCallback } from 'react';
import { 
  Box, 
  Flex, 
  VStack, 
  HStack, 
  Text, 
  IconButton, 
  Button, 
  useDisclosure,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerHeader,
  DrawerBody,
  DrawerCloseButton,
  Divider,
  Tag,
  Badge,
  Code,
  Input,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import { LayoutDashboard, Wallet, Settings, Play, Terminal as TerminalIcon, ChevronRight, Clock, Cpu, Hash, FileText, Search, Layers, Zap, Calendar } from 'lucide-react';
import { MetricHeader } from './components/MetricHeader';
import { AgentGraph } from './components/AgentGraph';
import { useAgentStream, AgentEvent } from './hooks/useAgentStream';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8088/api';

export const Dashboard: React.FC = () => {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [scanDate, setScanDate] = useState(new Date().toISOString().split('T')[0]);
  const portfolioId = "main_portfolio";
  const { events, status, clearEvents } = useAgentStream(activeRunId);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedEvent, setSelectedEvent] = useState<AgentEvent | null>(null);
  const triggerLockRef = useRef(false);

  const startRun = useCallback(async (type: string) => {
    if (triggerLockRef.current || status === 'streaming' || status === 'connecting') return;
    triggerLockRef.current = true;
    setIsTriggering(true);
    try {
      clearEvents();
      const res = await axios.post(`${API_BASE}/run/${type}`, {
        portfolio_id: portfolioId,
        date: scanDate,
      });
      setActiveRunId(res.data.run_id);
    } catch (err) {
      console.error("Failed to start run:", err);
    } finally {
      triggerLockRef.current = false;
      setIsTriggering(false);
    }
  }, [status, portfolioId, scanDate, clearEvents]);

  const handleEventClick = (evt: AgentEvent) => {
    setSelectedEvent(evt);
    onOpen();
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'tool': return 'purple.400';
      case 'result': return 'green.400';
      case 'thought': return 'cyan.400';
      default: return 'whiteAlpha.600';
    }
  };

  const isRunning = isTriggering || status === 'connecting' || status === 'streaming';

  return (
    <Flex h="100vh" bg="slate.950" color="white" overflow="hidden">
      {/* Sidebar */}
      <VStack w="64px" bg="slate.900" borderRight="1px solid" borderColor="whiteAlpha.100" py={4} spacing={6}>
        <Box mb={4}><Text fontWeight="black" color="cyan.400" fontSize="xl">A</Text></Box>
        <IconButton aria-label="Dashboard" icon={<LayoutDashboard size={20} />} variant="ghost" color="cyan.400" _hover={{ bg: "whiteAlpha.100" }} />
        <IconButton aria-label="Portfolio" icon={<Wallet size={20} />} variant="ghost" color="whiteAlpha.600" _hover={{ bg: "whiteAlpha.100" }} />
        <IconButton aria-label="Settings" icon={<Settings size={20} />} variant="ghost" color="whiteAlpha.600" _hover={{ bg: "whiteAlpha.100" }} />
      </VStack>

      {/* Main Content */}
      <Flex flex="1" direction="column">
        {/* Top Metric Header */}
        <MetricHeader portfolioId={portfolioId} />

        {/* Dashboard Body */}
        <Flex flex="1" overflow="hidden">
          {/* Left Side: Graph Area */}
          <Box flex="1" position="relative" borderRight="1px solid" borderColor="whiteAlpha.100">
             <AgentGraph events={events} onNodeClick={handleEventClick} />
             
             {/* Floating Control Panel */}
             <Box position="absolute" top={4} left={4} bg="blackAlpha.800" p={3} borderRadius="lg" backdropFilter="blur(10px)" border="1px solid" borderColor="whiteAlpha.200">
                {/* Date Input Row */}
                <Flex align="center" gap={2} mb={2}>
                  <Calendar size={14} color="#4fd1c5" />
                  <Input
                    type="date"
                    size="xs"
                    value={scanDate}
                    onChange={(e) => setScanDate(e.target.value)}
                    bg="whiteAlpha.100"
                    border="1px solid"
                    borderColor="whiteAlpha.200"
                    borderRadius="md"
                    color="white"
                    w="140px"
                    fontSize="xs"
                    _hover={{ borderColor: 'whiteAlpha.400' }}
                    _focus={{ borderColor: 'cyan.400', boxShadow: '0 0 0 1px #4fd1c5' }}
                    sx={{
                      '&::-webkit-calendar-picker-indicator': {
                        filter: 'invert(1)',
                        cursor: 'pointer',
                      }
                    }}
                  />
                  <Tag size="sm" colorScheme={status === 'streaming' ? 'green' : status === 'completed' ? 'blue' : 'gray'}>
                    {status.toUpperCase()}
                  </Tag>
                </Flex>
                
                {/* Run Buttons Row */}
                <HStack spacing={2}>
                  <Button 
                    size="xs" 
                    leftIcon={<Search size={12} />} 
                    colorScheme="cyan" 
                    variant="solid"
                    onClick={() => startRun('scan')}
                    isLoading={isRunning}
                  >
                    Scan
                  </Button>
                  <Button 
                    size="xs" 
                    leftIcon={<Layers size={12} />} 
                    colorScheme="purple" 
                    variant="solid"
                    onClick={() => startRun('pipeline')}
                    isLoading={isRunning}
                  >
                    Pipeline
                  </Button>
                  <Button 
                    size="xs" 
                    leftIcon={<Wallet size={12} />} 
                    colorScheme="green" 
                    variant="solid"
                    onClick={() => startRun('portfolio')}
                    isLoading={isRunning}
                  >
                    Portfolio
                  </Button>
                  <Button 
                    size="xs" 
                    leftIcon={<Zap size={12} />} 
                    colorScheme="orange" 
                    variant="solid"
                    onClick={() => startRun('auto')}
                    isLoading={isRunning}
                  >
                    Auto
                  </Button>
                </HStack>
             </Box>
          </Box>

          {/* Right Side: Live Terminal */}
          <VStack w="420px" bg="blackAlpha.400" align="stretch" spacing={0}>
            <Flex p={3} bg="whiteAlpha.50" align="center" gap={2} borderBottom="1px solid" borderColor="whiteAlpha.100">
               <TerminalIcon size={16} color="#4fd1c5" />
               <Text fontSize="xs" fontWeight="bold" textTransform="uppercase" letterSpacing="wider">Live Terminal</Text>
               <Box flex="1" />
               <Badge variant="outline" fontSize="2xs" colorScheme="cyan">{events.length} events</Badge>
            </Flex>
            
            <Box flex="1" overflowY="auto" p={3} sx={{
              '&::-webkit-scrollbar': { width: '4px' },
              '&::-webkit-scrollbar-track': { background: 'transparent' },
              '&::-webkit-scrollbar-thumb': { background: 'whiteAlpha.300', borderRadius: 'full' }
            }}>
               {events.map((evt) => (
                 <Box 
                   key={evt.id} 
                   mb={2} 
                   fontSize="xs" 
                   fontFamily="mono"
                   p={2}
                   borderRadius="md"
                   cursor="pointer"
                   bg="whiteAlpha.50"
                   border="1px solid"
                   borderColor="transparent"
                   _hover={{ bg: 'whiteAlpha.100', borderColor: 'whiteAlpha.200' }}
                   transition="all 0.15s ease"
                   onClick={() => handleEventClick(evt)}
                 >
                   <Flex gap={2} align="center">
                     <Text color="whiteAlpha.400" minW="54px" fontSize="10px">[{evt.timestamp}]</Text>
                     <Text 
                       color={getEventColor(evt.type)} 
                       fontWeight="bold"
                       fontSize="10px"
                       noOfLines={1}
                       maxW="110px"
                     >
                        {evt.agent}
                     </Text>
                     <ChevronRight size={10} style={{ marginTop: 1, opacity: 0.4 }} />
                     <Text color="whiteAlpha.800" fontSize="10px" noOfLines={1} flex="1">{evt.message}</Text>
                   </Flex>
                   {evt.metrics && (evt.metrics.tokens_in || evt.metrics.tokens_out || evt.metrics.latency_ms) && (
                     <HStack spacing={3} mt={1} ml="58px" color="whiteAlpha.400" fontSize="9px">
                       {(evt.metrics.tokens_in || evt.metrics.tokens_out) ? (
                         <Text>tokens: {evt.metrics.tokens_in || 0}/{evt.metrics.tokens_out || 0}</Text>
                       ) : null}
                       {evt.metrics.latency_ms ? (
                         <Text>{evt.metrics.latency_ms}ms</Text>
                       ) : null}
                     </HStack>
                   )}
                 </Box>
               ))}
               {events.length === 0 && (
                 <Flex h="100%" align="center" justify="center" direction="column" gap={4} opacity={0.3}>
                    <TerminalIcon size={48} />
                    <Text fontSize="sm">Awaiting agent activation...</Text>
                 </Flex>
               )}
            </Box>
          </VStack>
        </Flex>
      </Flex>

      {/* Event Detail Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="lg">
        <DrawerOverlay backdropFilter="blur(4px)" />
        <DrawerContent bg="slate.900" color="white" borderLeft="1px solid" borderColor="whiteAlpha.200">
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px" borderColor="whiteAlpha.100" pb={3}>
             <Flex align="center" gap={2}>
               <Cpu size={18} color="#4fd1c5" />
               <Text fontSize="md">Event Detail</Text>
             </Flex>
             {selectedEvent && (
               <Flex gap={2} mt={2}>
                 <Badge colorScheme={
                   selectedEvent.type === 'result' ? 'green' 
                   : selectedEvent.type === 'tool' ? 'purple' 
                   : 'cyan'
                 } variant="subtle">
                   {selectedEvent.type.toUpperCase()}
                 </Badge>
                 <Badge variant="outline" colorScheme="gray" fontSize="2xs">
                   {selectedEvent.agent}
                 </Badge>
               </Flex>
             )}
          </DrawerHeader>
          <DrawerBody pt={4}>
            {selectedEvent && (
              <VStack align="stretch" spacing={4}>
                {/* Metrics Summary */}
                <Box>
                  <Text fontSize="xs" fontWeight="bold" color="whiteAlpha.500" textTransform="uppercase" mb={3}>Metrics</Text>
                  <VStack spacing={2} align="stretch">
                    <Flex justify="space-between" bg="whiteAlpha.50" p={2} borderRadius="md">
                      <Flex align="center" gap={2}>
                        <Cpu size={12} color="#4fd1c5" />
                        <Text fontSize="xs" color="whiteAlpha.600">Model</Text>
                      </Flex>
                      <Text fontSize="xs" fontWeight="bold" maxW="250px" textAlign="right" wordBreak="break-all">
                        {selectedEvent.metrics?.model || selectedEvent.details?.model_used || 'N/A'}
                      </Text>
                    </Flex>
                    <Flex justify="space-between" bg="whiteAlpha.50" p={2} borderRadius="md">
                      <Flex align="center" gap={2}>
                        <Clock size={12} color="#4fd1c5" />
                        <Text fontSize="xs" color="whiteAlpha.600">Latency</Text>
                      </Flex>
                      <Text fontSize="xs" fontWeight="bold">
                        {selectedEvent.metrics?.latency_ms || selectedEvent.details?.latency_ms || 0}ms
                      </Text>
                    </Flex>
                    <Flex justify="space-between" bg="whiteAlpha.50" p={2} borderRadius="md">
                      <Flex align="center" gap={2}>
                        <Hash size={12} color="#4fd1c5" />
                        <Text fontSize="xs" color="whiteAlpha.600">Input / Output Tokens</Text>
                      </Flex>
                      <Text fontSize="xs" fontWeight="bold">
                        {selectedEvent.metrics?.tokens_in || selectedEvent.details?.input_tokens || 0} / {selectedEvent.metrics?.tokens_out || selectedEvent.details?.output_tokens || 0}
                      </Text>
                    </Flex>
                  </VStack>
                </Box>

                <Divider borderColor="whiteAlpha.100" />

                {/* Metadata */}
                <Box>
                  <Text fontSize="xs" fontWeight="bold" color="whiteAlpha.500" textTransform="uppercase" mb={2}>Metadata</Text>
                  <VStack spacing={1} align="stretch" fontSize="xs" color="whiteAlpha.500">
                    <Flex justify="space-between">
                      <Text>Timestamp</Text>
                      <Text color="whiteAlpha.800">{selectedEvent.timestamp}</Text>
                    </Flex>
                    <Flex justify="space-between">
                      <Text>Node ID</Text>
                      <Text color="whiteAlpha.800" maxW="250px" noOfLines={1}>{selectedEvent.node_id}</Text>
                    </Flex>
                    <Flex justify="space-between">
                      <Text>Parent</Text>
                      <Text color="whiteAlpha.800" maxW="250px" noOfLines={1}>{selectedEvent.parent_node_id || '—'}</Text>
                    </Flex>
                  </VStack>
                </Box>

                <Divider borderColor="whiteAlpha.100" />

                {/* Request / Response Tabs */}
                <Tabs variant="soft-rounded" colorScheme="cyan" size="sm">
                  <TabList>
                    <Tab fontSize="xs" _selected={{ bg: 'cyan.900', color: 'cyan.200' }}>Request</Tab>
                    <Tab fontSize="xs" _selected={{ bg: 'cyan.900', color: 'cyan.200' }}>Response</Tab>
                  </TabList>
                  <TabPanels>
                    <TabPanel px={0}>
                      <Code 
                        display="block" 
                        p={3} 
                        bg="blackAlpha.600" 
                        borderRadius="md" 
                        fontSize="10px" 
                        whiteSpace="pre-wrap"
                        wordBreak="break-word"
                        maxH="400px"
                        overflowY="auto"
                        color="whiteAlpha.800"
                        sx={{
                          '&::-webkit-scrollbar': { width: '4px' },
                          '&::-webkit-scrollbar-track': { background: 'transparent' },
                          '&::-webkit-scrollbar-thumb': { background: 'whiteAlpha.300' }
                        }}
                      >
                        {selectedEvent.details?.request_content || selectedEvent.message || 'No request data captured'}
                      </Code>
                    </TabPanel>
                    <TabPanel px={0}>
                      <Code 
                        display="block" 
                        p={3} 
                        bg="blackAlpha.600" 
                        borderRadius="md" 
                        fontSize="10px" 
                        whiteSpace="pre-wrap"
                        wordBreak="break-word"
                        maxH="400px"
                        overflowY="auto"
                        color="whiteAlpha.800"
                        sx={{
                          '&::-webkit-scrollbar': { width: '4px' },
                          '&::-webkit-scrollbar-track': { background: 'transparent' },
                          '&::-webkit-scrollbar-thumb': { background: 'whiteAlpha.300' }
                        }}
                      >
                        {selectedEvent.details?.response_content || selectedEvent.metrics?.raw_json_response || 'No response data captured'}
                      </Code>
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </VStack>
            )}
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Flex>
  );
};
