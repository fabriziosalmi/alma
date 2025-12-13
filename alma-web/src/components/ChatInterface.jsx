import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';

export default function ChatInterface() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am ALMA. How can I help you orchestrate your infrastructure today?' }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = {
            role: 'user',
            content: input,
            timestamp: new Date().toLocaleTimeString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput(''); // Changed from setInputValue to setInput
        setIsTyping(true); // Changed from setIsLoading to setIsTyping

        // Safety timeout to prevent infinite loading state
        const safetyTimeout = setTimeout(() => {
            if (isTyping) {
                setIsTyping(false);
                console.warn("Chat stream safety timeout triggered.");
            }
        }, 30000);

        try {
            // Direct connection to backend to avoid Vite Proxy buffering issues with SSE
            const response = await fetch('http://localhost:8000/api/v1/conversation/chat-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage.content }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = {
                role: 'assistant',
                content: '',
                timestamp: new Date().toLocaleTimeString(),
            };

            setMessages((prev) => [...prev, assistantMessage]);

            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Process buffer for complete messages
                const parts = buffer.split('\n\n');

                // Keep the last part in buffer (it might be incomplete)
                buffer = parts.pop() || '';

                for (const part of parts) {
                    if (part.trim().startsWith('data: ')) {
                        const dataStr = part.trim().replace('data: ', '');
                        try {
                            const data = JSON.parse(dataStr);

                            if (data.type === 'text') {
                                assistantMessage.content += data.data;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            } else if (data.type === 'done') {
                                setIsTyping(false);
                            } else if (data.type === 'intent') {
                                // Optional: visualize intense processing
                            }
                        } catch (e) {
                            console.warn('Failed to parse SSE event:', dataStr);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: 'Sorry, I encountered an error connecting to the server.',
                    timestamp: new Date().toLocaleTimeString(),
                },
            ]);
            setIsTyping(false);
        } finally {
            clearTimeout(safetyTimeout);
            setIsTyping(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b border-slate-700/50 bg-slate-900/80 flex items-center gap-3">
                <div className="bg-cyan-500/20 p-2 rounded-lg">
                    <Sparkles className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="font-semibold text-slate-100">Neural Interface</h3>
                    <p className="text-xs text-slate-400">ALMA Core v0.7.5</p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'assistant' ? 'bg-cyan-600' : 'bg-purple-600'
                            }`}>
                            {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'assistant'
                            ? 'bg-slate-800/80 text-slate-200 rounded-tl-none border border-slate-700/50'
                            : 'bg-purple-600/20 text-purple-100 rounded-tr-none border border-purple-500/30'
                            }`}>
                            <p className="text-sm leading-relaxed">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center flex-shrink-0">
                            <Bot size={16} />
                        </div>
                        <div className="bg-slate-800/80 rounded-2xl rounded-tl-none p-4 border border-slate-700/50 flex items-center gap-2">
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-slate-900/80 border-t border-slate-700/50">
                <form onSubmit={handleSubmit} className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Describe your infrastructure needs..."
                        className="w-full bg-slate-800/50 border border-slate-600 rounded-xl py-3 pl-4 pr-12 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isTyping}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={16} />
                    </button>
                </form>
            </div>
        </div>
    );
}
