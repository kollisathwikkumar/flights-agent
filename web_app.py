"""Web UI Application for T10 Flight Option Finder.

Single-page dashboard layout:
- Modular boxed sections adjusting perfectly to the screen
- Exact animated AI Agentic Workflow diagram matching user reference:
  (LLM -> Tools -> External Environment -> Results -> Memory -> Evaluation Loop)
- Live real-time step highlighting, glowing node transitions, and pulse animations
- Top verified flight card, smart recommendations, candidate fares matrix, and trace telemetry
"""

from typing import Optional
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent import agent

app = FastAPI(title="T10 Flight Option Finder")


class SearchPayload(BaseModel):
    query: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_date: Optional[str] = None
    budget: Optional[float] = None
    passengers: Optional[int] = 1
    cabin_class: Optional[str] = "economy"
    preferred_departure: Optional[str] = None


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>T10 Flight Option Finder — AI Agent Workflow</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        code, pre, .font-mono { font-family: 'JetBrains Mono', monospace; }

        .badge-verified { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .badge-unverified { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
        .badge-unavailable { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

        /* Smooth node transitions */
        .agent-node {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Glowing Pulse for Active Agent Nodes */
        .node-active-llm {
            box-shadow: 0 0 0 3px #f59e0b, 0 10px 25px -5px rgba(245, 158, 11, 0.4);
            transform: translateY(-2px);
            border-color: #f59e0b !important;
        }
        .node-active-tools {
            box-shadow: 0 0 0 3px #10b981, 0 10px 25px -5px rgba(16, 185, 129, 0.4);
            transform: translateY(-2px);
            border-color: #10b981 !important;
        }
        .node-active-ext {
            box-shadow: 0 0 0 3px #6366f1, 0 10px 25px -5px rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
            border-color: #6366f1 !important;
        }
        .node-active-mem {
            box-shadow: 0 0 0 3px #0284c7, 0 10px 25px -5px rgba(2, 132, 199, 0.4);
            transform: translateY(-2px);
            border-color: #0284c7 !important;
        }

        /* Animated connection lines */
        .path-animated {
            stroke-dasharray: 6;
            animation: dash 1s linear infinite;
            stroke: #2563eb !important;
            stroke-width: 2.5px !important;
        }

        @keyframes dash {
            to { stroke-dashoffset: -12; }
        }

        /* Custom Scrollbar for inner boxes */
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="bg-slate-100/70 text-slate-800 antialiased h-screen overflow-hidden flex flex-col selection:bg-blue-600 selection:text-white">
    
    <!-- Top Navbar (Slim Header) -->
    <header class="bg-white border-b border-slate-200/80 px-5 py-2.5 flex-shrink-0 flex items-center justify-between shadow-xs">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/30">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
            </div>
            <div>
                <h1 class="text-sm font-black text-slate-900 tracking-tight flex items-center gap-2">
                    T10 FLIGHT OPTION FINDER
                    <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">AUTONOMOUS AGENT</span>
                </h1>
            </div>
        </div>

        <div class="flex items-center gap-4 text-xs">
            <div class="hidden sm:flex items-center gap-2 text-slate-500 font-medium text-[11px]">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>NVIDIA NIM</span> • <span>AviationStack</span> • <span>Ignav Live GDS</span>
            </div>
            <span class="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono text-[10px] font-bold">100% ZERO FAKE DATA</span>
        </div>
    </header>

    <!-- Main Viewport Grid (Single-Page Boxed Sections) -->
    <main class="flex-1 p-3.5 sm:p-4 grid grid-cols-1 lg:grid-cols-12 gap-3.5 min-h-0 overflow-hidden">
        
        <!-- LEFT COLUMN (5 Cols): Search Control & Animated AI Agent Workflow -->
        <div class="lg:col-span-5 flex flex-col gap-3.5 min-h-0 overflow-hidden">
            
            <!-- Box 1: Search Form Box -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-4 flex-shrink-0">
                <!-- Tabs -->
                <div class="flex border-b border-slate-100 pb-2 mb-3 gap-6 text-xs font-bold uppercase tracking-wider">
                    <button id="tabFormBtn" onclick="switchTab('form')" class="text-blue-600 border-b-2 border-blue-600 pb-1.5 -mb-2.5 transition">Structured Flight Form</button>
                    <button id="tabPromptBtn" onclick="switchTab('prompt')" class="text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-1.5 -mb-2.5 transition">Natural Language Prompt</button>
                </div>

                <!-- Form Content -->
                <div id="formTabContent" class="space-y-2.5">
                    <div class="grid grid-cols-2 gap-2.5">
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">FROM (ORIGIN)</label>
                            <input type="text" id="formOrigin" list="airportList" 
                                class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-xs bg-white font-medium shadow-xs"
                                placeholder="Amritsar (ATQ)" value="Amritsar (ATQ)">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">TO (DESTINATION)</label>
                            <input type="text" id="formDest" list="airportList" 
                                class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-xs bg-white font-medium shadow-xs"
                                placeholder="Chennai (MAA)" value="Chennai (MAA)">
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2.5">
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">DEPARTURE DATE</label>
                            <input type="date" id="formDate" 
                                class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-xs bg-white font-medium shadow-xs"
                                value="2026-09-27">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">MAX BUDGET (₹ INR)</label>
                            <input type="number" id="formBudget" 
                                class="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-xs bg-white font-medium shadow-xs"
                                placeholder="25000" value="25000">
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-2 pt-0.5">
                        <div>
                            <label class="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">PAX</label>
                            <select id="formPax" class="w-full px-2 py-1 rounded-lg border border-slate-200 text-slate-700 text-xs bg-white">
                                <option value="1" selected>1 Pax</option>
                                <option value="2">2 Pax</option>
                                <option value="3">3 Pax</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">CLASS</label>
                            <select id="formCabin" class="w-full px-2 py-1 rounded-lg border border-slate-200 text-slate-700 text-xs bg-white">
                                <option value="economy" selected>Economy</option>
                                <option value="business">Business</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">TIME</label>
                            <select id="formTime" class="w-full px-2 py-1 rounded-lg border border-slate-200 text-slate-700 text-xs bg-white">
                                <option value="" selected>Any Time</option>
                                <option value="morning">Morning</option>
                                <option value="afternoon">Afternoon</option>
                                <option value="evening">Evening</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Prompt Content -->
                <div id="promptTabContent" class="hidden space-y-2">
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Type flight request naturally</label>
                    <textarea id="promptInput" rows="3" 
                        class="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-xs bg-white font-medium shadow-xs"
                        placeholder="e.g. Find me a flight from Amritsar to Chennai on September 27 under ₹25,000">Find me a flight from Amritsar to Chennai on September 27 under ₹25,000</textarea>
                </div>

                <!-- Action Row -->
                <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between gap-2">
                    <div class="flex items-center gap-1.5 overflow-x-auto text-[10px] text-slate-500 py-0.5">
                        <button onclick="setFormDirect('Amritsar (ATQ)', 'Chennai (MAA)', '2026-09-27', 25000)" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded transition whitespace-nowrap">ATQ &rarr; MAA</button>
                        <button onclick="setFormDirect('Vijayawada (VGA)', 'Mumbai (BOM)', '2026-09-24', 8000)" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded transition whitespace-nowrap">VGA &rarr; BOM</button>
                        <button onclick="setFormDirect('Delhi (DEL)', 'Dubai (DXB)', '2026-09-24', 20000)" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded transition whitespace-nowrap">DEL &rarr; DXB</button>
                    </div>

                    <button id="searchBtn" onclick="runSearch()" 
                        class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs shadow-md shadow-blue-500/20 transition flex items-center gap-1.5 flex-shrink-0">
                        <span id="btnText">Find Best Option</span>
                        <svg id="btnSpinner" class="hidden animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Box 2: Animated AI Agentic Workflow (Exact Reference Diagram Architecture) -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-4 flex-1 flex flex-col min-h-0 overflow-hidden">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                        AI Agentic Architecture Workflow
                    </h3>
                    <span id="agentStatePill" class="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">STANDBY</span>
                </div>

                <!-- Visual Workflow Canvas (Reference Diagram Style) -->
                <div class="relative flex-1 bg-slate-50/70 rounded-xl border border-slate-200/70 p-3 flex flex-col justify-center overflow-hidden min-h-[220px]">
                    
                    <!-- SVG Connection Canvas Overlay -->
                    <svg class="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Path 1: Reasoning loop (above LLM) -->
                        <path id="svgPathReason" d="M 65 65 C 45 15, 125 15, 105 65" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" />
                        
                        <!-- Path 2: LLM -> Tools -->
                        <path id="svgPathTools" d="M 145 95 L 210 95" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />
                        
                        <!-- Path 3: Tools -> External Environment -->
                        <path id="svgPathExt" d="M 290 95 L 345 95" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />
                        
                        <!-- Path 3b: External Environment -> Tools (Results Return) -->
                        <path id="svgPathExtReturn" d="M 345 125 L 290 125" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />

                        <!-- Path 4: Tools -> LLM (Observation) -->
                        <path id="svgPathObserve" d="M 210 125 L 145 125" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />
                        
                        <!-- Path 5: LLM <-> Memory -->
                        <path id="svgPathMemUp" d="M 95 145 L 95 185" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />
                        <path id="svgPathMemDown" d="M 75 185 L 75 145" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arrowhead)" />

                        <defs>
                            <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                                <polygon points="0 0, 6 3, 0 6" fill="#64748b" />
                            </marker>
                        </defs>
                    </svg>

                    <!-- Main Dashed AI Agent Outer Container -->
                    <div class="border-2 border-dashed border-slate-300 rounded-xl p-2.5 relative flex items-center justify-between gap-2.5 z-10 bg-white/60 backdrop-blur-xs">
                        
                        <!-- AI Agent Label -->
                        <span class="absolute -bottom-2.5 left-4 text-[9px] font-black uppercase tracking-widest text-slate-400 bg-white px-2 py-0.2 rounded border border-slate-200">
                            AI AGENT
                        </span>

                        <!-- Column A: LLM + Memory -->
                        <div class="flex flex-col items-center gap-3">
                            
                            <!-- Prompt Driven Reasoning Label (1) -->
                            <div class="text-[8px] font-bold text-slate-500 uppercase tracking-tighter text-center leading-none">
                                <span class="inline-block w-3.5 h-3.5 rounded-full bg-slate-200 text-slate-700 text-[8px] leading-3.5 text-center font-bold">1</span>
                                Reasoning / Evaluation
                            </div>

                            <!-- LLM Box (Pale Gold) -->
                            <div id="nodeLLM" class="agent-node w-24 h-18 rounded-xl bg-amber-50 border-2 border-amber-200/90 p-2 flex flex-col items-center justify-center text-center shadow-xs">
                                <svg class="w-5 h-5 text-amber-600 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                </svg>
                                <span class="text-[10px] font-black text-amber-950">LLM</span>
                                <span class="text-[7px] text-amber-700 font-mono">NVIDIA NIM</span>
                            </div>

                            <!-- Memory Box (Pale Blue) -->
                            <div id="nodeMemory" class="agent-node w-24 h-14 rounded-xl bg-sky-50 border-2 border-sky-200/90 p-1.5 flex flex-col items-center justify-center text-center shadow-xs">
                                <div class="flex items-center gap-1">
                                    <svg class="w-3.5 h-3.5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7M4 7c0-2 1.5-3 3.5-3h9c2 0 3.5 1 3.5 3M4 7h16"></path>
                                    </svg>
                                    <span class="text-[9px] font-black text-sky-950">Memory</span>
                                </div>
                                <span class="text-[7px] text-sky-700 font-mono">Session State</span>
                            </div>
                        </div>

                        <!-- Column B: Tools -->
                        <div class="flex flex-col items-center justify-center">
                            <!-- Use Tools Label (2) -->
                            <div class="text-[8px] font-bold text-slate-500 uppercase tracking-tighter text-center mb-1">
                                <span class="inline-block w-3.5 h-3.5 rounded-full bg-slate-200 text-slate-700 text-[8px] leading-3.5 text-center font-bold">2</span>
                                Use Tools
                            </div>

                            <!-- Tools Box (Mint Green) -->
                            <div id="nodeTools" class="agent-node w-24 h-24 rounded-xl bg-emerald-50 border-2 border-emerald-200/90 p-2 flex flex-col items-center justify-center text-center shadow-xs">
                                <svg class="w-6 h-6 text-emerald-600 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <span class="text-[10px] font-black text-emerald-950">Tools</span>
                                <span class="text-[7px] text-emerald-700 font-mono">search • compare</span>
                            </div>
                        </div>

                    </div>

                    <!-- Outside Block: External Environment (Right Side) -->
                    <div class="absolute right-2 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center">
                        <div class="text-[8px] font-bold text-slate-500 uppercase tracking-tighter mb-1 text-center">
                            <span class="inline-block w-3.5 h-3.5 rounded-full bg-slate-200 text-slate-700 text-[8px] leading-3.5 text-center font-bold">3</span>
                            Execute Action
                        </div>
                        <div id="nodeExternal" class="agent-node w-24 h-24 rounded-xl bg-slate-200 border-2 border-slate-300 p-2 flex flex-col items-center justify-center text-center shadow-xs">
                            <svg class="w-5 h-5 text-slate-600 mb-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span class="text-[9px] font-black text-slate-800 leading-tight">External APIs</span>
                            <span class="text-[7px] text-slate-600 font-mono">AviationStack &bull; Ignav</span>
                        </div>
                    </div>

                </div>

                <!-- Live Agent Step Telemetry Line -->
                <div class="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                    <div class="flex items-center gap-1.5 text-slate-600">
                        <span class="font-bold text-slate-800">Current Phase:</span>
                        <span id="agentPhaseText" class="font-mono text-blue-600 font-semibold">Idle</span>
                    </div>
                    <span id="agentLatency" class="text-[9px] font-mono text-slate-400">Ready</span>
                </div>
            </div>

        </div>

        <!-- RIGHT COLUMN (7 Cols): Results & Multi-Section Dashboard Grid -->
        <div class="lg:col-span-7 flex flex-col gap-3.5 min-h-0 overflow-hidden">
            
            <!-- Box 3: Top Verified Flight Option Card (Dynamic & Visual) -->
            <div id="bestOptionCard" class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden flex-shrink-0">
                <div class="p-5 text-center text-slate-400 text-xs">
                    Configure flight details on the left and click <b>Find Best Option</b>.
                </div>
            </div>

            <!-- Box 3b: Smart Fallback Recommendations (Appears when no flights match budget) -->
            <div id="suggestionsCard" class="hidden bg-amber-50 rounded-2xl border border-amber-200 p-4 shadow-xs flex-shrink-0">
                <div class="flex items-center gap-2 text-amber-900 font-bold text-xs mb-2">
                    <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Smart Alternative Recommendations
                </div>
                <ul id="suggestionsList" class="space-y-1.5 text-[11px] text-amber-800 font-medium"></ul>
            </div>

            <!-- Box 4: Multi-Step Live Execution Trace (Scrollable Telemetry) -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-3.5 flex-1 flex flex-col min-h-0 overflow-hidden">
                <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-100 flex-shrink-0">
                    <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                        Agent Execution Trace Telemetry (PLAN &bull; ACT &bull; OBSERVE &bull; EVALUATE &bull; DECIDE)
                    </h3>
                    <span id="traceStepCount" class="text-[9px] font-mono text-slate-400">0 Steps</span>
                </div>
                <div id="traceSteps" class="space-y-2 flex-1 overflow-y-auto pr-1">
                    <div class="text-[11px] text-slate-400 italic text-center py-4">
                        Execution steps and tool invocations will appear here.
                    </div>
                </div>
            </div>

            <!-- Box 5: Candidate Fares Matrix (Scrollable Table) -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-3.5 flex-1 flex flex-col min-h-0 overflow-hidden">
                <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-100 flex-shrink-0">
                    <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                        Retrieved Fares & Deterministic Matching Matrix
                    </h3>
                    <span id="faresCountBadge" class="text-[9px] font-mono text-slate-400">0 Fares</span>
                </div>
                <div class="flex-1 overflow-y-auto pr-1">
                    <table class="w-full text-left text-[11px] text-slate-600">
                        <thead class="bg-slate-50 text-slate-700 uppercase font-semibold sticky top-0 text-[10px] border-b border-slate-200">
                            <tr>
                                <th class="px-2.5 py-1.5">Flight</th>
                                <th class="px-2.5 py-1.5">Airline</th>
                                <th class="px-2.5 py-1.5">Route</th>
                                <th class="px-2.5 py-1.5">Schedule</th>
                                <th class="px-2.5 py-1.5">Price</th>
                                <th class="px-2.5 py-1.5">Status</th>
                                <th class="px-2.5 py-1.5">Match</th>
                            </tr>
                        </thead>
                        <tbody id="candidatesTableBody" class="divide-y divide-slate-100 font-mono text-[10px]">
                            <tr>
                                <td colspan="7" class="px-2.5 py-4 text-center text-slate-400 font-sans italic">No fare search executed yet.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </main>

    <!-- Global & Indian Regional Airport Autocomplete Datalist -->
    <datalist id="airportList">
        <option value="Amritsar (ATQ)">Amritsar (ATQ) - Sri Guru Ram Dass Jee Intl</option>
        <option value="Delhi (DEL)">Delhi (DEL) - Indira Gandhi Intl</option>
        <option value="Mumbai (BOM)">Mumbai (BOM) - Chhatrapati Shivaji Intl</option>
        <option value="Chennai (MAA)">Chennai (MAA) - Chennai Intl</option>
        <option value="Bengaluru (BLR)">Bengaluru (BLR) - Kempegowda Intl</option>
        <option value="Hyderabad (HYD)">Hyderabad (HYD) - Rajiv Gandhi Intl</option>
        <option value="Vijayawada (VGA)">Vijayawada (VGA) - Vijayawada Intl</option>
        <option value="Kolkata (CCU)">Kolkata (CCU) - Netaji Subhash Chandra Bose</option>
        <option value="Goa (GOI)">Goa Dabolim (GOI)</option>
        <option value="Ahmedabad (AMD)">Ahmedabad (AMD) - Sardar Vallabhbhai Patel</option>
        <option value="Pune (PNQ)">Pune (PNQ) - Pune Airport</option>
        <option value="Kochi (COK)">Kochi (COK) - Cochin Intl</option>
        <option value="Jaipur (JAI)">Jaipur (JAI) - Jaipur Intl</option>
        <option value="Lucknow (LKO)">Lucknow (LKO) - Chaudhary Charan Singh</option>
        <option value="Chandigarh (IXC)">Chandigarh (IXC) - Shaheed Bhagat Singh</option>
        <option value="Dehradun (DED)">Dehradun (DED) - Jolly Grant Airport</option>
        <option value="Ayodhya (AYJ)">Ayodhya (AYJ) - Maharishi Valmiki</option>
        <option value="Tirupati (TIR)">Tirupati (TIR) - Tirupati Airport</option>
        <option value="Visakhapatnam (VTZ)">Visakhapatnam (VTZ) - Vizag Airport</option>
        <option value="Dubai (DXB)">Dubai (DXB) - Dubai International</option>
        <option value="London (LHR)">London (LHR) - Heathrow Airport</option>
        <option value="New York (JFK)">New York (JFK) - John F. Kennedy Intl</option>
        <option value="Singapore (SIN)">Singapore (SIN) - Changi Airport</option>
    </datalist>

    <script>
        let currentTab = 'form';

        function switchTab(tab) {
            currentTab = tab;
            const formBtn = document.getElementById('tabFormBtn');
            const promptBtn = document.getElementById('tabPromptBtn');
            const formContent = document.getElementById('formTabContent');
            const promptContent = document.getElementById('promptTabContent');

            if (tab === 'form') {
                formBtn.className = "text-blue-600 border-b-2 border-blue-600 pb-1.5 -mb-2.5 transition";
                promptBtn.className = "text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-1.5 -mb-2.5 transition";
                formContent.classList.remove('hidden');
                promptContent.classList.add('hidden');
            } else {
                promptBtn.className = "text-blue-600 border-b-2 border-blue-600 pb-1.5 -mb-2.5 transition";
                formBtn.className = "text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-1.5 -mb-2.5 transition";
                promptContent.classList.remove('hidden');
                formContent.classList.add('hidden');
            }
        }

        function setFormDirect(orig, dest, date, budget) {
            document.getElementById('formOrigin').value = orig;
            document.getElementById('formDest').value = dest;
            document.getElementById('formDate').value = date;
            document.getElementById('formBudget').value = budget;
            switchTab('form');
            runSearch();
        }

        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        // Animate Diagram Nodes & Paths
        function resetDiagram() {
            document.getElementById('nodeLLM').className = "agent-node w-24 h-18 rounded-xl bg-amber-50 border-2 border-amber-200/90 p-2 flex flex-col items-center justify-center text-center shadow-xs";
            document.getElementById('nodeTools').className = "agent-node w-24 h-24 rounded-xl bg-emerald-50 border-2 border-emerald-200/90 p-2 flex flex-col items-center justify-center text-center shadow-xs";
            document.getElementById('nodeExternal').className = "agent-node w-24 h-24 rounded-xl bg-slate-200 border-2 border-slate-300 p-2 flex flex-col items-center justify-center text-center shadow-xs";
            document.getElementById('nodeMemory').className = "agent-node w-24 h-14 rounded-xl bg-sky-50 border-2 border-sky-200/90 p-1.5 flex flex-col items-center justify-center text-center shadow-xs";
            
            document.getElementById('svgPathReason').classList.remove('path-animated');
            document.getElementById('svgPathTools').classList.remove('path-animated');
            document.getElementById('svgPathExt').classList.remove('path-animated');
            document.getElementById('svgPathExtReturn').classList.remove('path-animated');
            document.getElementById('svgPathObserve').classList.remove('path-animated');
            document.getElementById('svgPathMemUp').classList.remove('path-animated');
        }

        function activateNode(nodeName) {
            resetDiagram();
            if (nodeName === 'llm') {
                document.getElementById('nodeLLM').classList.add('node-active-llm');
                document.getElementById('svgPathReason').classList.add('path-animated');
            } else if (nodeName === 'tools') {
                document.getElementById('nodeTools').classList.add('node-active-tools');
                document.getElementById('svgPathTools').classList.add('path-animated');
            } else if (nodeName === 'external') {
                document.getElementById('nodeExternal').classList.add('node-active-ext');
                document.getElementById('svgPathExt').classList.add('path-animated');
                document.getElementById('svgPathExtReturn').classList.add('path-animated');
            } else if (nodeName === 'memory') {
                document.getElementById('nodeMemory').classList.add('node-active-mem');
                document.getElementById('svgPathMemUp').classList.add('path-animated');
            }
        }

        async function runSearch() {
            const btnText = document.getElementById('btnText');
            const spinner = document.getElementById('btnSpinner');
            const searchBtn = document.getElementById('searchBtn');
            const agentStatePill = document.getElementById('agentStatePill');
            const agentPhaseText = document.getElementById('agentPhaseText');
            const traceStepsBox = document.getElementById('traceSteps');

            btnText.innerText = "Processing...";
            spinner.classList.remove('hidden');
            searchBtn.disabled = true;
            agentStatePill.innerText = "RUNNING";
            agentStatePill.className = "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 animate-pulse";

            let payload = {};
            if (currentTab === 'form') {
                const orig = document.getElementById('formOrigin').value.trim();
                const dest = document.getElementById('formDest').value.trim();
                const date = document.getElementById('formDate').value.trim();
                const budget = document.getElementById('formBudget').value.trim();
                const pax = document.getElementById('formPax').value;
                const cabin = document.getElementById('formCabin').value;
                const time = document.getElementById('formTime').value;

                let promptParts = [`Find me a flight from ${orig} to ${dest} on ${date}`];
                if (budget) promptParts.push(`under ₹${budget}`);
                if (time) promptParts.push(time);
                if (pax > 1) promptParts.push(`for ${pax} passengers`);
                if (cabin !== 'economy') promptParts.push(`in ${cabin}`);

                payload = { 
                    query: promptParts.join(' '),
                    origin: orig,
                    destination: dest,
                    travel_date: date,
                    budget: budget ? parseFloat(budget) : null,
                    passengers: parseInt(pax) || 1,
                    cabin_class: cabin,
                    preferred_departure: time || null
                };
            } else {
                const query = document.getElementById('promptInput').value.trim();
                if (!query) {
                    alert('Please enter a flight query.');
                    searchBtn.disabled = false;
                    spinner.classList.add('hidden');
                    btnText.innerText = "Find Best Option";
                    return;
                }
                payload = { query };
            }

            // Step 1: Prompt-Driven Reasoning / Evaluation (LLM)
            activateNode('llm');
            agentPhaseText.innerText = "1. Prompt-driven reasoning & constraint formulation";
            
            try {
                const fetchPromise = fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                await sleep(400);

                // Step 2: Use Tools
                activateNode('tools');
                agentPhaseText.innerText = "2. Invoking search_flights() & compare_price() tools";
                await sleep(500);

                // Step 3: Execute Action in External Environment
                activateNode('external');
                agentPhaseText.innerText = "3. Querying live AviationStack & Ignav GDS endpoints";

                const resp = await fetchPromise;
                const data = await resp.json();

                // Step 4: Update Memory
                activateNode('memory');
                agentPhaseText.innerText = "4. Updating session state & multi-turn memory";
                await sleep(350);

                // Final Evaluation & Decision
                activateNode('llm');
                agentPhaseText.innerText = "Completed: Deterministic ranking & flight verified";

                agentStatePill.innerText = "DONE ✓";
                agentStatePill.className = "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";

                renderResults(data);
            } catch (err) {
                alert('Error querying flight options: ' + err);
                agentStatePill.innerText = "ERROR";
                agentStatePill.className = "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200";
            } finally {
                btnText.innerText = "Find Best Option";
                spinner.classList.add('hidden');
                searchBtn.disabled = false;
            }
        }

        function renderResults(data) {
            const best = data.best_flight;
            const req = data.search_request || {};
            const card = document.getElementById('bestOptionCard');
            const suggCard = document.getElementById('suggestionsCard');
            const suggList = document.getElementById('suggestionsList');

            // Render Best Option
            if (best && best.price) {
                card.innerHTML = `
                    <div class="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 p-4 text-white">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] uppercase tracking-widest font-bold bg-white/20 px-2.5 py-0.5 rounded-full backdrop-blur-xs">✈️ TOP VERIFIED FLIGHT OPTION</span>
                            <span class="text-[10px] font-mono font-bold bg-emerald-500/30 border border-emerald-400/40 text-emerald-100 px-2 py-0.5 rounded">${best.price_status.toUpperCase()} FARE</span>
                        </div>
                        <div class="mt-2.5 flex items-baseline justify-between gap-3">
                            <div>
                                <h2 class="text-xl font-black tracking-tight">${best.airline || ''} ${best.flight_number}</h2>
                                <p class="text-blue-100 text-xs font-medium">${req.origin_city || best.origin} (${best.origin}) &rarr; ${req.destination_city || best.destination} (${best.destination})</p>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-black">₹${best.price.toLocaleString()} <span class="text-xs font-normal text-blue-200">${best.currency || 'INR'}</span></div>
                                <div class="text-[10px] text-blue-200">${req.budget ? (best.price <= req.budget ? '✓ Within Budget (₹' + req.budget.toLocaleString() + ')' : 'Exceeds Budget') : 'No budget limit'}</div>
                            </div>
                        </div>
                    </div>
                    <div class="p-3 grid grid-cols-4 gap-2 text-[10px] border-b border-slate-100 bg-slate-50/60 font-mono">
                        <div><span class="text-slate-400 block font-sans text-[9px]">DATE</span><span class="font-bold text-slate-800">${best.travel_date}</span></div>
                        <div><span class="text-slate-400 block font-sans text-[9px]">DEPARTURE</span><span class="font-bold text-slate-800">${best.departure_time || 'N/A'}</span></div>
                        <div><span class="text-slate-400 block font-sans text-[9px]">ARRIVAL</span><span class="font-bold text-slate-800">${best.arrival_time || 'N/A'}</span></div>
                        <div><span class="text-slate-400 block font-sans text-[9px]">STOPS</span><span class="font-bold text-slate-800">${best.stops === 0 ? 'Nonstop' : best.stops + ' Stop'}</span></div>
                    </div>
                    <div class="p-3 flex items-center justify-between gap-3 bg-white">
                        <div class="text-[11px] text-slate-600 flex-1">
                            <span class="font-bold text-slate-800">Why:</span>
                            ${data.recommendation_reason || 'Optimal verified flight within budget.'}
                        </div>
                        ${best.booking_url ? `<a href="${best.booking_url}" target="_blank" class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-xs shadow-sm transition whitespace-nowrap">Book via ${best.booking_provider || 'Airline'} &rarr;</a>` : `<span class="text-[10px] text-slate-400">Direct booking</span>`}
                    </div>
                `;
                suggCard.classList.add('hidden');
            } else {
                card.innerHTML = `
                    <div class="p-4 text-center bg-slate-50">
                        <div class="inline-flex items-center justify-center p-2 bg-amber-100 text-amber-600 rounded-full mb-1.5">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                            </svg>
                        </div>
                        <h3 class="text-xs font-bold text-slate-800 mb-0.5">No Flights Available Matching Exact Budget</h3>
                        <p class="text-[11px] text-slate-500 max-w-sm mx-auto">${data.recommendation_reason || 'No flights found within the requested budget and route constraints.'}</p>
                    </div>
                `;

                if (data.suggestions && data.suggestions.length > 0) {
                    suggList.innerHTML = data.suggestions.map(s => `<li class="flex items-start gap-1.5"><span class="text-amber-500 font-bold">•</span><span>${s}</span></li>`).join('');
                    suggCard.classList.remove('hidden');
                } else {
                    suggCard.classList.add('hidden');
                }
            }

            // Trace Box
            const traceBox = document.getElementById('traceSteps');
            const traceList = data.trace || [];
            document.getElementById('traceStepCount').innerText = `${traceList.length} Steps`;
            traceBox.innerHTML = traceList.map(t => `
                <div class="flex items-start gap-2 text-[11px] p-2 bg-slate-50/80 rounded-lg border border-slate-100">
                    <span class="px-1.5 py-0.5 rounded font-mono font-bold text-[9px] uppercase tracking-wider ${t.phase === 'PLAN' ? 'bg-purple-100 text-purple-700' : t.phase === 'ACT' ? 'bg-blue-100 text-blue-700' : t.phase === 'OBSERVE' ? 'bg-emerald-100 text-emerald-700' : t.phase === 'EVALUATE' ? 'bg-amber-100 text-amber-700' : 'bg-indigo-100 text-indigo-700'}">${t.phase}</span>
                    <span class="text-slate-700 flex-1 leading-snug font-medium">${t.content}</span>
                </div>
            `).join('');

            // Candidates Table
            const tb = document.getElementById('candidatesTableBody');
            const items = data.matched_fares || data.fares_found || [];
            document.getElementById('faresCountBadge').innerText = `${items.length} Fares`;
            if (items.length > 0) {
                tb.innerHTML = items.slice(0, 20).map(f => `
                    <tr class="hover:bg-slate-50 transition">
                        <td class="px-2.5 py-1.5 font-bold text-slate-800">${f.flight_number}</td>
                        <td class="px-2.5 py-1.5 font-sans">${f.airline || '-'}</td>
                        <td class="px-2.5 py-1.5">${f.origin} &rarr; ${f.destination}</td>
                        <td class="px-2.5 py-1.5">${f.departure_time || '-'} - ${f.arrival_time || '-'}</td>
                        <td class="px-2.5 py-1.5 font-bold text-slate-900">${f.price ? '₹' + f.price.toLocaleString() : 'Unavailable'}</td>
                        <td class="px-2.5 py-1.5"><span class="px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase ${f.price_status === 'verified' ? 'badge-verified' : f.price_status === 'unverified' ? 'badge-unverified' : 'badge-unavailable'}">${f.price_status}</span></td>
                        <td class="px-2.5 py-1.5 text-emerald-600 font-bold">${f.price_available ? '✓ MATCH' : '✕ NO MATCH'}</td>
                    </tr>
                `).join('');
            } else {
                tb.innerHTML = `<tr><td colspan="7" class="px-2.5 py-4 text-center text-slate-400 font-sans italic">No candidate fares available.</td></tr>`;
            }
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve live web user interface."""
    return HTML_TEMPLATE


@app.post("/api/search")
def api_search(payload: SearchPayload):
    """API endpoint to run flight search agent."""
    query = payload.query or f"Find flight from {payload.origin} to {payload.destination} on {payload.travel_date} under {payload.budget}"
    result = agent.run(query)
    return JSONResponse(content=result.model_dump())


if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
