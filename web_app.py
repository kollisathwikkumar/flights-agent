"""Web UI Application for T10 Flight Option Finder.

Modern light-mode design matching exact visual specifications:
- Structured Flight Form (From, To, Departure Date, Max Budget, Pax, Class, Time)
- Natural Language Prompt Tab
- Live Step-by-Step Execution Stepper with real-time animation
- Top Verified Flight Recommendation Card with direct airline booking button
- Smart Alternative Recommendations Card
- Candidate Fares & Matching Matrix Table
"""

from typing import Optional
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from agent import agent
from airport_resolver import resolve_airport

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
    <title>T10 Flight Option Finder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        code, pre { font-family: 'JetBrains Mono', monospace; }
        
        .badge-verified { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
        .badge-unverified { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
        .badge-unavailable { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
        .badge-passed { background: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 10px rgba(37, 99, 235, 0.3); }
            50% { box-shadow: 0 0 20px rgba(37, 99, 235, 0.6); }
        }
        .live-active-node {
            animation: pulse-glow 1.5s infinite;
            border-color: #2563eb !important;
            background-color: #eff6ff !important;
        }

        .step-transition {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
    </style>
</head>
<body class="bg-slate-50/60 min-h-screen text-slate-800 antialiased selection:bg-blue-600 selection:text-white">
    <div class="max-w-5xl mx-auto px-4 py-8">
        
        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center p-3 bg-blue-600 text-white rounded-2xl shadow-lg shadow-blue-500/20 mb-3">
                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
            </div>
            <h1 class="text-3xl font-black text-slate-900 tracking-tight">T10 Flight Option Finder</h1>
            <p class="text-slate-500 mt-1.5 text-xs sm:text-sm max-w-xl mx-auto font-medium">Real flight schedules via AviationStack, live fares via Ignav, deterministic matching & smart recommendations.</p>
        </div>

        <!-- Main Search Card (Exact Light-Theme Design) -->
        <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 mb-8">
            <!-- Tabs -->
            <div class="flex border-b border-slate-100 pb-3 mb-5 gap-8 text-xs font-bold uppercase tracking-wider">
                <button id="tabFormBtn" onclick="switchTab('form')" class="text-blue-600 border-b-2 border-blue-600 pb-2 -mb-3 transition">Structured Flight Form</button>
                <button id="tabPromptBtn" onclick="switchTab('prompt')" class="text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-2 -mb-3 transition">Natural Language Prompt</button>
            </div>

            <!-- TAB 1: Structured Form -->
            <div id="formTabContent" class="space-y-4">
                <!-- Top Row (4 Columns) -->
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                    <!-- From -->
                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">FROM (ORIGIN)</label>
                        <input type="text" id="formOrigin" list="airportList" 
                            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-sm bg-white font-medium shadow-sm transition"
                            placeholder="e.g. London (LHR), Delhi (DEL)" value="Chennai (MAA)">
                    </div>

                    <!-- To -->
                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">TO (DESTINATION)</label>
                        <input type="text" id="formDest" list="airportList" 
                            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-sm bg-white font-medium shadow-sm transition"
                            placeholder="e.g. New York (JFK), Dubai (DXB)" value="Delhi (DEL)">
                    </div>

                    <!-- Date -->
                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">DEPARTURE DATE</label>
                        <input type="date" id="formDate" 
                            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-sm bg-white font-medium shadow-sm transition"
                            value="2026-09-06">
                    </div>

                    <!-- Budget -->
                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">MAX BUDGET (₹ INR / USD)</label>
                        <input type="number" id="formBudget" 
                            class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-sm bg-white font-medium shadow-sm transition"
                            placeholder="25000" value="25000">
                    </div>
                </div>

                <!-- Secondary Row (3 Columns) -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">PASSENGERS</label>
                        <select id="formPax" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-800 text-sm bg-white font-medium shadow-sm">
                            <option value="1" selected>1 Passenger</option>
                            <option value="2">2 Passengers</option>
                            <option value="3">3 Passengers</option>
                            <option value="4">4+ Passengers</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">CABIN CLASS</label>
                        <select id="formCabin" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-800 text-sm bg-white font-medium shadow-sm">
                            <option value="economy" selected>Economy</option>
                            <option value="premium_economy">Premium Economy</option>
                            <option value="business">Business</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">DEPARTURE TIME</label>
                        <select id="formTime" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-800 text-sm bg-white font-medium shadow-sm">
                            <option value="" selected>Any Time</option>
                            <option value="morning">Morning (05:00 - 12:00)</option>
                            <option value="afternoon">Afternoon (12:00 - 17:00)</option>
                            <option value="evening">Evening (17:00 - 21:00)</option>
                            <option value="night">Night (21:00 - 05:00)</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- TAB 2: Natural Language Prompt -->
            <div id="promptTabContent" class="hidden space-y-2">
                <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Type flight request naturally</label>
                <textarea id="promptInput" rows="3" 
                    class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 text-sm bg-white font-medium shadow-sm"
                    placeholder="e.g. Find me a flight from Delhi to Dubai on September 24 under ₹20,000">Find me a flight from Delhi to Dubai on September 24 under ₹20,000</textarea>
            </div>

            <!-- Bottom Action Bar -->
            <div class="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                <!-- Quick Chips -->
                <div class="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span class="font-medium text-slate-400">Quick:</span>
                    <button onclick="setFormDirect('Delhi (DEL)', 'Dubai (DXB)', '2026-09-24', 20000)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition">Delhi &rarr; Dubai</button>
                    <button onclick="setFormDirect('London (LHR)', 'New York (JFK)', '2026-09-24', 50000)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition">London &rarr; New York</button>
                    <button onclick="setFormDirect('Chennai (MAA)', 'Delhi (DEL)', '2026-09-06', 25000)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition">Chennai &rarr; Delhi</button>
                    <button onclick="setFormDirect('Vijayawada (VGA)', 'Mumbai (BOM)', '2026-09-24', 8000)" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition">Vijayawada &rarr; Mumbai</button>
                </div>

                <button id="searchBtn" onclick="runSearch()" 
                    class="w-full sm:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm shadow-md shadow-blue-500/20 transition flex items-center justify-center gap-2">
                    <span id="btnText">Find Best Option</span>
                    <svg id="btnSpinner" class="hidden animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Live Step-by-Step Stepper Card (Animated) -->
        <div id="stepperContainer" class="hidden bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 mb-8">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                    <span class="flex h-2 w-2 relative">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
                    </span>
                    Agent Decision & Verification Flow
                </h3>
                <span id="stepperStatusBadge" class="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">EXECUTING</span>
            </div>
            <div id="stepperStepsList" class="space-y-2.5"></div>
        </div>

        <!-- Results Area -->
        <div id="resultsContainer" class="space-y-6">
            <!-- Best Option Card -->
            <div id="bestOptionCard" class="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
                <div class="p-8 text-center text-slate-400 text-sm">
                    Select origin, destination and date above to find the best verified flight.
                </div>
            </div>

            <!-- Smart Fallback Suggestions (When no flights meet constraints) -->
            <div id="suggestionsCard" class="hidden bg-amber-50 rounded-2xl border border-amber-200 p-6 shadow-sm">
                <div class="flex items-center gap-2 text-amber-900 font-bold text-sm mb-3">
                    <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Smart Alternative Recommendations
                </div>
                <ul id="suggestionsList" class="space-y-2 text-xs text-amber-800 font-medium"></ul>
            </div>

            <!-- Request Extraction Breakdown -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Request Extraction</h3>
                <div id="requestBreakdown" class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm font-medium"></div>
            </div>

            <!-- Agent Trace Log -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Agent Execution Trace (PLAN &rarr; ACT &rarr; OBSERVE &rarr; EVALUATE &rarr; DECIDE)</h3>
                <div id="traceSteps" class="space-y-2.5"></div>
            </div>

            <!-- Candidate Fares Table -->
            <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 overflow-x-auto">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Candidate Fares & Real Matching Status</h3>
                <table class="w-full text-left text-xs text-slate-600">
                    <thead class="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200 text-[11px]">
                        <tr>
                            <th class="px-4 py-3">Flight</th>
                            <th class="px-4 py-3">Airline</th>
                            <th class="px-4 py-3">Route</th>
                            <th class="px-4 py-3">Schedule</th>
                            <th class="px-4 py-3">Price</th>
                            <th class="px-4 py-3">Fare Status</th>
                            <th class="px-4 py-3">Match</th>
                        </tr>
                    </thead>
                    <tbody id="candidatesTableBody" class="divide-y divide-slate-100 font-mono text-[11px]">
                        <tr>
                            <td colspan="7" class="px-4 py-6 text-center text-slate-400 font-sans italic">No fare search executed yet.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Global & Indian Regional Airport Autocomplete Datalist -->
    <datalist id="airportList">
        <!-- North & Central India -->
        <option value="Amritsar (ATQ)">Amritsar (ATQ) - Sri Guru Ram Dass Jee Intl</option>
        <option value="Delhi (DEL)">Delhi (DEL) - Indira Gandhi Intl</option>
        <option value="Chandigarh (IXC)">Chandigarh (IXC) - Shaheed Bhagat Singh</option>
        <option value="Dehradun (DED)">Dehradun (DED) - Jolly Grant Airport</option>
        <option value="Ayodhya (AYJ)">Ayodhya (AYJ) - Maharishi Valmiki Intl</option>
        <option value="Lucknow (LKO)">Lucknow (LKO) - Chaudhary Charan Singh Intl</option>
        <option value="Varanasi (VNS)">Varanasi (VNS) - Lal Bahadur Shastri Intl</option>
        <option value="Jaipur (JAI)">Jaipur (JAI) - Jaipur Intl</option>
        <option value="Udaipur (UDR)">Udaipur (UDR) - Maharana Pratap Airport</option>
        <option value="Jodhpur (JDH)">Jodhpur (JDH) - Jodhpur Airport</option>
        <option value="Jaisalmer (JSA)">Jaisalmer (JSA) - Jaisalmer Airport</option>
        <option value="Bikaner (BKB)">Bikaner (BKB) - Nal Airport</option>
        <option value="Kishangarh (KQH)">Kishangarh (KQH) - Ajmer Airport</option>
        <option value="Dharamshala (DHM)">Dharamshala (DHM) - Kangra Airport</option>
        <option value="Kullu (KUU)">Kullu Manali (KUU) - Bhuntar Airport</option>
        <option value="Shimla (SLV)">Shimla (SLV) - Jubbarhatti Airport</option>
        <option value="Pantnagar (PGH)">Pantnagar (PGH) - Nainital Airport</option>
        <option value="Srinagar (SXR)">Srinagar (SXR) - Sheikh ul-Alam Intl</option>
        <option value="Jammu (IXJ)">Jammu (IXJ) - Jammu Civil Enclave</option>
        <option value="Leh (IXL)">Leh (IXL) - Kushok Bakula Rimpochee</option>
        <option value="Prayagraj (IXD)">Prayagraj (IXD) - Allahabad Airport</option>
        <option value="Kanpur (KNU)">Kanpur (KNU) - Chakeri Airport</option>
        <option value="Agra (AGR)">Agra (AGR) - Kheria Airport</option>
        <option value="Gorakhpur (GOP)">Gorakhpur (GOP) - Gorakhpur Airport</option>
        <option value="Bareilly (BEK)">Bareilly (BEK) - Bareilly Airport</option>
        <option value="Kushinagar (KBK)">Kushinagar (KBK) - Kushinagar Intl</option>
        <option value="Gwalior (GWL)">Gwalior (GWL) - Rajmata Vijaya Raje</option>
        <option value="Bhopal (BHO)">Bhopal (BHO) - Raja Bhoj Airport</option>
        <option value="Indore (IDR)">Indore (IDR) - Devi Ahilya Bai Holkar</option>
        <option value="Jabalpur (JLR)">Jabalpur (JLR) - Dumna Airport</option>
        <option value="Khajuraho (HJR)">Khajuraho (HJR) - Khajuraho Airport</option>
        <option value="Raipur (RPR)">Raipur (RPR) - Swami Vivekananda</option>
        <option value="Bilaspur (PAB)">Bilaspur (PAB) - Bilasa Devi Kevat</option>
        <option value="Jagdalpur (JGB)">Jagdalpur (JGB) - Maa Danteshwari</option>

        <!-- West India -->
        <option value="Mumbai (BOM)">Mumbai (BOM) - Chhatrapati Shivaji Intl</option>
        <option value="Pune (PNQ)">Pune (PNQ) - Pune Airport</option>
        <option value="Nagpur (NAG)">Nagpur (NAG) - Dr. Babasaheb Ambedkar Intl</option>
        <option value="Aurangabad (IXU)">Aurangabad (IXU) - Chhatrapati Sambhajinagar</option>
        <option value="Shirdi (SAG)">Shirdi (SAG) - Shirdi Airport</option>
        <option value="Nashik (ISK)">Nashik (ISK) - Ozar Airport</option>
        <option value="Kolhapur (KLH)">Kolhapur (KLH) - Chhatrapati Rajaram</option>
        <option value="Sindhudurg (SDW)">Sindhudurg (SDW) - Chipi Airport</option>
        <option value="Nanded (NDC)">Nanded (NDC) - Shri Guru Gobind Singh</option>
        <option value="Jalgaon (JLG)">Jalgaon (JLG) - Jalgaon Airport</option>
        <option value="Goa (GOI)">Goa Dabolim (GOI)</option>
        <option value="Goa (GOX)">Goa Mopa (GOX) - Manohar Intl</option>
        <option value="Ahmedabad (AMD)">Ahmedabad (AMD) - Sardar Vallabhbhai Patel</option>
        <option value="Surat (STV)">Surat (STV) - Surat Intl</option>
        <option value="Vadodara (BDQ)">Vadodara (BDQ) - Vadodara Airport</option>
        <option value="Rajkot (RAJ)">Rajkot (RAJ) - Hirasar Intl</option>
        <option value="Bhavnagar (BHU)">Bhavnagar (BHU) - Bhavnagar Airport</option>
        <option value="Jamnagar (JGA)">Jamnagar (JGA) - Jamnagar Airport</option>
        <option value="Porbandar (PBD)">Porbandar (PBD) - Porbandar Airport</option>
        <option value="Bhuj (BHJ)">Bhuj (BHJ) - Bhuj Airport</option>
        <option value="Kandla (IXY)">Kandla (IXY) - Gandhidham Airport</option>
        <option value="Keshod (IXK)">Keshod (IXK) - Junagadh / Gir</option>

        <!-- South India -->
        <option value="Bengaluru (BLR)">Bengaluru (BLR) - Kempegowda Intl</option>
        <option value="Chennai (MAA)">Chennai (MAA) - Chennai Intl</option>
        <option value="Hyderabad (HYD)">Hyderabad (HYD) - Rajiv Gandhi Intl</option>
        <option value="Vijayawada (VGA)">Vijayawada (VGA) - Vijayawada Intl</option>
        <option value="Visakhapatnam (VTZ)">Visakhapatnam (VTZ) - Vizag Airport</option>
        <option value="Tirupati (TIR)">Tirupati (TIR) - Tirupati Airport</option>
        <option value="Rajahmundry (RJA)">Rajahmundry (RJA) - Rajamahendravaram</option>
        <option value="Kadapa (CDP)">Kadapa (CDP) - Cuddapah Airport</option>
        <option value="Kurnool (KJB)">Kurnool (KJB) - Orvakal Airport</option>
        <option value="Kochi (COK)">Kochi (COK) - Cochin Intl</option>
        <option value="Thiruvananthapuram (TRV)">Thiruvananthapuram (TRV) - Trivandrum Intl</option>
        <option value="Kozhikode (CCJ)">Kozhikode (CCJ) - Calicut Intl</option>
        <option value="Kannur (CNN)">Kannur (CNN) - Kannur Intl</option>
        <option value="Mangalore (IXE)">Mangalore (IXE) - Mangaluru Intl</option>
        <option value="Hubli (HBX)">Hubli (HBX) - Hubballi Airport</option>
        <option value="Belgaum (IXG)">Belgaum (IXG) - Belagavi Airport</option>
        <option value="Mysore (MYQ)">Mysore (MYQ) - Mandakalli Airport</option>
        <option value="Kalaburagi (GBI)">Kalaburagi (GBI) - Gulbarga Airport</option>
        <option value="Shivamogga (RQY)">Shivamogga (RQY) - Kuvempu Airport</option>
        <option value="Bidar (IXX)">Bidar (IXX) - Bidar Airport</option>
        <option value="Ballari (VDY)">Ballari (VDY) - Jindal Vidyanagar</option>
        <option value="Coimbatore (CJB)">Coimbatore (CJB) - Coimbatore Intl</option>
        <option value="Madurai (IXM)">Madurai (IXM) - Madurai Airport</option>
        <option value="Tiruchirappalli (TRZ)">Tiruchirappalli (TRZ) - Trichy Intl</option>
        <option value="Tuticorin (TCR)">Tuticorin (TCR) - Thoothukudi Airport</option>
        <option value="Salem (SXV)">Salem (SXV) - Salem Airport</option>
        <option value="Puducherry (PNY)">Puducherry (PNY) - Pondicherry Airport</option>
        <option value="Agatti (AGX)">Agatti Island (AGX) - Lakshadweep</option>
        <option value="Port Blair (IXZ)">Port Blair (IXZ) - Veer Savarkar Intl</option>

        <!-- East & Northeast India -->
        <option value="Kolkata (CCU)">Kolkata (CCU) - Netaji Subhash Chandra Bose</option>
        <option value="Bagdogra (IXB)">Bagdogra (IXB) - Siliguri / Darjeeling</option>
        <option value="Durgapur (RDP)">Durgapur (RDP) - Kazi Nazrul Islam</option>
        <option value="Patna (PAT)">Patna (PAT) - Jay Prakash Narayan</option>
        <option value="Gaya (GAY)">Gaya (GAY) - Bodh Gaya Airport</option>
        <option value="Darbhanga (DBR)">Darbhanga (DBR) - Darbhanga Airport</option>
        <option value="Ranchi (IXR)">Ranchi (IXR) - Birsa Munda Airport</option>
        <option value="Deoghar (DGH)">Deoghar (DGH) - Deoghar Airport</option>
        <option value="Jamshedpur (IXW)">Jamshedpur (IXW) - Sonari Airport</option>
        <option value="Bhubaneswar (BBI)">Bhubaneswar (BBI) - Biju Patnaik Intl</option>
        <option value="Jharsuguda (JRG)">Jharsuguda (JRG) - Veer Surendra Sai</option>
        <option value="Rourkela (RRK)">Rourkela (RRK) - Rourkela Airport</option>
        <option value="Guwahati (GAU)">Guwahati (GAU) - Lokpriya Gopinath Bordoloi</option>
        <option value="Dibrugarh (DIB)">Dibrugarh (DIB) - Mohanbari Airport</option>
        <option value="Silchar (IXS)">Silchar (IXS) - Kumbhirgram Airport</option>
        <option value="Jorhat (JRH)">Jorhat (JRH) - Rowriah Airport</option>
        <option value="Agartala (IXA)">Agartala (IXA) - Maharaja Bir Bikram</option>
        <option value="Imphal (IMF)">Imphal (IMF) - Bir Tikendrajit Intl</option>
        <option value="Dimapur (DMU)">Dimapur (DMU) - Nagaland Airport</option>
        <option value="Aizawl (AJL)">Aizawl (AJL) - Lengpui Airport</option>
        <option value="Shillong (SHL)">Shillong (SHL) - Umroi Airport</option>
        <option value="Itanagar (HGI)">Itanagar (HGI) - Donyi Polo Airport</option>
        <option value="Pakyong (PYG)">Pakyong (PYG) - Sikkim Airport</option>

        <!-- Middle East -->
        <option value="Dubai (DXB)">Dubai (DXB) - Dubai International</option>
        <option value="Abu Dhabi (AUH)">Abu Dhabi (AUH) - Zayed Intl</option>
        <option value="Sharjah (SHJ)">Sharjah (SHJ) - Sharjah Intl</option>
        <option value="Doha (DOH)">Doha (DOH) - Hamad International</option>
        <option value="Jeddah (JED)">Jeddah (JED) - King Abdulaziz Intl</option>
        <option value="Riyadh (RUH)">Riyadh (RUH) - King Khalid Intl</option>
        <option value="Bahrain (BAH)">Bahrain (BAH) - Bahrain Intl</option>
        <option value="Kuwait (KWI)">Kuwait (KWI) - Kuwait Intl</option>
        <option value="Muscat (MCT)">Muscat (MCT) - Muscat Intl</option>

        <!-- Europe -->
        <option value="London (LHR)">London (LHR) - Heathrow Airport</option>
        <option value="London (LGW)">London (LGW) - Gatwick Airport</option>
        <option value="Manchester (MAN)">Manchester (MAN) - Manchester Airport</option>
        <option value="Edinburgh (EDI)">Edinburgh (EDI) - Edinburgh Airport</option>
        <option value="Paris (CDG)">Paris (CDG) - Charles de Gaulle</option>
        <option value="Paris (ORY)">Paris (ORY) - Paris Orly</option>
        <option value="Frankfurt (FRA)">Frankfurt (FRA) - Frankfurt Airport</option>
        <option value="Munich (MUC)">Munich (MUC) - Munich Airport</option>
        <option value="Berlin (BER)">Berlin (BER) - Berlin Brandenburg</option>
        <option value="Amsterdam (AMS)">Amsterdam (AMS) - Schiphol Airport</option>
        <option value="Madrid (MAD)">Madrid (MAD) - Adolfo Suárez Barajas</option>
        <option value="Barcelona (BCN)">Barcelona (BCN) - El Prat Airport</option>
        <option value="Rome (FCO)">Rome (FCO) - Fiumicino Airport</option>
        <option value="Milan (MXP)">Milan (MXP) - Malpensa Airport</option>
        <option value="Zurich (ZRH)">Zurich (ZRH) - Zurich Airport</option>
        <option value="Geneva (GVA)">Geneva (GVA) - Geneva Airport</option>
        <option value="Vienna (VIE)">Vienna (VIE) - Vienna Intl</option>
        <option value="Brussels (BRU)">Brussels (BRU) - Brussels Airport</option>
        <option value="Copenhagen (CPH)">Copenhagen (CPH) - Copenhagen Airport</option>
        <option value="Dublin (DUB)">Dublin (DUB) - Dublin Airport</option>
        <option value="Istanbul (IST)">Istanbul (IST) - Istanbul Airport</option>

        <!-- North America -->
        <option value="New York (JFK)">New York (JFK) - John F. Kennedy Intl</option>
        <option value="New York (EWR)">New York (EWR) - Newark Liberty Intl</option>
        <option value="Los Angeles (LAX)">Los Angeles (LAX) - Los Angeles Intl</option>
        <option value="San Francisco (SFO)">San Francisco (SFO) - San Francisco Intl</option>
        <option value="Chicago (ORD)">Chicago (ORD) - O'Hare International</option>
        <option value="Dallas (DFW)">Dallas (DFW) - Dallas/Fort Worth Intl</option>
        <option value="Atlanta (ATL)">Atlanta (ATL) - Hartsfield-Jackson Intl</option>
        <option value="Miami (MIA)">Miami (MIA) - Miami International</option>
        <option value="Seattle (SEA)">Seattle (SEA) - Seattle-Tacoma Intl</option>
        <option value="Boston (BOS)">Boston (BOS) - Logan International</option>
        <option value="Toronto (YYZ)">Toronto (YYZ) - Pearson International</option>
        <option value="Vancouver (YVR)">Vancouver (YVR) - Vancouver Intl</option>

        <!-- Asia-Pacific -->
        <option value="Singapore (SIN)">Singapore (SIN) - Changi Airport</option>
        <option value="Bangkok (BKK)">Bangkok (BKK) - Suvarnabhumi Airport</option>
        <option value="Phuket (HKT)">Phuket (HKT) - Phuket Intl</option>
        <option value="Kuala Lumpur (KUL)">Kuala Lumpur (KUL) - KLIA</option>
        <option value="Bali (DPS)">Bali (DPS) - Ngurah Rai Intl</option>
        <option value="Tokyo (HND)">Tokyo (HND) - Haneda Airport</option>
        <option value="Tokyo (NRT)">Tokyo (NRT) - Narita International</option>
        <option value="Seoul (ICN)">Seoul (ICN) - Incheon International</option>
        <option value="Hong Kong (HKG)">Hong Kong (HKG) - Hong Kong Intl</option>
        <option value="Sydney (SYD)">Sydney (SYD) - Kingsford Smith</option>
        <option value="Melbourne (MEL)">Melbourne (MEL) - Melbourne Airport</option>
        <option value="Auckland (AKL)">Auckland (AKL) - Auckland Airport</option>
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
                formBtn.className = "text-blue-600 border-b-2 border-blue-600 pb-2 -mb-3 transition";
                promptBtn.className = "text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-2 -mb-3 transition";
                formContent.classList.remove('hidden');
                promptContent.classList.add('hidden');
            } else {
                promptBtn.className = "text-blue-600 border-b-2 border-blue-600 pb-2 -mb-3 transition";
                formBtn.className = "text-slate-400 hover:text-slate-600 border-b-2 border-transparent pb-2 -mb-3 transition";
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

        function addStepperStep(phase, msg, state) {
            const list = document.getElementById('stepperStepsList');
            const item = document.createElement('div');
            item.className = "flex items-start gap-3 p-3 rounded-xl border border-slate-100 bg-slate-50/50 step-transition text-xs";
            
            const colorClass = phase === 'PLAN' ? 'bg-purple-100 text-purple-700' :
                               phase === 'ACT' ? 'bg-blue-100 text-blue-700' :
                               phase === 'OBSERVE' ? 'bg-emerald-100 text-emerald-700' :
                               phase === 'EVALUATE' ? 'bg-amber-100 text-amber-700' :
                               'bg-indigo-100 text-indigo-700';

            item.innerHTML = `
                <span class="px-2.5 py-0.5 rounded font-mono font-bold uppercase tracking-wider text-[10px] ${colorClass}">${phase}</span>
                <span class="text-slate-700 flex-1 leading-relaxed font-medium">${msg}</span>
                <span class="text-[10px] font-bold text-emerald-600 font-mono">✓</span>
            `;
            list.appendChild(item);
        }

        async function runSearch() {
            const btnText = document.getElementById('btnText');
            const spinner = document.getElementById('btnSpinner');
            const searchBtn = document.getElementById('searchBtn');
            const stepperContainer = document.getElementById('stepperContainer');
            const stepperList = document.getElementById('stepperStepsList');
            const stepperBadge = document.getElementById('stepperStatusBadge');

            btnText.innerText = "Finding Best Option...";
            spinner.classList.remove('hidden');
            searchBtn.disabled = true;
            stepperContainer.classList.remove('hidden');
            stepperList.innerHTML = '';
            stepperBadge.innerText = "EXECUTING";
            stepperBadge.className = "text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 animate-pulse";

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

            try {
                addStepperStep('PLAN', `Parsing request & resolving IATA airports (${payload.origin || 'Route'})...`);
                await sleep(300);

                addStepperStep('ACT', `Tool 1: search_flights() — checking AviationStack flight schedules...`);
                await sleep(300);

                addStepperStep('ACT', `Tool 2: compare_price() — querying Ignav live fares & segments...`);

                const resp = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();

                addStepperStep('OBSERVE', `Retrieved ${data.fares_found ? data.fares_found.length : 0} live fares from Ignav.`);
                await sleep(200);

                addStepperStep('EVALUATE', `Deterministic matching engine verified ${data.matched_fares ? data.matched_fares.length : 0} candidates.`);
                await sleep(200);

                addStepperStep('DECIDE', `Selected optimal flight: ${data.best_flight ? (data.best_flight.airline + ' ' + data.best_flight.flight_number + ' at ₹' + data.best_flight.price.toLocaleString()) : 'No match within budget'}`);

                stepperBadge.innerText = "COMPLETED";
                stepperBadge.className = "text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";

                renderResults(data);
            } catch (err) {
                alert('Error querying flight options: ' + err);
                stepperBadge.innerText = "ERROR";
                stepperBadge.className = "text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200";
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

            // Render Best Option Card (Exact Match from User's Screenshot)
            if (best && best.price) {
                card.innerHTML = `
                    <div class="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 text-white">
                        <div class="flex items-center justify-between">
                            <span class="text-xs uppercase tracking-widest font-semibold bg-white/20 px-3 py-1 rounded-full">✈️ TOP VERIFIED FLIGHT OPTION</span>
                            <span class="text-xs font-medium bg-green-500/30 border border-green-400 text-green-100 px-2.5 py-0.5 rounded-md">${best.price_status.toUpperCase()} FARE</span>
                        </div>
                        <div class="mt-4 flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
                            <div>
                                <h2 class="text-3xl font-extrabold tracking-tight">${best.airline || ''} ${best.flight_number}</h2>
                                <p class="text-blue-100 text-sm mt-0.5 font-medium">${req.origin_city || best.origin} (${best.origin}) &rarr; ${req.destination_city || best.destination} (${best.destination})</p>
                            </div>
                            <div class="sm:text-right">
                                <div class="text-3xl font-extrabold">₹${best.price.toLocaleString()} <span class="text-sm font-normal text-blue-200">${best.currency || 'INR'}</span></div>
                                <div class="text-xs text-blue-200 mt-0.5">${req.budget ? (best.price <= req.budget ? '✓ Within Budget (₹' + req.budget.toLocaleString() + ')' : 'Exceeds Budget') : 'No budget limit'}</div>
                            </div>
                        </div>
                    </div>
                    <div class="p-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs border-b border-slate-100 bg-slate-50/50">
                        <div><span class="text-slate-400 block font-medium">DATE</span><span class="font-semibold text-slate-800">${best.travel_date}</span></div>
                        <div><span class="text-slate-400 block font-medium">DEPARTURE</span><span class="font-semibold text-slate-800">${best.departure_time || 'N/A'}</span></div>
                        <div><span class="text-slate-400 block font-medium">ARRIVAL</span><span class="font-semibold text-slate-800">${best.arrival_time || 'N/A'}</span></div>
                        <div><span class="text-slate-400 block font-medium">WEB VERIFICATION</span><span class="font-semibold text-blue-700 uppercase">${best.web_verification_status || 'UNAVAILABLE'}</span></div>
                    </div>
                    <div class="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div class="text-xs text-slate-600">
                            <span class="font-semibold text-slate-800 block mb-0.5">Selection Rationale:</span>
                            ${data.recommendation_reason || 'Optimal verified flight within budget.'}
                        </div>
                        ${best.booking_url ? `<a href="${best.booking_url}" target="_blank" class="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs shadow transition text-center whitespace-nowrap">Book via ${best.booking_provider || 'Airline'} &rarr;</a>` : `<span class="text-xs text-slate-400">Booking link unavailable</span>`}
                    </div>
                `;
                suggCard.classList.add('hidden');
            } else {
                card.innerHTML = `
                    <div class="p-8 text-center bg-slate-50">
                        <div class="inline-flex items-center justify-center p-3 bg-amber-100 text-amber-600 rounded-full mb-3">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                            </svg>
                        </div>
                        <h3 class="text-base font-bold text-slate-800 mb-1">No Flights Available Matching Exact Criteria</h3>
                        <p class="text-xs text-slate-500 max-w-md mx-auto">${data.recommendation_reason || 'No flights found within the requested budget and route constraints.'}</p>
                    </div>
                `;

                if (data.suggestions && data.suggestions.length > 0) {
                    suggList.innerHTML = data.suggestions.map(s => `<li class="flex items-start gap-2"><span class="text-amber-500 font-bold">•</span><span>${s}</span></li>`).join('');
                    suggCard.classList.remove('hidden');
                } else {
                    suggCard.classList.add('hidden');
                }
            }

            // Breakdown
            const bd = document.getElementById('requestBreakdown');
            bd.innerHTML = `
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-100"><span class="text-xs text-slate-400 block font-medium">Origin</span><span class="font-bold text-slate-800">${req.origin_city || '-'} (${req.origin_code || '-'})</span></div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-100"><span class="text-xs text-slate-400 block font-medium">Destination</span><span class="font-bold text-slate-800">${req.destination_city || '-'} (${req.destination_code || '-'})</span></div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-100"><span class="text-xs text-slate-400 block font-medium">Travel Date</span><span class="font-bold text-slate-800">${req.travel_date || '-'}</span></div>
                <div class="p-3 bg-slate-50 rounded-xl border border-slate-100"><span class="text-xs text-slate-400 block font-medium">Budget</span><span class="font-bold text-slate-800">${req.budget ? '₹' + req.budget.toLocaleString() : 'None'}</span></div>
            `;

            // Trace
            const traceBox = document.getElementById('traceSteps');
            traceBox.innerHTML = (data.trace || []).map(t => `
                <div class="flex items-start gap-3 text-xs p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                    <span class="px-2 py-0.5 rounded font-mono font-bold uppercase tracking-wider text-[10px] ${t.phase === 'PLAN' ? 'bg-purple-100 text-purple-700' : t.phase === 'ACT' ? 'bg-blue-100 text-blue-700' : t.phase === 'OBSERVE' ? 'bg-emerald-100 text-emerald-700' : t.phase === 'EVALUATE' ? 'bg-amber-100 text-amber-700' : 'bg-indigo-100 text-indigo-700'}">${t.phase}</span>
                    <span class="text-slate-700 flex-1 leading-relaxed">${t.content}</span>
                </div>
            `).join('');

            // Candidates
            const tb = document.getElementById('candidatesTableBody');
            const items = data.matched_fares || data.fares_found || [];
            if (items.length > 0) {
                tb.innerHTML = items.slice(0, 15).map(f => `
                    <tr class="hover:bg-slate-50 transition">
                        <td class="px-4 py-3 font-semibold text-slate-800">${f.flight_number}</td>
                        <td class="px-4 py-3 font-sans">${f.airline || '-'}</td>
                        <td class="px-4 py-3">${f.origin} &rarr; ${f.destination}</td>
                        <td class="px-4 py-3">${f.departure_time || '-'} - ${f.arrival_time || '-'}</td>
                        <td class="px-4 py-3 font-semibold text-slate-900">${f.price ? '₹' + f.price.toLocaleString() : 'Unavailable'}</td>
                        <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${f.price_status === 'verified' ? 'badge-verified' : f.price_status === 'unverified' ? 'badge-unverified' : 'badge-unavailable'}">${f.price_status}</span></td>
                        <td class="px-4 py-3 text-emerald-600 font-semibold">${f.price_available ? '✓ MATCH' : '✕ NO MATCH'}</td>
                    </tr>
                `).join('');
            } else {
                tb.innerHTML = `<tr><td colspan="7" class="px-4 py-6 text-center text-slate-400 font-sans italic">No candidate fares available.</td></tr>`;
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
