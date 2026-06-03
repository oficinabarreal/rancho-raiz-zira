import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Text, OrbitControls, Sparkles, Bloom, EffectComposer } from '@react-three/drei';
import { useSpring, animated } from '@react-spring/three';

const NEON = ['#00ccff','#3366ff','#00ff99','#7744ff','#ff3388','#ff6600','#00ffcc','#4488ff','#9933ff','#00ddff','#ff44aa'];

function Letter({ char, position: pos, color, index }) {
  const ref = useRef();
  const [scattered, setScattered] = useState(false);
  const phase = useMemo(() => Math.random() * Math.PI * 2, []);
  const speed = useMemo(() => 0.2 + Math.random() * 0.3, []);
  const amp = useMemo(() => 0.1 + Math.random() * 0.15, []);

  const { x, y, z, rotX, rotY, rotZ } = useSpring({
    x: scattered ? pos[0] + (Math.random() - 0.5) * 7 : pos[0],
    y: scattered ? (Math.random() - 0.5) * 5 : pos[1],
    z: scattered ? (Math.random() - 0.5) * 5 : pos[2],
    rotX: scattered ? Math.random() * 3 : 0,
    rotY: scattered ? Math.random() * 3 : 0,
    rotZ: scattered ? Math.random() * 2 : 0,
    config: { mass: 0.8, tension: 120, friction: 14 },
  });

  useFrame((state) => {
    if (!scattered && ref.current) {
      const t = state.clock.elapsedTime;
      ref.current.position.y = pos[1] + Math.sin(t * speed + phase) * amp;
      ref.current.position.x = pos[0] + Math.sin(t * speed * 0.6 + phase * 1.3) * amp * 0.3;
      ref.current.rotation.x = Math.sin(t * speed * 0.7 + phase) * amp * 0.8;
      ref.current.rotation.y = Math.sin(t * speed * 0.5 + phase * 1.1) * amp * 1.2;
    }
  });

  return (
    <animated.group ref={ref} position-x={x} position-y={y} position-z={z} rotation-x={rotX} rotation-y={rotY} rotation-z={rotZ}
      onClick={() => setScattered(!scattered)}>
      <Text fontSize={1.2} fontWeight={900} color={color} anchorX="center" anchorY="middle"
        transparent opacity={0.9} toneMapped={false}>
        {char}
      </Text>
      {/* Glow aura */}
      <Text fontSize={1.8} fontWeight={900} color={color} anchorX="center" anchorY="middle"
        transparent opacity={0.08} toneMapped={false} position-z={-0.05}>
        {char}
      </Text>
    </animated.group>
  );
}

export default function TranslucentLetters() {
  const text = 'Rancho Raiz';
  const spacing = 1.3;
  const total = text.length * spacing;
  const startX = -total / 2 + spacing / 2;

  // Detect aspect ratio for responsive layout
  const isVertical = typeof window !== 'undefined' && window.innerHeight > window.innerWidth;
  const cameraZ = isVertical ? 14 : 12;

  return (
    <>
      <Canvas camera={{ position: [0, 0.5, cameraZ], fov: 45 }} dpr={[1, 2]}
        style={{ width: '100%', height: '100%', background: '#050510' }}>
        <ambientLight intensity={0.2} />
        <pointLight position={[5, 5, 5]} intensity={0.5} />

        {text.split('').map((ch, i) =>
          ch === ' ' ? null : (
            <Letter key={i} char={ch} position={[startX + i * spacing, 0, 0]} color={NEON[i % NEON.length]} index={i} />
          )
        )}

        {/* Floating particles */}
        <Sparkles count={300} scale={10} size={0.8} speed={0.3} opacity={0.3} color="#4488ff" />

        <OrbitControls autoRotate autoRotateSpeed={0.5} enablePan={false}
          maxPolarAngle={Math.PI / 2.3} minPolarAngle={Math.PI / 4}
          enableZoom={false} />

        <EffectComposer>
          <Bloom mipmapBlur luminanceThreshold={0.2} luminanceSmoothing={0.9} intensity={0.8} />
        </EffectComposer>
      </Canvas>

      <div style={{
        position: 'absolute', bottom: 30, left: 0, width: '100%', textAlign: 'center',
        color: 'rgba(255,255,255,0.25)', fontSize: '0.75rem', letterSpacing: '0.2em',
        pointerEvents: 'none',
      }}>
        ✦ toca una letra para dispersar ✦
      </div>
    </>
  );
}
