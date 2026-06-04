#!/usr/bin/env python3
"""
SVG Emoji Components - formas geométricas que reemplazan emoji text.
Cualquier renderizador SVG (cairosvg, Chromium, etc.) puede dibujarlas.
"""
import re

# Cada emoji → grupo SVG inline
EMOJI_SVG = {
    "⛰️": """  <!-- Mountain (alt) -->
  <g transform="translate(540, 260)" fill="#94a3b8">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#64748b"/>
    <polygon points="0,-28 -28,18 28,18" fill="#64748b"/>
    <polygon points="-22,18 0,-10 22,18" fill="#94a3b8"/>
    <polygon points="-12,18 0,4 12,18" fill="#cbd5e1"/>
    <polygon points="0,-28 -6,-4 6,-4" fill="#fff" opacity="0.6"/>
  </g>""",
    
    "🌙": """  <!-- Moon crescent -->
  <g transform="translate(540, 260)" fill="#f7c92b">
    <circle cx="0" cy="0" r="36" fill="#f7c92b" opacity="0.15"/>
    <circle cx="0" cy="0" r="28" fill="#f7c92b"/>
    <circle cx="8" cy="-6" r="22" fill="#0f172a"/>
  </g>""",
    
    "🏔️": """  <!-- Mountain -->
  <g transform="translate(540, 260)" fill="#94a3b8">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#4a9eff"/>
    <polygon points="0,-32 -30,20 30,20" fill="#64748b"/>
    <polygon points="-30,20 0,-12 20,20" fill="#94a3b8"/>
    <polygon points="0,-32 -8,-10 8,-10" fill="#fff" opacity="0.8"/>
  </g>""",
    
    "🏞️": """  <!-- Park / River -->
  <g transform="translate(540, 260)" fill="#94a3b8">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#10b981"/>
    <polygon points="0,-28 -25,15 25,15" fill="#64748b"/>
    <polygon points="-25,15 0,-8 20,15" fill="#94a3b8"/>
    <path d="M-15,8 Q-5,12 0,8 Q5,4 15,8" stroke="#10b981" stroke-width="2.5" fill="none" opacity="0.8"/>
    <polygon points="0,-28 -6,-6 6,-6" fill="#fff" opacity="0.7"/>
  </g>""",
    
    "🧘": """  <!-- Lotus / Meditation -->
  <g transform="translate(540, 260)" fill="#a78bfa">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#a78bfa"/>
    <ellipse cx="0" cy="-8" rx="18" ry="10" fill="#c4b5fd"/>
    <ellipse cx="0" cy="-2" rx="12" ry="8" fill="#a78bfa"/>
    <circle cx="0" cy="-18" r="6" fill="#c4b5fd"/>
    <path d="M-10,2 Q-6,8 0,10 Q6,8 10,2" stroke="#7c3aed" stroke-width="1.5" fill="none"/>
  </g>""",
    
    "🤗": """  <!-- Hug / Open arms -->
  <g transform="translate(540, 260)" fill="#fbbf24">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#fbbf24"/>
    <circle cx="0" cy="-3" r="16" fill="#fbbf24"/>
    <circle cx="-6" cy="-6" r="3" fill="#92400e"/>
    <circle cx="6" cy="-6" r="3" fill="#92400e"/>
    <path d="M-6,4 Q0,10 6,4" stroke="#92400e" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M-22,-8 Q-28,-2 -22,8" stroke="#fbbf24" stroke-width="5" fill="none" stroke-linecap="round"/>
    <path d="M22,-8 Q28,-2 22,8" stroke="#fbbf24" stroke-width="5" fill="none" stroke-linecap="round"/>
  </g>""",
    
    "🌳": """  <!-- Tree -->
  <g transform="translate(540, 260)" fill="#10b981">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#10b981"/>
    <rect x="-3" y="5" width="6" height="18" rx="2" fill="#92400e"/>
    <circle cx="0" cy="-10" r="18" fill="#34d399"/>
    <circle cx="-10" cy="-2" r="12" fill="#10b981"/>
    <circle cx="10" cy="-2" r="12" fill="#10b981"/>
    <circle cx="0" cy="-16" r="10" fill="#6ee7b7"/>
  </g>""",
    
    "🌿": """  <!-- Leaf / Herb -->
  <g transform="translate(540, 260)" fill="#10b981">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#10b981"/>
    <path d="M0,18 Q-20,0 0,-18 Q20,0 0,18Z" fill="#34d399"/>
    <path d="M0,18 Q-12,4 -4,-6" stroke="#10b981" stroke-width="2" fill="none"/>
    <path d="M0,18 Q12,4 4,-6" stroke="#10b981" stroke-width="2" fill="none"/>
    <line x1="0" y1="18" x2="0" y2="-14" stroke="#065f46" stroke-width="1.5"/>
  </g>""",
    
    "☀️": """  <!-- Sun -->
  <g transform="translate(540, 260)" fill="#fbbf24">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#fbbf24"/>
    <circle cx="0" cy="0" r="16" fill="#fbbf24"/>
    <circle cx="0" cy="0" r="12" fill="#f59e0b"/>
    <g stroke="#fbbf24" stroke-width="3" stroke-linecap="round">
      <line x1="0" y1="-24" x2="0" y2="-30"/>
      <line x1="0" y1="24" x2="0" y2="30"/>
      <line x1="-24" y1="0" x2="-30" y2="0"/>
      <line x1="24" y1="0" x2="30" y2="0"/>
      <line x1="-17" y1="-17" x2="-21" y2="-21"/>
      <line x1="17" y1="-17" x2="21" y2="-21"/>
      <line x1="-17" y1="17" x2="-21" y2="21"/>
      <line x1="17" y1="17" x2="21" y2="21"/>
    </g>
  </g>""",
    
    "💎": """  <!-- Diamond -->
  <g transform="translate(540, 260)" fill="#a78bfa">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#a78bfa"/>
    <polygon points="0,-22 20,0 0,22 -20,0" fill="#c4b5fd"/>
    <polygon points="0,-22 10,0 0,22" fill="#a78bfa"/>
    <polygon points="0,-10 20,0 -20,0" fill="#8b5cf6" opacity="0.3"/>
    <circle cx="0" cy="0" r="4" fill="#fff" opacity="0.6"/>
  </g>""",
    
    "🌅": """  <!-- Sunrise -->
  <g transform="translate(540, 260)" fill="#f59e0b">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#f59e0b"/>
    <circle cx="0" cy="-4" r="14" fill="#fbbf24"/>
    <rect x="-30" y="10" width="60" height="4" rx="2" fill="#f59e0b"/>
    <g stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" opacity="0.6">
      <line x1="0" y1="-22" x2="0" y2="-28"/>
      <line x1="16" y1="-16" x2="22" y2="-20"/>
      <line x1="-16" y1="-16" x2="-22" y2="-20"/>
    </g>
    <path d="M-20,10 Q-10,4 0,10 Q10,4 20,10" fill="none" stroke="#f59e0b" stroke-width="3"/>
  </g>""",
    
    "🌧️": """  <!-- Rain -->
  <g transform="translate(540, 260)" fill="#60a5fa">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#60a5fa"/>
    <path d="M-18,-8 Q-14,-18 -4,-14 Q0,-24 10,-16 Q20,-20 22,-8 Q28,-2 22,6 Z" fill="#93c5fd"/>
    <g stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round">
      <line x1="-14" y1="10" x2="-18" y2="20"/>
      <line x1="-4" y1="12" x2="-8" y2="24"/>
      <line x1="6" y1="10" x2="2" y2="22"/>
      <line x1="14" y1="8" x2="10" y2="18"/>
    </g>
  </g>""",
    
    "🔥": """  <!-- Fire -->
  <g transform="translate(540, 260)" fill="#ef4444">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#ef4444"/>
    <path d="M0,18 Q-14,2 -8,-8 Q-2,-16 0,-24 Q2,-16 8,-8 Q14,2 0,18Z" fill="#f97316"/>
    <path d="M0,18 Q-6,6 -2,-4 Q0,-10 0,-16 Q2,-8 6,-2 Q8,6 0,18Z" fill="#fbbf24"/>
    <path d="M0,16 Q-3,8 0,0 Q2,6 3,10 Q3,14 0,16Z" fill="#fff" opacity="0.5"/>
  </g>""",
    
    "❄️": """  <!-- Snowflake -->
  <g transform="translate(540, 260)" fill="#e2e8f0">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#e2e8f0"/>
    <g stroke="#93c5fd" stroke-width="2.5" stroke-linecap="round">
      <line x1="0" y1="-20" x2="0" y2="20"/>
      <line x1="-17" y1="-10" x2="17" y2="10"/>
      <line x1="-17" y1="10" x2="17" y2="-10"/>
    </g>
    <g fill="#93c5fd">
      <circle cx="0" cy="-22" r="2.5"/>
      <circle cx="0" cy="22" r="2.5"/>
      <circle cx="-19" cy="-11" r="2.5"/>
      <circle cx="19" cy="11" r="2.5"/>
      <circle cx="-19" cy="11" r="2.5"/>
      <circle cx="19" cy="-11" r="2.5"/>
    </g>
  </g>""",
    
    "💦": """  <!-- Water drops -->
  <g transform="translate(540, 260)" fill="#60a5fa">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#60a5fa"/>
    <ellipse cx="-8" cy="-4" rx="5" ry="8" fill="#60a5fa" transform="rotate(-15,-8,-4)"/>
    <ellipse cx="8" cy="2" rx="4" ry="7" fill="#93c5fd" transform="rotate(10,8,2)"/>
    <ellipse cx="0" cy="10" rx="3" ry="5" fill="#60a5fa" transform="rotate(-5,0,10)"/>
  </g>""",
    
    "✨": """  <!-- Sparkles -->
  <g transform="translate(540, 260)" fill="#fbbf24">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#fbbf24"/>
    <polygon points="0,-18 4,-6 16,-6 6,2 10,14 0,6 -10,14 -6,2 -16,-6 -4,-6" fill="#fbbf24"/>
    <circle cx="-16" cy="-14" r="3" fill="#fbbf24"/>
    <circle cx="14" cy="-18" r="2.5" fill="#fbbf24"/>
    <circle cx="-10" cy="18" r="2" fill="#fbbf24"/>
    <circle cx="16" cy="14" r="2" fill="#fbbf24"/>
  </g>""",
    
    "🎵": """  <!-- Musical note -->
  <g transform="translate(540, 260)" fill="#4a9eff">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#4a9eff"/>
    <circle cx="-4" cy="6" r="6" fill="#4a9eff"/>
    <circle cx="8" cy="0" r="5" fill="#60a5fa"/>
    <line x1="2" y1="6" x2="2" y2="-16" stroke="#4a9eff" stroke-width="3" stroke-linecap="round"/>
    <line x1="13" y1="0" x2="13" y2="-14" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M2,-16 Q10,-12 13,-14" stroke="#4a9eff" stroke-width="2.5" fill="none"/>
  </g>""",
    
    "🌟": """  <!-- Star -->
  <g transform="translate(540, 260)" fill="#fbbf24">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#fbbf24"/>
    <polygon points="0,-22 6,-8 20,-8 9,2 13,16 0,8 -13,16 -9,2 -20,-8 -6,-8" fill="#fbbf24"/>
    <polygon points="0,-18 4,-6 14,-6 6,2 9,12 0,6 -9,12 -6,2 -14,-6 -4,-6" fill="#f59e0b" opacity="0.6"/>
  </g>""",
    
    "⚡": """  <!-- Lightning -->
  <g transform="translate(540, 260)" fill="#fbbf24">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#fbbf24"/>
    <polygon points="4,-22 -6,0 2,0 -4,22 10,-2 0,-2" fill="#fbbf24"/>
    <polygon points="2,-18 -4,0 2,0 -2,14 6,-2 0,-2" fill="#fff" opacity="0.4"/>
  </g>""",
    
    "🌄": """  <!-- Sunrise over mountains -->
  <g transform="translate(540, 260)" fill="#f59e0b">
    <circle cx="0" cy="0" r="36" opacity="0.1" fill="#f59e0b"/>
    <circle cx="0" cy="-6" r="12" fill="#f97316"/>
    <polygon points="-30,12 -15,-8 0,5 15,-4 30,12" fill="#475569"/>
    <polygon points="-30,16 -10,0 10,8 30,12" fill="#334155"/>
    <g stroke="#fbbf24" stroke-width="2" stroke-linecap="round" opacity="0.5">
      <line x1="0" y1="-22" x2="0" y2="-28"/>
      <line x1="14" y1="-16" x2="18" y2="-20"/>
      <line x1="-14" y1="-16" x2="-18" y2="-20"/>
    </g>
  </g>""",
}

def replace_emoji_in_svg(svg_content):
    """Replace emoji text elements with SVG shape equivalents."""
    for emoji, svg_fragment in EMOJI_SVG.items():
        # Match emoji inside <text> elements
        # Pattern: <text ...>EMOJI</text>
        pattern = re.escape(emoji)
        svg_content = re.sub(
            rf'<text[^>]*>{pattern}</text>',
            svg_fragment,
            svg_content
        )
    return svg_content


if __name__ == "__main__":
    # Test with one SVG
    import sys
    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if test_path:
        with open(test_path) as f:
            content = f.read()
        
        before_emoji = sum(content.count(e) for e in EMOJI_SVG)
        result = replace_emoji_in_svg(content)
        after_emoji = sum(result.count(e) for e in EMOJI_SVG)
        
        print(f"Emojis reemplazados: {before_emoji} → {after_emoji}")
        print(f"SVG actualizado: {len(content)} → {len(result)} chars")
        
        out_path = test_path.replace(".svg", "-fixed.svg")
        with open(out_path, "w") as f:
            f.write(result)
        print(f"Guardado: {out_path}")
    else:
        print(f"🧩 SVG Emoji Components disponibles: {len(EMOJI_SVG)}")
        for e in sorted(EMOJI_SVG.keys()):
            print(f"  {e} → SVG shape")
