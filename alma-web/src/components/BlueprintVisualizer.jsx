import React, { useCallback, useMemo } from 'react';
import { Network } from 'lucide-react';
import {
    ReactFlow,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Cloud, Server, Database } from 'lucide-react';

// Custom Node Component
const CustomNode = ({ data, selected }) => {
    const Icon = data.icon;

    return (
        <div className={`px-4 py-3 shadow-xl rounded-xl border transition-all duration-200 min-w-[150px]
      ${selected
                ? 'bg-slate-800 border-cyan-400 shadow-cyan-500/20'
                : 'bg-slate-900 border-slate-700 hover:border-slate-600'
            }`}>
            <Handle type="target" position={Position.Top} className="!bg-slate-600 !w-3 !h-3" />

            <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${data.colorClass || 'bg-slate-800'}`}>
                    <Icon className={`w-5 h-5 ${data.iconClass || 'text-slate-300'}`} />
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-slate-200">{data.label}</h3>
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider">{data.subLabel}</p>
                </div>
            </div>

            <Handle type="source" position={Position.Bottom} className="!bg-slate-600 !w-3 !h-3" />
        </div>
    );
};

const initialNodes = [];
const initialEdges = [];

export default function BlueprintVisualizer() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    React.useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/v1/monitoring/stats/infrastructure');
                if (response.ok) {
                    const data = await response.json();

                    // Map icon strings to components
                    const mappedNodes = data.nodes.map(node => ({
                        ...node,
                        data: {
                            ...node.data,
                            icon: node.data.icon === 'Database' ? Database :
                                node.data.icon === 'Cloud' ? Cloud : Server
                        }
                    }));

                    setNodes(mappedNodes);
                    setEdges(data.edges);
                }
            } catch (error) {
                console.error("Failed to fetch infrastructure:", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, [setNodes, setEdges]);

    const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6 flex-none">
                <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <Network className="w-5 h-5 text-purple-400" />
                    Infrastructure View
                </h3>
                <span className="px-2 py-1 bg-cyan-500/10 text-cyan-400 text-xs rounded border border-cyan-500/20">
                    Interactive
                </span>
            </div>

            <div className="flex-1 border-2 border-dashed border-slate-800 rounded-xl overflow-hidden bg-slate-950/50">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    nodeTypes={nodeTypes}
                    fitView
                    className="bg-slate-950/0"
                >
                    <Background color="#1e293b" gap={20} size={1} />
                    <Controls className="!bg-slate-800 !border-slate-700 !fill-slate-400 [&>button]:!border-b-slate-700 hover:[&>button]:!bg-slate-700" />
                </ReactFlow>
            </div>
        </div>
    );
}
