import React, { useState } from 'react';
import TranslucentLetters from './scenes/TranslucentLetters';
import Glassmorphism from './scenes/Glassmorphism';
import ParticleGalaxy from './scenes/ParticleGalaxy';
import LogoReveal from './scenes/LogoReveal';

const scenes = [
  { id: 'translucent-letters', name: 'Letras Translúcidas', desc: 'Texto 3D neón con dispersión interactiva — formato 9:16 Reel', component: TranslucentLetters },
  { id: 'glassmorphism', name: 'Glassmorphism', desc: 'Geometrías flotantes con efecto vidrio esmerilado y refracción', component: Glassmorphism },
  { id: 'particle-galaxy', name: 'Galaxia de Partículas', desc: 'Sistema orgánico de 2000 partículas con shaders y color dinámico', component: ParticleGalaxy },
  { id: 'logo-reveal', name: 'Logo Reveal', desc: 'Revelación de marca con partículas que confluyen en el texto', component: LogoReveal },
];

const styles = {
  container: {
    width: '100vw', height: '100vh', overflow: 'hidden',
    background: '#050510', color: '#fff', fontFamily: 'system-ui, sans-serif',
  },
  gallery: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', height: '100%', gap: '2rem',
    padding: '2rem', boxSizing: 'border-box',
  },
  title: {
    fontSize: '2.5rem', fontWeight: 300, letterSpacing: '0.3em',
    background: 'linear-gradient(135deg, #00ccff, #7744ff)',
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    margin: 0,
  },
  subtitle: {
    fontSize: '1rem', opacity: 0.4, letterSpacing: '0.2em', marginTop: '-1rem',
  },
  grid: {
    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '1.5rem', width: '100%', maxWidth: '1100px',
  },
  card: {
    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: 16, padding: '2rem', cursor: 'pointer',
    transition: 'all 0.3s ease', backdropFilter: 'blur(10px)',
  },
  cardTitle: { fontSize: '1.3rem', fontWeight: 600, margin: '0 0 0.5rem' },
  cardDesc: { fontSize: '0.85rem', opacity: 0.5, lineHeight: 1.5, margin: 0 },
  backBtn: {
    position: 'fixed', top: 20, left: 20, zIndex: 100,
    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
    color: '#fff', padding: '10px 20px', borderRadius: 8, cursor: 'pointer',
    fontSize: '0.85rem', backdropFilter: 'blur(10px)',
  },
};

function Gallery({ onSelect }) {
  return (
    <div style={styles.gallery}>
      <h1 style={styles.title}>GALERÍA 3D</h1>
      <p style={styles.subtitle}>★ Poimandres · Three.js · React Spring ★</p>
      <div style={styles.grid}>
        {scenes.map(s => (
          <div key={s.id} style={styles.card} onClick={() => onSelect(s.id)}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.transform = 'translateY(-4px)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.transform = 'none'; }}>
            <h3 style={styles.cardTitle}>{s.name}</h3>
            <p style={styles.cardDesc}>{s.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [current, setCurrent] = useState(null);

  if (!current) return <Gallery onSelect={setCurrent} />;

  const scene = scenes.find(s => s.id === current);
  const SceneComponent = scene?.component;

  return (
    <div style={styles.container}>
      <button style={styles.backBtn} onClick={() => setCurrent(null)}>← Galería</button>
      {SceneComponent && <SceneComponent />}
    </div>
  );
}
