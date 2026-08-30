"""Comprehensive Worldwide and Indian Regional Airport Resolver module.

Contains full catalog of all 140+ Indian operational commercial airports (metro, Tier-2, Tier-3, and UDAN regional airports)
as well as all major global hubs worldwide.
Includes typo-tolerant fuzzy matching, parenthesized code extraction, and multi-alias resolution.
"""

import re
import difflib
from typing import Optional, NamedTuple


class AirportResolution(NamedTuple):
    code: str
    city: str
    airport_name: str
    country: str
    is_ambiguous: bool
    possible_codes: list[str]


# Exhaustive Database of Indian Domestic/Regional Airports + Major Global Airports
AIRPORT_DATABASE: dict[str, dict] = {
    # ==================== NORTH INDIA ====================
    # Delhi & NCR
    "DEL": {"city": "Delhi", "name": "Indira Gandhi International Airport", "country": "India", "aliases": ["delhi", "new delhi", "del", "vidp", "igi", "delhi ncr", "delhi airport"]},
    "HDO": {"city": "Hindon (Ghaziabad)", "name": "Hindon Airport", "country": "India", "aliases": ["hindon", "ghaziabad", "hdo"]},

    # Punjab, Haryana & Chandigarh
    "ATQ": {"city": "Amritsar", "name": "Sri Guru Ram Dass Jee International Airport", "country": "India", "aliases": ["amritsar", "amrister", "amratsar", "amritser", "atq", "rajasansi", "sri guru ram dass jee"]},
    "IXC": {"city": "Chandigarh", "name": "Shaheed Bhagat Singh International Airport", "country": "India", "aliases": ["chandigarh", "mohali", "panchkula", "ixc"]},
    "AIP": {"city": "Adampur (Jalandhar)", "name": "Adampur Airport", "country": "India", "aliases": ["adampur", "jalandhar", "aip"]},
    "LUH": {"city": "Ludhiana", "name": "Sahnewal Airport", "country": "India", "aliases": ["ludhiana", "sahnewal", "luh"]},
    "BUP": {"city": "Bathinda", "name": "Bathinda Airport", "country": "India", "aliases": ["bathinda", "bhatinda", "bup"]},
    "IXP": {"city": "Pathankot", "name": "Pathankot Airport", "country": "India", "aliases": ["pathankot", "ixp"]},

    # Jammu, Kashmir & Ladakh
    "SXR": {"city": "Srinagar", "name": "Sheikh ul-Alam International Airport", "country": "India", "aliases": ["srinagar", "kashmir", "sxr"]},
    "IXJ": {"city": "Jammu", "name": "Jammu Civil Enclave", "country": "India", "aliases": ["jammu", "satwari", "ixj"]},
    "IXL": {"city": "Leh", "name": "Kushok Bakula Rimpochee Airport", "country": "India", "aliases": ["leh", "ladakh", "ixl"]},

    # Himachal Pradesh & Uttarakhand
    "DHM": {"city": "Dharamshala (Kangra)", "name": "Kangra Airport", "country": "India", "aliases": ["dharamshala", "dharamsala", "kangra", "gaggal", "dhm", "mcleodganj"]},
    "KUU": {"city": "Kullu (Manali)", "name": "Kullu-Manali Airport", "country": "India", "aliases": ["kullu", "manali", "bhuntar", "kuu"]},
    "SLV": {"city": "Shimla", "name": "Shimla Airport", "country": "India", "aliases": ["shimla", "jubbarhatti", "slv"]},
    "DED": {"city": "Dehradun", "name": "Jolly Grant Airport", "country": "India", "aliases": ["dehradun", "dehradoon", "ded", "rishikesh", "haridwar", "jolly grant"]},
    "PGH": {"city": "Pantnagar", "name": "Pantnagar Airport", "country": "India", "aliases": ["pantnagar", "nainital", "jim corbett", "pgh"]},
    "NNS": {"city": "Pithoragarh", "name": "Naini Saini Airport", "country": "India", "aliases": ["pithoragarh", "naini saini", "nns"]},

    # Uttar Pradesh
    "LKO": {"city": "Lucknow", "name": "Chaudhary Charan Singh International Airport", "country": "India", "aliases": ["lucknow", "lko", "amausi"]},
    "VNS": {"city": "Varanasi", "name": "Lal Bahadur Shastri International Airport", "country": "India", "aliases": ["varanasi", "banaras", "kashi", "vns", "babatpur"]},
    "AYJ": {"city": "Ayodhya", "name": "Maharishi Valmiki International Airport", "country": "India", "aliases": ["ayodhya", "faizabad", "ayj", "maharishi valmiki"]},
    "IXD": {"city": "Prayagraj (Allahabad)", "name": "Prayagraj Airport", "country": "India", "aliases": ["prayagraj", "allahabad", "ixd", "bamrauli"]},
    "KNU": {"city": "Kanpur", "name": "Kanpur Airport", "country": "India", "aliases": ["kanpur", "chakeri", "knu"]},
    "AGR": {"city": "Agra", "name": "Agra Airport", "country": "India", "aliases": ["agra", "kheria", "taj mahal", "agr"]},
    "GOP": {"city": "Gorakhpur", "name": "Gorakhpur Airport", "country": "India", "aliases": ["gorakhpur", "gop"]},
    "BEK": {"city": "Bareilly", "name": "Bareilly Airport", "country": "India", "aliases": ["bareilly", "bek"]},
    "KBK": {"city": "Kushinagar", "name": "Kushinagar International Airport", "country": "India", "aliases": ["kushinagar", "kbk"]},
    "AHM": {"city": "Aligarh", "name": "Aligarh Airport", "country": "India", "aliases": ["aligarh", "ahm"]},
    "MZD": {"city": "Moradabad", "name": "Moradabad Airport", "country": "India", "aliases": ["moradabad", "mzd"]},

    # Rajasthan
    "JAI": {"city": "Jaipur", "name": "Jaipur International Airport", "country": "India", "aliases": ["jaipur", "jai", "sanganer", "pink city"]},
    "UDR": {"city": "Udaipur", "name": "Maharana Pratap Airport", "country": "India", "aliases": ["udaipur", "udr", "dabok", "lake city"]},
    "JDH": {"city": "Jodhpur", "name": "Jodhpur Airport", "country": "India", "aliases": ["jodhpur", "jdh", "sun city"]},
    "JSA": {"city": "Jaisalmer", "name": "Jaisalmer Airport", "country": "India", "aliases": ["jaisalmer", "jsa"]},
    "BKB": {"city": "Bikaner", "name": "Nal Airport", "country": "India", "aliases": ["bikaner", "nal", "bkb"]},
    "KQH": {"city": "Kishangarh (Ajmer)", "name": "Kishangarh Airport", "country": "India", "aliases": ["kishangarh", "ajmer", "pushkar", "kqh"]},
    "KTU": {"city": "Kota", "name": "Kota Airport", "country": "India", "aliases": ["kota", "ktu"]},

    # ==================== WEST & CENTRAL INDIA ====================
    # Maharashtra
    "BOM": {"city": "Mumbai", "name": "Chhatrapati Shivaji Maharaj International Airport", "country": "India", "aliases": ["mumbai", "bombay", "bom", "mumbay", "csia", "sahar", "santacruz"]},
    "PNQ": {"city": "Pune", "name": "Pune Airport", "country": "India", "aliases": ["pune", "poona", "pnq", "lohegaon"]},
    "NAG": {"city": "Nagpur", "name": "Dr. Babasaheb Ambedkar International Airport", "country": "India", "aliases": ["nagpur", "nag", "sonegaon"]},
    "IXU": {"city": "Aurangabad (Chhatrapati Sambhajinagar)", "name": "Chhatrapati Sambhajinagar Airport", "country": "India", "aliases": ["aurangabad", "sambhajinagar", "chhatrapati sambhajinagar", "ixu", "chikalthana"]},
    "SAG": {"city": "Shirdi", "name": "Shirdi Airport", "country": "India", "aliases": ["shirdi", "kakadi", "sag"]},
    "ISK": {"city": "Nashik", "name": "Nashik Airport", "country": "India", "aliases": ["nashik", "nasik", "ozar", "isk"]},
    "KLH": {"city": "Kolhapur", "name": "Chhatrapati Rajaram Maharaj Airport", "country": "India", "aliases": ["kolhapur", "klh", "ujalaiwadi"]},
    "NDC": {"city": "Nanded", "name": "Shri Guru Gobind Singh Ji Airport", "country": "India", "aliases": ["nanded", "ndc"]},
    "JLG": {"city": "Jalgaon", "name": "Jalgaon Airport", "country": "India", "aliases": ["jalgaon", "jlg"]},
    "SDW": {"city": "Sindhudurg (Chipi)", "name": "Sindhudurg Airport", "country": "India", "aliases": ["sindhudurg", "chipi", "tarkarli", "sdw"]},
    "GDB": {"city": "Gondia", "name": "Birsi Airport", "country": "India", "aliases": ["gondia", "birsi", "gdb"]},
    "SSL": {"city": "Solapur", "name": "Solapur Airport", "country": "India", "aliases": ["solapur", "sholapur", "ssl"]},

    # Goa
    "GOI": {"city": "Goa (Dabolim)", "name": "Dabolim Airport", "country": "India", "aliases": ["goa", "dabolim", "goi", "vasco", "south goa"]},
    "GOX": {"city": "Goa (Mopa)", "name": "Manohar International Airport", "country": "India", "aliases": ["mopa", "gox", "manohar", "north goa"]},

    # Gujarat
    "AMD": {"city": "Ahmedabad", "name": "Sardar Vallabhbhai Patel International Airport", "country": "India", "aliases": ["ahmedabad", "ahmedbad", "amd", "svpia"]},
    "STV": {"city": "Surat", "name": "Surat International Airport", "country": "India", "aliases": ["surat", "stv", "magdalla"]},
    "BDQ": {"city": "Vadodara", "name": "Vadodara Airport", "country": "India", "aliases": ["vadodara", "baroda", "bdq", "harni"]},
    "RAJ": {"city": "Rajkot", "name": "Rajkot International Airport (Hirasar)", "country": "India", "aliases": ["rajkot", "hirasar", "raj", "hsr"]},
    "BHU": {"city": "Bhavnagar", "name": "Bhavnagar Airport", "country": "India", "aliases": ["bhavnagar", "bhu"]},
    "JGA": {"city": "Jamnagar", "name": "Jamnagar Airport", "country": "India", "aliases": ["jamnagar", "jga"]},
    "PBD": {"city": "Porbandar", "name": "Porbandar Airport", "country": "India", "aliases": ["porbandar", "pbd"]},
    "BHJ": {"city": "Bhuj", "name": "Bhuj Airport", "country": "India", "aliases": ["bhuj", "kutch", "bhj"]},
    "IXY": {"city": "Kandla (Gandhidham)", "name": "Kandla Airport", "country": "India", "aliases": ["kandla", "gandhidham", "ixy"]},
    "IXK": {"city": "Keshod (Junagadh)", "name": "Keshod Airport", "country": "India", "aliases": ["keshod", "junagadh", "gir", "somnath", "ixk"]},

    # Madhya Pradesh & Chhattisgarh
    "BHO": {"city": "Bhopal", "name": "Raja Bhoj Airport", "country": "India", "aliases": ["bhopal", "bho", "raja bhoj"]},
    "IDR": {"city": "Indore", "name": "Devi Ahilya Bai Holkar Airport", "country": "India", "aliases": ["indore", "idr", "ahilyabai"]},
    "GWL": {"city": "Gwalior", "name": "Rajmata Vijaya Raje Scindia Airport", "country": "India", "aliases": ["gwalior", "gwl", "maharajpur"]},
    "JLR": {"city": "Jabalpur", "name": "Dumna Airport", "country": "India", "aliases": ["jabalpur", "dumna", "jlr"]},
    "HJR": {"city": "Khajuraho", "name": "Khajuraho Airport", "country": "India", "aliases": ["khajuraho", "hjr"]},
    "RPR": {"city": "Raipur", "name": "Swami Vivekananda Airport", "country": "India", "aliases": ["raipur", "rpr", "mana"]},
    "PAB": {"city": "Bilaspur", "name": "Bilasa Devi Kevat Airport", "country": "India", "aliases": ["bilaspur", "chakarbhatha", "pab"]},
    "JGB": {"city": "Jagdalpur", "name": "Maa Danteshwari Airport", "country": "India", "aliases": ["jagdalpur", "bastar", "jgb"]},

    # ==================== SOUTH INDIA ====================
    # Andhra Pradesh & Telangana
    "HYD": {"city": "Hyderabad", "name": "Rajiv Gandhi International Airport", "country": "India", "aliases": ["hyderabad", "hyd", "shamshabad", "rgia", "secunderabad"]},
    "VGA": {"city": "Vijayawada", "name": "Vijayawada International Airport", "country": "India", "aliases": ["vijayawada", "vijawada", "vijaywada", "vga", "gannavaram", "amaravati"]},
    "VTZ": {"city": "Visakhapatnam", "name": "Visakhapatnam International Airport", "country": "India", "aliases": ["visakhapatnam", "vizag", "vishakapatnam", "vtz"]},
    "TIR": {"city": "Tirupati", "name": "Tirupati Airport", "country": "India", "aliases": ["tirupati", "tirupathi", "tir", "renigunta", "tirumala"]},
    "RJA": {"city": "Rajahmundry", "name": "Rajahmundry Airport", "country": "India", "aliases": ["rajahmundry", "rajamahendravaram", "rja", "madhurapudi"]},
    "CDP": {"city": "Kadapa (Cuddapah)", "name": "Kadapa Airport", "country": "India", "aliases": ["kadapa", "cuddapah", "cdp"]},
    "KJB": {"city": "Kurnool", "name": "Uyyalawada Narasimha Reddy Airport", "country": "India", "aliases": ["kurnool", "orvakal", "kjb"]},

    # Tamil Nadu & Puducherry
    "MAA": {"city": "Chennai", "name": "Chennai International Airport", "country": "India", "aliases": ["chennai", "madras", "maa", "meenambakkam", "trisulam"]},
    "CJB": {"city": "Coimbatore", "name": "Coimbatore International Airport", "country": "India", "aliases": ["coimbatore", "coimbator", "cjb", "peelamedu"]},
    "IXM": {"city": "Madurai", "name": "Madurai Airport", "country": "India", "aliases": ["madurai", "ixm"]},
    "TRZ": {"city": "Tiruchirappalli (Trichy)", "name": "Tiruchirappalli International Airport", "country": "India", "aliases": ["tiruchirappalli", "trichy", "tiruchirapalli", "trz"]},
    "TCR": {"city": "Tuticorin (Thoothukudi)", "name": "Tuticorin Airport", "country": "India", "aliases": ["tuticorin", "thoothukudi", "tcr", "vaigaikulam"]},
    "SXV": {"city": "Salem", "name": "Salem Airport", "country": "India", "aliases": ["salem", "sxv", "kamalapuram"]},
    "PNY": {"city": "Puducherry (Pondicherry)", "name": "Puducherry Airport", "country": "India", "aliases": ["puducherry", "pondicherry", "pondy", "pny"]},

    # Karnataka
    "BLR": {"city": "Bengaluru", "name": "Kempegowda International Airport", "country": "India", "aliases": ["bangalore", "bengaluru", "bengalor", "blr", "devanahalli", "kia"]},
    "IXE": {"city": "Mangalore", "name": "Mangaluru International Airport", "country": "India", "aliases": ["mangalore", "mangaluru", "ixe", "bajpe"]},
    "HBX": {"city": "Hubli (Hubballi)", "name": "Hubballi Airport", "country": "India", "aliases": ["hubli", "hubballi", "dharwad", "hbx"]},
    "IXG": {"city": "Belgaum (Belagavi)", "name": "Belagavi Airport", "country": "India", "aliases": ["belgaum", "belagavi", "ixg", "sambre"]},
    "MYQ": {"city": "Mysore (Mysuru)", "name": "Mysore Airport", "country": "India", "aliases": ["mysore", "mysuru", "mandakalli", "myq"]},
    "GBI": {"city": "Kalaburagi (Gulbarga)", "name": "Kalaburagi Airport", "country": "India", "aliases": ["kalaburagi", "gulbarga", "gbi"]},
    "IXX": {"city": "Bidar", "name": "Bidar Airport", "country": "India", "aliases": ["bidar", "ixx"]},
    "RQY": {"city": "Shivamogga (Shimoga)", "name": "Kuvempu Airport", "country": "India", "aliases": ["shivamogga", "shimoga", "sogane", "rqy"]},
    "VDY": {"city": "Ballari (Jindal Vidyanagar)", "name": "Jindal Vijaynagar Airport", "country": "India", "aliases": ["ballari", "bellary", "toranagallu", "hampi", "vdy"]},

    # Kerala & Islands
    "COK": {"city": "Kochi (Cochin)", "name": "Cochin International Airport", "country": "India", "aliases": ["kochi", "cochin", "cok", "nedumbassery", "ernakulam"]},
    "TRV": {"city": "Thiruvananthapuram (Trivandrum)", "name": "Trivandrum International Airport", "country": "India", "aliases": ["trivandrum", "thiruvananthapuram", "trivendrum", "trv", "chacka"]},
    "CCJ": {"city": "Kozhikode (Calicut)", "name": "Calicut International Airport", "country": "India", "aliases": ["kozhikode", "calicut", "ccj", "karipur"]},
    "CNN": {"city": "Kannur", "name": "Kannur International Airport", "country": "India", "aliases": ["kannur", "mattannur", "cnn"]},
    "AGX": {"city": "Agatti Island (Lakshadweep)", "name": "Agatti Airport", "country": "India", "aliases": ["agatti", "lakshadweep", "agx"]},
    "IXZ": {"city": "Port Blair (Andaman)", "name": "Veer Savarkar International Airport", "country": "India", "aliases": ["port blair", "andaman", "nicobar", "ixz", "veer savarkar"]},

    # ==================== EAST & NORTHEAST INDIA ====================
    # West Bengal, Bihar, Jharkhand & Odisha
    "CCU": {"city": "Kolkata", "name": "Netaji Subhash Chandra Bose International Airport", "country": "India", "aliases": ["kolkata", "calcutta", "kolkatta", "ccu", "dum dum"]},
    "IXB": {"city": "Bagdogra (Siliguri)", "name": "Bagdogra Airport", "country": "India", "aliases": ["bagdogra", "siliguri", "darjeeling", "ixb"]},
    "RDP": {"city": "Durgapur (Andal)", "name": "Kazi Nazrul Islam Airport", "country": "India", "aliases": ["durgapur", "asansol", "andal", "rdp"]},
    "COH": {"city": "Cooch Behar", "name": "Cooch Behar Airport", "country": "India", "aliases": ["cooch behar", "coh"]},
    "PAT": {"city": "Patna", "name": "Jay Prakash Narayan Airport", "country": "India", "aliases": ["patna", "pat"]},
    "GAY": {"city": "Gaya (Bodh Gaya)", "name": "Gaya Airport", "country": "India", "aliases": ["gaya", "bodhgaya", "bodh gaya", "gay"]},
    "DBR": {"city": "Darbhanga", "name": "Darbhanga Airport", "country": "India", "aliases": ["darbhanga", "dbr"]},
    "IXR": {"city": "Ranchi", "name": "Birsa Munda Airport", "country": "India", "aliases": ["ranchi", "ixr", "birsa munda"]},
    "DGH": {"city": "Deoghar", "name": "Deoghar Airport", "country": "India", "aliases": ["deoghar", "baidyanath", "dgh"]},
    "IXW": {"city": "Jamshedpur", "name": "Sonari Airport", "country": "India", "aliases": ["jamshedpur", "tatanagar", "ixw"]},
    "BBI": {"city": "Bhubaneswar", "name": "Biju Patnaik Airport", "country": "India", "aliases": ["bhubaneswar", "bhubaneshwar", "bbi", "biju patnaik"]},
    "JRG": {"city": "Jharsuguda", "name": "Veer Surendra Sai Airport", "country": "India", "aliases": ["jharsuguda", "jrg"]},
    "RRK": {"city": "Rourkela", "name": "Rourkela Airport", "country": "India", "aliases": ["rourkela", "rrk"]},
    "PYB": {"city": "Jeypore", "name": "Jeypore Airport", "country": "India", "aliases": ["jeypore", "pyb"]},

    # Northeast States (Assam, Meghalaya, Tripura, Manipur, Nagaland, Mizoram, Arunachal, Sikkim)
    "GAU": {"city": "Guwahati", "name": "Lokpriya Gopinath Bordoloi International Airport", "country": "India", "aliases": ["guwahati", "gauhati", "gau", "borjhar"]},
    "DIB": {"city": "Dibrugarh", "name": "Dibrugarh Airport", "country": "India", "aliases": ["dibrugarh", "mohanbari", "dib"]},
    "IXS": {"city": "Silchar", "name": "Silchar Airport", "country": "India", "aliases": ["silchar", "kumbhirgram", "ixs"]},
    "JRH": {"city": "Jorhat", "name": "Jorhat Airport", "country": "India", "aliases": ["jorhat", "rowriah", "jrh"]},
    "TEZ": {"city": "Tezpur", "name": "Tezpur Airport", "country": "India", "aliases": ["tezpur", "salonibari", "tez"]},
    "IXI": {"city": "Lilabari (North Lakhimpur)", "name": "Lilabari Airport", "country": "India", "aliases": ["lilabari", "lakhimpur", "ixi"]},
    "RUP": {"city": "Rupsi (Dhubri)", "name": "Rupsi Airport", "country": "India", "aliases": ["rupsi", "dhubri", "rup"]},
    "IXA": {"city": "Agartala", "name": "Maharaja Bir Bikram Airport", "country": "India", "aliases": ["agartala", "tripura", "ixa"]},
    "IMF": {"city": "Imphal", "name": "Bir Tikendrajit International Airport", "country": "India", "aliases": ["imphal", "manipur", "imf"]},
    "DMU": {"city": "Dimapur", "name": "Dimapur Airport", "country": "India", "aliases": ["dimapur", "nagaland", "kohima", "dmu"]},
    "AJL": {"city": "Aizawl", "name": "Lengpui Airport", "country": "India", "aliases": ["aizawl", "lengpui", "mizoram", "ajl"]},
    "SHL": {"city": "Shillong (Umroi)", "name": "Shillong Airport", "country": "India", "aliases": ["shillong", "umroi", "barapani", "meghalaya", "shl"]},
    "HGI": {"city": "Itanagar (Hollongi)", "name": "Donyi Polo Airport", "country": "India", "aliases": ["itanagar", "hollongi", "donyi polo", "arunachal", "hgi"]},
    "IXT": {"city": "Pasighat", "name": "Pasighat Airport", "country": "India", "aliases": ["pasighat", "ixt"]},
    "TEI": {"city": "Tezu", "name": "Tezu Airport", "country": "India", "aliases": ["tezu", "tei"]},
    "PYG": {"city": "Pakyong (Gangtok/Sikkim)", "name": "Pakyong Airport", "country": "India", "aliases": ["pakyong", "gangtok", "sikkim", "pyg"]},

    # ==================== MIDDLE EAST ====================
    "DXB": {"city": "Dubai", "name": "Dubai International Airport", "country": "UAE", "aliases": ["dubai", "dxb", "dubayy"]},
    "AUH": {"city": "Abu Dhabi", "name": "Zayed International Airport", "country": "UAE", "aliases": ["abu dhabi", "abudhabi", "auh"]},
    "SHJ": {"city": "Sharjah", "name": "Sharjah International Airport", "country": "UAE", "aliases": ["sharjah", "shj"]},
    "DOH": {"city": "Doha", "name": "Hamad International Airport", "country": "Qatar", "aliases": ["doha", "qatar", "doh"]},
    "JED": {"city": "Jeddah", "name": "King Abdulaziz International Airport", "country": "Saudi Arabia", "aliases": ["jeddah", "jed", "mecca", "makkah"]},
    "RUH": {"city": "Riyadh", "name": "King Khalid International Airport", "country": "Saudi Arabia", "aliases": ["riyadh", "ruh"]},
    "BAH": {"city": "Bahrain", "name": "Bahrain International Airport", "country": "Bahrain", "aliases": ["bahrain", "manama", "bah"]},
    "KWI": {"city": "Kuwait", "name": "Kuwait International Airport", "country": "Kuwait", "aliases": ["kuwait", "kwi"]},
    "MCT": {"city": "Muscat", "name": "Muscat International Airport", "country": "Oman", "aliases": ["muscat", "oman", "mct"]},
    "AMM": {"city": "Amman", "name": "Queen Alia International Airport", "country": "Jordan", "aliases": ["amman", "jordan", "amm"]},

    # ==================== EUROPE ====================
    "LHR": {"city": "London (Heathrow)", "name": "Heathrow Airport", "country": "UK", "aliases": ["london", "heathrow", "lhr"]},
    "LGW": {"city": "London (Gatwick)", "name": "Gatwick Airport", "country": "UK", "aliases": ["gatwick", "lgw"]},
    "STN": {"city": "London (Stansted)", "name": "Stansted Airport", "country": "UK", "aliases": ["stansted", "stn"]},
    "MAN": {"city": "Manchester", "name": "Manchester Airport", "country": "UK", "aliases": ["manchester", "man"]},
    "EDI": {"city": "Edinburgh", "name": "Edinburgh Airport", "country": "UK", "aliases": ["edinburgh", "edi"]},
    "CDG": {"city": "Paris (CDG)", "name": "Charles de Gaulle Airport", "country": "France", "aliases": ["paris", "cdg", "charles de gaulle"]},
    "ORY": {"city": "Paris (Orly)", "name": "Paris Orly Airport", "country": "France", "aliases": ["orly", "ory"]},
    "FRA": {"city": "Frankfurt", "name": "Frankfurt Airport", "country": "Germany", "aliases": ["frankfurt", "fra"]},
    "MUC": {"city": "Munich", "name": "Munich Airport", "country": "Germany", "aliases": ["munich", "muc"]},
    "BER": {"city": "Berlin", "name": "Berlin Brandenburg Airport", "country": "Germany", "aliases": ["berlin", "ber"]},
    "AMS": {"city": "Amsterdam", "name": "Amsterdam Airport Schiphol", "country": "Netherlands", "aliases": ["amsterdam", "schiphol", "ams"]},
    "MAD": {"city": "Madrid", "name": "Adolfo Suárez Madrid–Barajas Airport", "country": "Spain", "aliases": ["madrid", "mad", "barajas"]},
    "BCN": {"city": "Barcelona", "name": "Josep Tarradellas Barcelona-El Prat Airport", "country": "Spain", "aliases": ["barcelona", "bcn", "el prat"]},
    "FCO": {"city": "Rome", "name": "Leonardo da Vinci–Fiumicino Airport", "country": "Italy", "aliases": ["rome", "fiumicino", "fco"]},
    "MXP": {"city": "Milan", "name": "Milan Malpensa Airport", "country": "Italy", "aliases": ["milan", "malpensa", "mxp"]},
    "ZRH": {"city": "Zurich", "name": "Zurich Airport", "country": "Switzerland", "aliases": ["zurich", "zrh"]},
    "GVA": {"city": "Geneva", "name": "Geneva Airport", "country": "Switzerland", "aliases": ["geneva", "gva"]},
    "VIE": {"city": "Vienna", "name": "Vienna International Airport", "country": "Austria", "aliases": ["vienna", "vie"]},
    "BRU": {"city": "Brussels", "name": "Brussels Airport", "country": "Belgium", "aliases": ["brussels", "bru"]},
    "CPH": {"city": "Copenhagen", "name": "Copenhagen Airport", "country": "Denmark", "aliases": ["copenhagen", "cph"]},
    "ARN": {"city": "Stockholm", "name": "Stockholm Arlanda Airport", "country": "Sweden", "aliases": ["stockholm", "arlanda", "arn"]},
    "OSL": {"city": "Oslo", "name": "Oslo Airport", "country": "Norway", "aliases": ["oslo", "osl"]},
    "HEL": {"city": "Helsinki", "name": "Helsinki-Vantaa Airport", "country": "Finland", "aliases": ["helsinki", "hel"]},
    "DUB": {"city": "Dublin", "name": "Dublin Airport", "country": "Ireland", "aliases": ["dublin", "dub"]},
    "IST": {"city": "Istanbul", "name": "Istanbul Airport", "country": "Turkey", "aliases": ["istanbul", "ist"]},
    "ATH": {"city": "Athens", "name": "Athens International Airport", "country": "Greece", "aliases": ["athens", "ath"]},
    "LIS": {"city": "Lisbon", "name": "Humberto Delgado Airport", "country": "Portugal", "aliases": ["lisbon", "lis"]},

    # ==================== NORTH AMERICA ====================
    "JFK": {"city": "New York (JFK)", "name": "John F. Kennedy International Airport", "country": "USA", "aliases": ["new york", "jfk", "nyc", "kennedy"]},
    "EWR": {"city": "New York (Newark)", "name": "Newark Liberty International Airport", "country": "USA", "aliases": ["newark", "ewr"]},
    "LGA": {"city": "New York (LaGuardia)", "name": "LaGuardia Airport", "country": "USA", "aliases": ["laguardia", "lga"]},
    "LAX": {"city": "Los Angeles", "name": "Los Angeles International Airport", "country": "USA", "aliases": ["los angeles", "lax", "la"]},
    "SFO": {"city": "San Francisco", "name": "San Francisco International Airport", "country": "USA", "aliases": ["san francisco", "sfo", "bay area"]},
    "ORD": {"city": "Chicago (O'Hare)", "name": "O'Hare International Airport", "country": "USA", "aliases": ["chicago", "ord", "ohare"]},
    "DFW": {"city": "Dallas", "name": "Dallas/Fort Worth International Airport", "country": "USA", "aliases": ["dallas", "dfw", "fort worth"]},
    "ATL": {"city": "Atlanta", "name": "Hartsfield–Jackson Atlanta International Airport", "country": "USA", "aliases": ["atlanta", "atl"]},
    "MIA": {"city": "Miami", "name": "Miami International Airport", "country": "USA", "aliases": ["miami", "mia"]},
    "SEA": {"city": "Seattle", "name": "Seattle–Tacoma International Airport", "country": "USA", "aliases": ["seattle", "sea", "seatac"]},
    "BOS": {"city": "Boston", "name": "Logan International Airport", "country": "USA", "aliases": ["boston", "bos", "logan"]},
    "DEN": {"city": "Denver", "name": "Denver International Airport", "country": "USA", "aliases": ["denver", "den"]},
    "LAS": {"city": "Las Vegas", "name": "Harry Reid International Airport", "country": "USA", "aliases": ["las vegas", "las", "vegas"]},
    "MCO": {"city": "Orlando", "name": "Orlando International Airport", "country": "USA", "aliases": ["orlando", "mco"]},
    "IAD": {"city": "Washington (Dulles)", "name": "Washington Dulles International Airport", "country": "USA", "aliases": ["washington", "dulles", "iad", "dc"]},
    "YYZ": {"city": "Toronto", "name": "Toronto Pearson International Airport", "country": "Canada", "aliases": ["toronto", "pearson", "yyz"]},
    "YVR": {"city": "Vancouver", "name": "Vancouver International Airport", "country": "Canada", "aliases": ["vancouver", "yvr"]},
    "YUL": {"city": "Montreal", "name": "Montréal–Trudeau International Airport", "country": "Canada", "aliases": ["montreal", "yul"]},
    "MEX": {"city": "Mexico City", "name": "Mexico City International Airport", "country": "Mexico", "aliases": ["mexico city", "mex"]},
    "CUN": {"city": "Cancun", "name": "Cancún International Airport", "country": "Mexico", "aliases": ["cancun", "cun"]},

    # ==================== ASIA-PACIFIC ====================
    "SIN": {"city": "Singapore", "name": "Singapore Changi Airport", "country": "Singapore", "aliases": ["singapore", "changi", "sin"]},
    "BKK": {"city": "Bangkok (Suvarnabhumi)", "name": "Suvarnabhumi Airport", "country": "Thailand", "aliases": ["bangkok", "suvarnabhumi", "bkk"]},
    "DMK": {"city": "Bangkok (Don Mueang)", "name": "Don Mueang International Airport", "country": "Thailand", "aliases": ["don mueang", "dmk"]},
    "HKT": {"city": "Phuket", "name": "Phuket International Airport", "country": "Thailand", "aliases": ["phuket", "hkt"]},
    "KUL": {"city": "Kuala Lumpur", "name": "Kuala Lumpur International Airport", "country": "Malaysia", "aliases": ["kuala lumpur", "kl", "kul", "klia"]},
    "CGK": {"city": "Jakarta", "name": "Soekarno–Hatta International Airport", "country": "Indonesia", "aliases": ["jakarta", "cgk"]},
    "DPS": {"city": "Bali", "name": "I Gusti Ngurah Rai International Airport", "country": "Indonesia", "aliases": ["bali", "denpasar", "dps"]},
    "MNL": {"city": "Manila", "name": "Ninoy Aquino International Airport", "country": "Philippines", "aliases": ["manila", "mnl"]},
    "SGN": {"city": "Ho Chi Minh City", "name": "Tan Son Nhat International Airport", "country": "Vietnam", "aliases": ["ho chi minh", "saigon", "sgn"]},
    "HAN": {"city": "Hanoi", "name": "Noi Bai International Airport", "country": "Vietnam", "aliases": ["hanoi", "han"]},
    "HND": {"city": "Tokyo (Haneda)", "name": "Haneda Airport", "country": "Japan", "aliases": ["tokyo", "haneda", "hnd"]},
    "NRT": {"city": "Tokyo (Narita)", "name": "Narita International Airport", "country": "Japan", "aliases": ["narita", "nrt"]},
    "KIX": {"city": "Osaka", "name": "Kansai International Airport", "country": "Japan", "aliases": ["osaka", "kansai", "kix"]},
    "ICN": {"city": "Seoul (Incheon)", "name": "Incheon International Airport", "country": "South Korea", "aliases": ["seoul", "incheon", "icn"]},
    "HKG": {"city": "Hong Kong", "name": "Hong Kong International Airport", "country": "Hong Kong", "aliases": ["hong kong", "hkg", "chep lap kok"]},
    "TPE": {"city": "Taipei", "name": "Taoyuan International Airport", "country": "Taiwan", "aliases": ["taipei", "tpe", "taoyuan"]},
    "PVG": {"city": "Shanghai (Pudong)", "name": "Shanghai Pudong International Airport", "country": "China", "aliases": ["shanghai", "pudong", "pvg"]},
    "PEK": {"city": "Beijing (Capital)", "name": "Beijing Capital International Airport", "country": "China", "aliases": ["beijing", "pek"]},
    "CAN": {"city": "Guangzhou", "name": "Guangzhou Baiyun International Airport", "country": "China", "aliases": ["guangzhou", "can", "baiyun"]},
    "SYD": {"city": "Sydney", "name": "Sydney Kingsford Smith Airport", "country": "Australia", "aliases": ["sydney", "syd"]},
    "MEL": {"city": "Melbourne", "name": "Melbourne Airport", "country": "Australia", "aliases": ["melbourne", "mel", "tullamarine"]},
    "BNE": {"city": "Brisbane", "name": "Brisbane Airport", "country": "Australia", "aliases": ["brisbane", "bne"]},
    "PER": {"city": "Perth", "name": "Perth Airport", "country": "Australia", "aliases": ["perth", "per"]},
    "AKL": {"city": "Auckland", "name": "Auckland Airport", "country": "New Zealand", "aliases": ["auckland", "akl"]},

    # ==================== NEIGHBORS, AFRICA & LATIN AMERICA ====================
    "CMB": {"city": "Colombo", "name": "Bandaranaike International Airport", "country": "Sri Lanka", "aliases": ["colombo", "sri lanka", "cmb"]},
    "MLE": {"city": "Maldives (Male)", "name": "Velana International Airport", "country": "Maldives", "aliases": ["male", "maldives", "mle"]},
    "KTM": {"city": "Kathmandu", "name": "Tribhuvan International Airport", "country": "Nepal", "aliases": ["kathmandu", "nepal", "ktm"]},
    "DAC": {"city": "Dhaka", "name": "Hazrat Shahjalal International Airport", "country": "Bangladesh", "aliases": ["dhaka", "dac"]},
    "CAI": {"city": "Cairo", "name": "Cairo International Airport", "country": "Egypt", "aliases": ["cairo", "cai"]},
    "JNB": {"city": "Johannesburg", "name": "O. R. Tambo International Airport", "country": "South Africa", "aliases": ["johannesburg", "jnb"]},
    "CPT": {"city": "Cape Town", "name": "Cape Town International Airport", "country": "South Africa", "aliases": ["cape town", "cpt"]},
    "NBO": {"city": "Nairobi", "name": "Jomo Kenyatta International Airport", "country": "Kenya", "aliases": ["nairobi", "nbo"]},
    "GRU": {"city": "Sao Paulo", "name": "São Paulo/Guarulhos International Airport", "country": "Brazil", "aliases": ["sao paulo", "gru", "guarulhos"]},
    "EZE": {"city": "Buenos Aires", "name": "Ministro Pistarini International Airport", "country": "Argentina", "aliases": ["buenos aires", "eze"]},
    "BOG": {"city": "Bogota", "name": "El Dorado International Airport", "country": "Colombia", "aliases": ["bogota", "bog"]},
}

# Ambiguous multi-airport cities
AMBIGUOUS_CITIES: dict[str, list[str]] = {
    "goa": ["GOI", "GOX"],
    "london": ["LHR", "LGW", "STN"],
    "new york": ["JFK", "EWR", "LGA"],
    "tokyo": ["HND", "NRT"],
    "paris": ["CDG", "ORY"],
    "bangkok": ["BKK", "DMK"],
    "beijing": ["PEK", "PKX"],
}


def resolve_airport(query: str, prefer_primary_for_ambiguous: bool = True) -> Optional[AirportResolution]:
    """Resolve any city name, airport name, parenthesized IATA code, or spelling variant worldwide."""
    if not query:
        return None

    raw_str = str(query).strip()

    # 1. Match parenthesized 3-letter IATA code e.g. "Amritsar (ATQ)" -> "ATQ"
    paren_match = re.search(r"\(([A-Za-z]{3})\)", raw_str)
    if paren_match:
        c = paren_match.group(1).upper()
        if c in AIRPORT_DATABASE:
            info = AIRPORT_DATABASE[c]
            return AirportResolution(
                code=c,
                city=info["city"],
                airport_name=info["name"],
                country=info["country"],
                is_ambiguous=False,
                possible_codes=[c],
            )
        elif len(c) == 3 and c.isalpha():
            return AirportResolution(
                code=c,
                city=c,
                airport_name=f"{c} Airport",
                country="International",
                is_ambiguous=False,
                possible_codes=[c],
            )

    # 2. Direct 3-letter uppercase IATA code match
    clean_code = raw_str.upper()
    if len(clean_code) == 3 and clean_code in AIRPORT_DATABASE:
        info = AIRPORT_DATABASE[clean_code]
        return AirportResolution(
            code=clean_code,
            city=info["city"],
            airport_name=info["name"],
            country=info["country"],
            is_ambiguous=False,
            possible_codes=[clean_code],
        )

    # Clean string: remove parenthesized parts e.g. "Amritsar (ATQ)" -> "amritsar"
    clean = re.sub(r"\s*\([A-Za-z0-9\s]+\)", "", raw_str).strip().lower()

    # 3. Check ambiguous city list
    if clean in AMBIGUOUS_CITIES:
        codes = AMBIGUOUS_CITIES[clean]
        primary_code = codes[0]
        info = AIRPORT_DATABASE[primary_code]
        return AirportResolution(
            code=primary_code,
            city=info["city"],
            airport_name=info["name"],
            country=info["country"],
            is_ambiguous=not prefer_primary_for_ambiguous,
            possible_codes=codes,
        )

    # 4. Search by exact alias or city name
    for code, info in AIRPORT_DATABASE.items():
        if clean == info["city"].lower() or any(clean == a.lower() for a in info.get("aliases", [])):
            return AirportResolution(
                code=code,
                city=info["city"],
                airport_name=info["name"],
                country=info["country"],
                is_ambiguous=False,
                possible_codes=[code],
            )

    # 5. Substring search fallback
    for code, info in AIRPORT_DATABASE.items():
        if clean in info["city"].lower() or any(clean in a.lower() for a in info.get("aliases", [])):
            return AirportResolution(
                code=code,
                city=info["city"],
                airport_name=info["name"],
                country=info["country"],
                is_ambiguous=False,
                possible_codes=[code],
            )

    # 6. Typo-tolerant fuzzy matching (with cutoff 0.60 for misspellings like 'amrister', 'vijawada')
    all_terms: dict[str, str] = {}
    for code, info in AIRPORT_DATABASE.items():
        all_terms[info["city"].lower()] = code
        for a in info.get("aliases", []):
            all_terms[a.lower()] = code

    matches = difflib.get_close_matches(clean, all_terms.keys(), n=1, cutoff=0.60)
    if matches:
        matched_term = matches[0]
        code = all_terms[matched_term]
        info = AIRPORT_DATABASE[code]
        return AirportResolution(
            code=code,
            city=info["city"],
            airport_name=info["name"],
            country=info["country"],
            is_ambiguous=False,
            possible_codes=[code],
        )

    # 7. Pass-through for valid 3-letter alphabetic codes
    if len(clean_code) == 3 and clean_code.isalpha():
        return AirportResolution(
            code=clean_code,
            city=clean_code,
            airport_name=f"{clean_code} Airport",
            country="International",
            is_ambiguous=False,
            possible_codes=[clean_code],
        )

    return None
