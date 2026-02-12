#!/usr/bin/env python3
"""
Generate UD Language Maps HTML

This creates an interactive map with all UD languages showing:
- Map 1: Languages colored by family
- Map 2: Languages sized by corpus size

Usage:
    from generate_ud_maps import generate_ud_maps
    generate_ud_maps(metadata, langNames, langnameGroup, data_dir, html_dir)
"""

import os
import json
import pandas as pd

# ISO 639-1 (2-letter) to ISO 639-3 (3-letter) code mapping
ISO_639_1_TO_3 = {
    'ab': 'abk', 'af': 'afr', 'am': 'amh', 'ar': 'ara', 'az': 'aze',
    'be': 'bel', 'bg': 'bul', 'bm': 'bam', 'bn': 'ben', 'br': 'bre',
    'ca': 'cat', 'cs': 'ces', 'cy': 'cym', 'da': 'dan', 'de': 'deu',
    'el': 'ell', 'en': 'eng', 'es': 'spa', 'et': 'est', 'eu': 'eus',
    'fa': 'fas', 'fi': 'fin', 'fo': 'fao', 'fr': 'fra', 'ga': 'gle',
    'gd': 'gla', 'gl': 'glg', 'gv': 'glv', 'ha': 'hau', 'he': 'heb',
    'hi': 'hin', 'hr': 'hrv', 'hu': 'hun', 'hy': 'hye', 'id': 'ind',
    'is': 'isl', 'it': 'ita', 'ja': 'jpn', 'ka': 'kat', 'kk': 'kaz',
    'km': 'khm', 'kn': 'kan', 'ko': 'kor', 'ku': 'kur', 'la': 'lat',
    'ky': 'kir', 'lb': 'ltz', 'lt': 'lit', 'lv': 'lav', 'mk': 'mkd',
    'ml': 'mal', 'mn': 'mon', 'mr': 'mar', 'ms': 'msa', 'mt': 'mlt',
    'my': 'mya', 'nb': 'nob', 'nl': 'nld', 'nn': 'nno', 'no': 'nor',
    'pa': 'pan', 'pl': 'pol', 'pt': 'por', 'ro': 'ron', 'ru': 'rus',
    'sa': 'san', 'si': 'sin', 'sk': 'slk', 'sl': 'slv', 'sq': 'sqi',
    'sr': 'srp', 'sv': 'swe', 'sw': 'swa', 'ta': 'tam', 'te': 'tel',
    'th': 'tha', 'tl': 'tgl', 'tr': 'tur', 'uk': 'ukr', 'ur': 'urd',
    'uz': 'uzb', 'vi': 'vie', 'wo': 'wol', 'yo': 'yor', 'zh': 'zho',
}

# Languages to exclude from maps (by name)
EXCLUDED_LANGUAGES = {
    'French (Alternative)',
}

# Manual coordinates for languages not in WALS or with non-standard codes
# Format: 'code': (latitude, longitude, 'Name', 'Family')
# Keys use the UD language code (2-letter or 3-letter as used in UD)
MANUAL_COORDS = {
    # Ancient/Historical languages
    'akk': (33.1, 44.4, 'Akkadian', 'Afro-Asiatic'),  # Mesopotamia
    'ang': (51.06, -1.31, 'Old English', 'Indo-European'),  # Winchester (Anglo-Saxon capital)
    'cu': (42.7, 25.5, 'Old Church Slavonic', 'Indo-European'),  # Bulgaria
    'egy': (26.8, 30.8, 'Egyptian', 'Afro-Asiatic'),  # Egypt
    'fro': (48.9, 2.35, 'Old French', 'Indo-European'),  # Paris
    'frm': (48.9, 2.35, 'Middle French', 'Indo-European'),  # Paris
    'got': (48.0, 14.0, 'Gothic', 'Indo-European'),  # Central Europe
    'grc': (38.0, 23.7, 'Ancient Greek', 'Indo-European'),  # Athens
    'hbo': (31.8, 35.2, 'Ancient Hebrew', 'Afro-Asiatic'),  # Israel
    'hit': (39.0, 33.0, 'Hittite', 'Indo-European'),  # Anatolia
    'la': (41.9, 12.5, 'Latin', 'Indo-European'),  # Rome
    'non': (60.5, 8.5, 'Old Norse', 'Indo-European'),  # Norway
    'orv': (55.75, 37.62, 'Old Russian', 'Indo-European'),  # Moscow
    'ota': (41.0, 29.0, 'Ottoman Turkish', 'Turkic'),  # Istanbul
    'otk': (43.0, 77.0, 'Old Turkic', 'Turkic'),  # Central Asia
    'pro': (43.7, 4.0, 'Old Provençal', 'Indo-European'),  # Provence
    'sa': (27.2, 83.0, 'Sanskrit', 'Indo-European'),  # Varanasi
    'sga': (53.3, -6.3, 'Old Irish', 'Indo-European'),  # Dublin
    'xcl': (40.0, 44.5, 'Classical Armenian', 'Indo-European'),  # Armenia
    'xpg': (39.0, 30.0, 'Phrygian', 'Indo-European'),  # Anatolia
    'xum': (42.5, 12.5, 'Umbrian', 'Indo-European'),  # Umbria, Italy
    
    # Modern languages not in WALS
    'aln': (41.3, 19.8, 'Gheg Albanian', 'Indo-European'),  # Albania
    'aqz': (-12.5, -60.5, 'Akuntsu', 'Tupian'),  # Rondônia, Brazil
    'bxr': (51.8, 107.6, 'Buryat', 'Mongolic'),  # Buryatia, Russia
    'cpg': (38.5, 34.5, 'Cappadocian Greek', 'Indo-European'),  # Cappadocia
    'ctn': (27.3, 87.2, 'Chintang', 'Sino-Tibetan'),  # Nepal
    'eo': (53.1, 23.2, 'Esperanto', 'Constructed'),  # Białystok, Poland (Zamenhof's birthplace)
    'gn': (-23.4, -58.4, 'Guarani', 'Tupian'),  # Paraguay
    'gun': (-25.5, -54.5, 'Mbyá Guaraní', 'Tupian'),  # Paraguay/Brazil
    'ht': (18.9, -72.3, 'Haitian Creole', 'Indo-European'),  # Haiti
    'hr': (45.8, 15.98, 'Croatian', 'Indo-European'),  # Zagreb
    'kfm': (33.0, 51.5, 'Khunsari', 'Indo-European'),  # Iran
    'ltg': (56.5, 27.3, 'Latgalian', 'Indo-European'),  # Latvia
    'lzh': (35.0, 108.9, 'Classical Chinese', 'Sino-Tibetan'),  # Xi'an (offset north)
    'mpu': (-12.0, -63.0, 'Makuráp', 'Tupian'),  # Rondônia, Brazil
    'nhi': (19.0, -98.0, 'Western Nahuatl', 'Uto-Aztecan'),  # Mexico
    'nyq': (33.5, 52.0, 'Nayini', 'Indo-European'),  # Iran
    'olo': (62.0, 33.0, 'Livvi', 'Uralic'),  # Karelia
    'qaf': (34.0, 2.0, 'Maghrebi Arabic', 'Afro-Asiatic'),  # North Africa
    'qfn': (53.2, 5.8, 'Frisian-Dutch', 'Indo-European'),  # Friesland
    'qpm': (41.5, 25.5, 'Pomak', 'Indo-European'),  # Bulgaria/Greece
    'qte': (17.4, 78.5, 'Telugu-English', 'Mixed'),  # India
    'qti': (39.9, 32.9, 'Turkish-English', 'Mixed'),  # Turkey
    'qtd': (52.5, 13.4, 'Turkish-German', 'Mixed'),  # Germany
    'say': (10.0, 9.5, 'Zaar', 'Afro-Asiatic'),  # Nigeria
    'scn': (37.5, 14.0, 'Sicilian', 'Indo-European'),  # Sicily
    'sdh': (35.5, 46.0, 'Southern Kurdish', 'Indo-European'),  # Iran/Iraq
    'sjo': (43.9, 81.3, 'Xibe', 'Tungusic'),  # Xinjiang, China
    'sms': (69.0, 28.0, 'Skolt Sami', 'Uralic'),  # Finland/Russia
    'soj': (33.5, 51.9, 'Soi', 'Indo-European'),  # Isfahan Province, Iran (Central Iranian)
    'sr': (44.8, 20.5, 'Serbian', 'Indo-European'),  # Belgrade
    'xnr': (32.5, 76.0, 'Kangri', 'Indo-European'),  # Himachal Pradesh
    'yrl': (-3.0, -60.0, 'Nheengatu', 'Tupian'),  # Amazon, Brazil
    'zh': (39.9, 116.4, 'Chinese', 'Sino-Tibetan'),  # Beijing (Mandarin)
    # Relocated languages (better geographic placement)
    'ar': (24.7, 46.7, 'Arabic', 'Afro-Asiatic'),  # Riyadh, Saudi Arabia
    'bar': (48.14, 11.58, 'Bavarian', 'Indo-European'),  # Munich, Bavaria
    'gsw': (47.37, 8.54, 'Swiss German', 'Indo-European'),  # Zurich, Switzerland
    'ky': (42.9, 74.6, 'Kyrgyz', 'Turkic'),  # Bishkek, Kyrgyzstan
    'nl': (52.37, 4.9, 'Dutch', 'Indo-European'),  # Amsterdam, Netherlands
    'orv': (59.93, 30.34, 'Old East Slavic', 'Indo-European'),  # St. Petersburg (Novgorod area)
    'otk': (39.9, 32.9, 'Old Turkish', 'Turkic'),  # Ankara, Turkey
    'qtd': (48.78, 9.18, 'Turkish-German', 'Mixed'),  # Stuttgart, West Germany
    'qti': (51.5, -0.1, 'Turkish-English', 'Mixed'),  # London, Britain
    'ru': (55.75, 37.62, 'Russian', 'Indo-European'),  # Moscow
    # Offsets for overlapping languages
    'fro': (49.5, 2.35, 'Old French', 'Indo-European'),  # Paris (offset north from Middle French)
    'hbo': (32.3, 35.2, 'Ancient Hebrew', 'Afro-Asiatic'),  # Israel (offset north from Modern Hebrew)
}

# HTML template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Dependencies Language Maps</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #2c3e50; margin-bottom: 10px; font-size: 2em; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 1.1em; }
        .map-section { background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 30px; overflow: hidden; }
        .map-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 25px; }
        .map-header h2 { margin: 0; font-size: 1.4em; }
        .map-header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 0.95em; }
        .map-container { height: 500px; width: 100%; }
        .info-box { background: #f8f9fa; border-top: 1px solid #e0e0e0; padding: 20px 25px; min-height: 120px; }
        .info-box h3 { color: #2c3e50; margin-bottom: 10px; font-size: 1.2em; }
        .info-box .placeholder { color: #999; font-style: italic; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 10px; }
        .stat-item { background: white; padding: 12px 15px; border-radius: 8px; border-left: 4px solid #667eea; }
        .stat-item .label { font-size: 0.85em; color: #666; margin-bottom: 3px; }
        .stat-item .value { font-size: 1.3em; font-weight: 600; color: #2c3e50; }
        .legend { background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 20px 25px; margin-bottom: 30px; }
        .legend h3 { margin-bottom: 15px; color: #2c3e50; }
        .legend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .legend-item { display: flex; align-items: center; gap: 8px; font-size: 0.9em; }
        .legend-dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(0,0,0,0.3); flex-shrink: 0; }
        .summary-stats { background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 20px 25px; margin-bottom: 30px; }
        .summary-stats h3 { margin-bottom: 15px; color: #2c3e50; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .summary-item { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .summary-item .number { font-size: 2em; font-weight: 700; color: #667eea; }
        .summary-item .desc { color: #666; font-size: 0.9em; margin-top: 5px; }
        footer { text-align: center; padding: 20px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Universal Dependencies Language Maps</h1>
        <p class="subtitle">Interactive visualization of UD 2.17 treebank coverage across world languages</p>
        <div class="summary-stats"><h3>📊 Global Statistics</h3><div class="summary-grid" id="globalStats"></div></div>
        <div class="legend"><h3>🎨 Language Family Colors</h3><div class="legend-grid" id="legendGrid"></div></div>
        <div class="map-section">
            <div class="map-header"><h2>📍 Map 1: Languages by Family</h2><p>Each dot represents a UD language, colored by language family. Hover for details.</p></div>
            <div id="map1" class="map-container"></div>
            <div class="info-box" id="info1"><h3>Language Information</h3><p class="placeholder">Hover over a language dot to see detailed statistics</p></div>
        </div>
        <div class="map-section">
            <div class="map-header"><h2>📏 Map 2: Languages by Corpus Size</h2><p>Dot size represents relative corpus size (number of tokens). Hover for details.</p></div>
            <div id="map2" class="map-container"></div>
            <div class="info-box" id="info2"><h3>Language Information</h3><p class="placeholder">Hover over a language dot to see detailed statistics</p></div>
        </div>
        <footer>Data from Universal Dependencies v2.17 • Geographic coordinates from WALS</footer>
    </div>
    <script>
    const languageData = LANGUAGE_DATA_PLACEHOLDER;
    const familyColors = {
        'Indo-European': '#4169E1', 'Sino-Austronesian': '#2E8B57', 'Afroasiatic': '#FF8C00',
        'Uralic': '#8B4513', 'Turkic': '#DC143C', 'Niger-Congo': '#228B22', 'Caucasian': '#FF69B4',
        'Dravidian': '#C71585', 'South-American': '#5F9EA0', 'Austronesian': '#32CD32',
        'Mongolic': '#9932CC', 'Sino-Tibetan': '#006400', 'Afro-Asiatic': '#FF8C00',
        'Trans-New Guinea': '#8B0000', 'Tupian': '#20B2AA', 'Constructed': '#808080',
        'Uto-Aztecan': '#DAA520', 'Tungusic': '#4B0082', 'Mixed': '#778899',
        'Other': '#696969', 'Unknown': '#A9A9A9'
    };
    function getColor(lang) {
        if (lang.ud_group && familyColors[lang.ud_group]) return familyColors[lang.ud_group];
        if (lang.wals_family && familyColors[lang.wals_family]) return familyColors[lang.wals_family];
        return familyColors['Other'];
    }
    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString();
    }
    function getRadius(tokens, maxTokens) {
        const minRadius = 2, maxRadius = 15;
        if (tokens <= 0) return minRadius;
        return minRadius + (maxRadius - minRadius) * (Math.log10(tokens + 1) / Math.log10(maxTokens + 1));
    }
    function createInfoHTML(lang) {
        const avgTreebankSentences = lang.treebanks > 0 ? Math.round(lang.sentences / lang.treebanks) : 0;
        const avgTreebankTokens = lang.treebanks > 0 ? Math.round(lang.tokens / lang.treebanks) : 0;
        return `<h3 style="color: ${getColor(lang)}; margin-bottom: 15px;">${lang.name} <span style="font-weight: normal; color: #666;">(${lang.code})</span></h3>
            <div class="stats-grid">
                <div class="stat-item"><div class="label">Language Family</div><div class="value">${lang.ud_group || lang.wals_family || 'Unknown'}</div></div>
                <div class="stat-item"><div class="label">Treebanks</div><div class="value">${lang.treebanks}</div></div>
                <div class="stat-item"><div class="label">Total Sentences</div><div class="value">${formatNumber(lang.sentences)}</div></div>
                <div class="stat-item"><div class="label">Total Tokens</div><div class="value">${formatNumber(lang.tokens)}</div></div>
                <div class="stat-item"><div class="label">Avg Sentence Length</div><div class="value">${lang.avg_sent_len} tokens</div></div>
                <div class="stat-item"><div class="label">Avg Treebank Size</div><div class="value">${formatNumber(avgTreebankSentences)} sent / ${formatNumber(avgTreebankTokens)} tok</div></div>
            </div>`;
    }
    function initMaps() {
        const totalLanguages = languageData.length;
        const totalTreebanks = languageData.reduce((sum, l) => sum + l.treebanks, 0);
        const totalSentences = languageData.reduce((sum, l) => sum + l.sentences, 0);
        const totalTokens = languageData.reduce((sum, l) => sum + l.tokens, 0);
        const maxTokens = Math.max(...languageData.map(l => l.tokens));
        document.getElementById('globalStats').innerHTML = `
            <div class="summary-item"><div class="number">${totalLanguages}</div><div class="desc">Languages on map</div></div>
            <div class="summary-item"><div class="number">${totalTreebanks}</div><div class="desc">Total Treebanks</div></div>
            <div class="summary-item"><div class="number">${formatNumber(totalSentences)}</div><div class="desc">Total Sentences</div></div>
            <div class="summary-item"><div class="number">${formatNumber(totalTokens)}</div><div class="desc">Total Tokens</div></div>`;
        const families = new Set();
        languageData.forEach(l => { if (l.ud_group) families.add(l.ud_group); else if (l.wals_family) families.add(l.wals_family); });
        document.getElementById('legendGrid').innerHTML = Array.from(families).sort().map(family => 
            `<div class="legend-item"><div class="legend-dot" style="background: ${familyColors[family] || familyColors['Other']}"></div><span>${family}</span></div>`
        ).join('');
        const map1 = L.map('map1', {attributionControl: false}).setView([30, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {}).addTo(map1);
        languageData.forEach(lang => {
            const marker = L.circleMarker([lang.lat, lang.lon], {radius: 7, fillColor: getColor(lang), color: '#333', weight: 1, opacity: 1, fillOpacity: 0.8}).addTo(map1);
            marker.bindTooltip(lang.name, {permanent: false, direction: 'top'});
            marker.on('mouseover', function() { document.getElementById('info1').innerHTML = createInfoHTML(lang); this.setStyle({weight: 3, radius: 10}); });
            marker.on('mouseout', function() { this.setStyle({weight: 1, radius: 7}); });
        });
        const map2 = L.map('map2', {attributionControl: false}).setView([30, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {}).addTo(map2);
        setTimeout(() => { map1.invalidateSize(); map2.invalidateSize(); }, 200);
        [...languageData].sort((a, b) => b.tokens - a.tokens).forEach(lang => {
            const radius = getRadius(lang.tokens, maxTokens);
            const marker = L.circleMarker([lang.lat, lang.lon], {radius: radius, fillColor: getColor(lang), color: '#333', weight: 1, opacity: 1, fillOpacity: 0.7}).addTo(map2);
            marker.bindTooltip(`${lang.name} (${formatNumber(lang.tokens)} tokens)`, {permanent: false, direction: 'top'});
            marker.on('mouseover', function() { document.getElementById('info2').innerHTML = createInfoHTML(lang); this.setStyle({weight: 3}); });
            marker.on('mouseout', function() { this.setStyle({weight: 1}); });
        });
    }
    document.addEventListener('DOMContentLoaded', initMaps);
    </script>

<!-- Integration Documentation -->
<div style="max-width: 1200px; margin: 60px auto 30px; padding: 0 20px;">
    <details style="background: #f8f9fa; border-radius: 8px; padding: 20px; border: 1px solid #dee2e6;">
        <summary style="font-size: 18px; font-weight: bold; cursor: pointer; color: #333;">🔧 Integration Guide: Embedding This Map</summary>
        <div style="margin-top: 20px; line-height: 1.6;">
            <h4 style="color: #495057;">Available JavaScript Functions</h4>
            <ul style="color: #666;">
                <li><code>initMaps()</code> - Initializes both map instances. Called automatically on DOMContentLoaded.</li>
                <li><code>getColor(lang)</code> - Returns the color for a language based on its family.</li>
                <li><code>getRadius(tokens, maxTokens)</code> - Calculates marker radius for corpus size map (logarithmic scale, min: 2px, max: 15px).</li>
                <li><code>createInfoHTML(lang)</code> - Generates the HTML for the info panel when hovering over a marker.</li>
                <li><code>formatNumber(num)</code> - Formats large numbers (e.g., 1.5M, 250K).</li>
            </ul>
            
            <h4 style="color: #495057; margin-top: 20px;">Event Handlers</h4>
            <ul style="color: #666;">
                <li><strong>mouseover</strong>: Updates the info panel (<code>#info1</code> or <code>#info2</code>) with language details and enlarges the marker.</li>
                <li><strong>mouseout</strong>: Resets marker size to default.</li>
                <li><strong>tooltip</strong>: Displays language name on hover via Leaflet's <code>bindTooltip()</code>.</li>
            </ul>
            
            <h4 style="color: #495057; margin-top: 20px;">Data Structure</h4>
            <p style="color: #666;">The <code>languageData</code> array contains objects with:</p>
            <pre style="background: #e9ecef; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 13px;">{
  code: "en",           // UD language code
  name: "English",      // Language name
  lat: 52.0,            // Latitude
  lon: -1.17,           // Longitude
  treebanks: 5,         // Number of treebanks
  sentences: 123456,    // Total sentences
  tokens: 2345678,      // Total tokens
  avg_sent_len: 19.0,   // Average sentence length
  ud_group: "Indo-European",  // UD language family
  wals_family: "Indo-European" // WALS family (fallback)
}</pre>
            
            <h4 style="color: #495057; margin-top: 20px;">Embedding in Another Page</h4>
            <ol style="color: #666;">
                <li>Include Leaflet CSS and JS: <code>&lt;link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"&gt;</code></li>
                <li>Create map container: <code>&lt;div id="myMap" style="height: 500px;"&gt;&lt;/div&gt;</code></li>
                <li>Copy <code>languageData</code>, <code>familyColors</code>, and desired functions from this file.</li>
                <li>Initialize with: <code>const map = L.map('myMap').setView([30, 0], 2);</code></li>
                <li>Call <code>map.invalidateSize()</code> after the container becomes visible (e.g., in tabs).</li>
            </ol>
            
            <h4 style="color: #495057; margin-top: 20px;">JSON Data File</h4>
            <p style="color: #666;">Language statistics are also saved to <code>html_analyses/ud_language_stats.json</code> for programmatic access.</p>
        </div>
    </details>
</div>

</body>
</html>'''


def find_wals_match(lang_code, lang_name, wals_df):
    """Find WALS match for a language."""
    # MANUAL_COORDS takes priority (for relocated/corrected languages)
    if lang_code in MANUAL_COORDS:
        lat, lon, name, family = MANUAL_COORDS[lang_code]
        return {'lat': lat, 'lon': lon, 'family': family}
    
    match = None
    
    # Try direct ISO3
    if 'ISO639P3code' in wals_df.columns:
        matches = wals_df[wals_df['ISO639P3code'] == lang_code]
        if len(matches) > 0:
            match = matches.iloc[0]
        
        # Try ISO1->ISO3
        if match is None and len(lang_code) == 2:
            iso3 = ISO_639_1_TO_3.get(lang_code)
            if iso3:
                matches = wals_df[wals_df['ISO639P3code'] == iso3]
                if len(matches) > 0:
                    match = matches.iloc[0]
    
    # Try exact name match
    if match is None and 'Name' in wals_df.columns:
        clean_name = lang_name.split('(')[0].strip().lower()
        for _, row in wals_df.iterrows():
            wals_name = str(row['Name']).split('(')[0].strip().lower()
            if clean_name == wals_name:
                match = row
                break
    
    # Check if match has valid coordinates
    if match is not None and pd.notna(match.get('Latitude')) and pd.notna(match.get('Longitude')):
        return {
            'lat': float(match['Latitude']),
            'lon': float(match['Longitude']),
            'family': str(match['Family']) if pd.notna(match.get('Family')) else 'Unknown'
        }
    return None


def count_stats_for_lang(lang_code, metadata):
    """Count sentences and tokens for a language from all its CoNLL files."""
    files = metadata['langConllFiles'].get(lang_code, [])
    total_sentences = 0
    total_tokens = 0
    treebank_names = set()
    
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        # Extract treebank name
        parts = filepath.split('/')
        for p in parts:
            if p.startswith('UD_'):
                treebank_names.add(p)
                break
        
        sentences = 0
        tokens = 0
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        sentences += 1
                    elif not line.startswith('#'):
                        parts = line.split('\t')
                        if parts and '-' not in parts[0] and '.' not in parts[0]:
                            tokens += 1
        except:
            continue
        total_sentences += sentences
        total_tokens += tokens
    
    return {
        'treebanks': len(treebank_names),
        'files': len(files),
        'sentences': total_sentences,
        'tokens': total_tokens,
        'avg_sent_len': round(total_tokens / total_sentences, 1) if total_sentences > 0 else 0
    }


def collect_language_stats(metadata, langNames, langnameGroup, data_dir):
    """
    Collect language statistics for UD maps.
    
    Parameters:
    -----------
    metadata : dict
        Metadata dict with 'langConllFiles' key mapping lang codes to file paths
    langNames : dict
        Mapping of language codes to language names
    langnameGroup : dict
        Mapping of language names to language family groups
    data_dir : str
        Path to data directory (for WALS data and stats output)
        
    Returns:
    --------
    list of language data dictionaries
    """
    # Load WALS data
    wals_path = os.path.join(data_dir, 'wals', 'languages.csv')
    wals_df = pd.read_csv(wals_path)
    
    # Collect all language data
    print("Collecting language statistics...")
    languages_data = []
    unmatched = []
    
    for lang_code in sorted(langNames.keys()):
        lang_name = langNames[lang_code]
        
        # Skip excluded languages
        if lang_name in EXCLUDED_LANGUAGES:
            continue
        
        geo = find_wals_match(lang_code, lang_name, wals_df)
        if geo is None:
            unmatched.append((lang_code, lang_name))
            continue
        
        stats = count_stats_for_lang(lang_code, metadata)
        group = langnameGroup.get(lang_name, 'Other') or 'Other'
        
        languages_data.append({
            'code': lang_code,
            'name': lang_name,
            'lat': geo['lat'],
            'lon': geo['lon'],
            'wals_family': geo['family'],
            'ud_group': group,
            'treebanks': stats['treebanks'],
            'files': stats['files'],
            'sentences': stats['sentences'],
            'tokens': stats['tokens'],
            'avg_sent_len': stats['avg_sent_len']
        })
    
    print(f"Collected data for {len(languages_data)} languages")
    if unmatched:
        print(f"Warning: {len(unmatched)} languages without coordinates:")
        for code, name in unmatched:
            print(f"  '{code}': (...),  # {name}")
    
    # Save stats JSON
    stats_path = os.path.join(data_dir, 'ud_language_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(languages_data, f, indent=2)
    print(f"Saved stats to {stats_path}")
    
    return languages_data


def generate_ud_maps_html(languages_data, html_dir):
    """
    Generate UD Language Maps HTML file from language data.
    
    Parameters:
    -----------
    languages_data : list
        List of language data dictionaries (from collect_language_stats)
    html_dir : str
        Path to HTML output directory
        
    Returns:
    --------
    dict with 'languages', 'treebanks', 'sentences', 'tokens' counts
    """
    # Generate HTML
    html_content = HTML_TEMPLATE.replace('LANGUAGE_DATA_PLACEHOLDER', json.dumps(languages_data, indent=2))
    ud_maps_path = os.path.join(html_dir, 'UD_maps.html')
    with open(ud_maps_path, 'w') as f:
        f.write(html_content)
    
    total_tokens = sum(l['tokens'] for l in languages_data)
    total_sentences = sum(l['sentences'] for l in languages_data)
    total_treebanks = sum(l['treebanks'] for l in languages_data)
    
    print(f"✓ Generated {ud_maps_path}")
    print(f"  {len(languages_data)} languages, {total_treebanks} treebanks, {total_sentences:,} sentences, {total_tokens:,} tokens")
    
    return {
        'languages': len(languages_data),
        'treebanks': total_treebanks,
        'sentences': total_sentences,
        'tokens': total_tokens
    }


def generate_ud_maps(metadata, langNames, langnameGroup, data_dir, html_dir):
    """
    Generate UD Language Maps HTML file (convenience function that calls both steps).
    
    Parameters:
    -----------
    metadata : dict
        Metadata dict with 'langConllFiles' key mapping lang codes to file paths
    langNames : dict
        Mapping of language codes to language names
    langnameGroup : dict
        Mapping of language names to language family groups
    data_dir : str
        Path to data directory (for WALS data and stats output)
    html_dir : str
        Path to HTML output directory
        
    Returns:
    --------
    dict with 'languages', 'treebanks', 'sentences', 'tokens' counts
    """
    languages_data = collect_language_stats(metadata, langNames, langnameGroup, data_dir)
    return generate_ud_maps_html(languages_data, html_dir)


if __name__ == '__main__':
    print("This module should be imported and called from a notebook.")
    print("Usage:")
    print("  from generate_ud_maps import collect_language_stats, generate_ud_maps_html")
    print("  languages_data = collect_language_stats(metadata, langNames, langnameGroup, DATA_DIR)")
    print("  result = generate_ud_maps_html(languages_data, HTML_DIR)")
    print()
    print("Or use the combined function:")
    print("  from generate_ud_maps import generate_ud_maps")
    print("  result = generate_ud_maps(metadata, langNames, langnameGroup, DATA_DIR, HTML_DIR)")
    print("  generate_ud_maps(metadata, langNames, langnameGroup, DATA_DIR, HTML_DIR)")
