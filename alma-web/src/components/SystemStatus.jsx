import React from 'react';
import { Activity, Cpu, HardDrive, Shield } from 'lucide-react';

const StatusCard = ({ icon: Icon, label, value, color }) => (
    <div className="bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-xl p-4 flex items-center gap-4 hover:bg-slate-800/60 transition-colors">
        <div className={`p-3 rounded-lg ${color} bg-opacity-20`}>
            <Icon className={`w-5 h-5 ${color.replace('bg-', 'text-')}`} />
        </div>
        <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
            <p className="text-lg font-bold text-slate-100">{value}</p>
        </div>
    </div>
);

export default function SystemStatus() {
    return (
        <div className="grid grid-cols-2 gap-4">
            <StatusCard
                icon={Cpu}
                label="CPU Usage"
                value="24%"
                color="bg-emerald-500"
            />
            <StatusCard
                icon={HardDrive}
                label="Memory"
                value="4.2 GB"
                color="bg-blue-500"
            />
            <StatusCard
                icon={Activity}
                label="Latency"
                value="45ms"
                color="bg-purple-500"
            />
            <StatusCard
                icon={Shield}
                label="Threats"
                value="0 Active"
                color="bg-cyan-500"
            />
        </div>
    );
}
