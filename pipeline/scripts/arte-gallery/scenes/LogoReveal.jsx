import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Text, OrbitControls, Sparkles, Bloom, EffectComposer } from '@react-three/drei';
import { useSpring, animated } from '@react-spring/three';
import * as THREE from 'three';

const WORDS = ['Rancho', 'Raiz'];
const COLORS = ['#00ccff', '#7744ff'];

function ParticleBurst({ targetPos, color, count = 200 }) {
  const ref = useRef();
  const [phase, setPhase] = useState('forming');

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 3 + Math.random() * 4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      pos[i*3] = r * Math.sin(phi) * Math.cos(theta) + targetPos[0];
      pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta) + targetPos[1];
      pos[i*3+2] = r * Math.cos(phi) + targetPos[2];
    }
    return pos;
  }, []);

  const velocities = useMemo(() => {
    const v = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      v[i*3] = (Math.random() - 0.5) * 0.005;
      v[i*3+1] = (Math.random() - 0.5) * 0.005;
      v[i*3+2] = (Math.random() - 0.5) * 0.005;
    }
    return v;
  }, []);

  const sizes = useMemo(() => {
    const s = new Float32Array(count);
    for (let i = 0; i < count; i++) s[i] = 0.02 + Math.random() * 0.06;
    return s;
  }, []);

  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    return g;
  }, []);

  useFrame((state) => {
    if (!ref.current) return;

    const t = state.clock.elapsedTime;
    const pos = ref.current.geometry.attributes.position.array;

    for (let i = 0; i < count; i++) {
      // Orbit around target
      const dx = pos[i*3] - targetPos[0];
      const dy = pos[i*3+1] - targetPos[1];
      const dz = pos[i*3+2] - targetPos[2];
      const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

      if (dist > 0.5) {
        // Attraction force (slowly bring particles in)
        const force = 0.002 * (1 + Math.sin(t * 0.3 + i) * 0.3);
        pos[i*3] -= dx * force;
        pos[i*3+1] -= dy * force;
        pos[i*3+2] -= dz * force;
      }

      // Small orbital motion
      pos[i*3] += Math.sin(t * 0.5 + i * 0.1) * 0.001;
      pos[i*3+1] += Math.cos(t * 0.4 + i * 0.15) * 0.001;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial
        size={0.04}
        color={color}
        transparent
        opacity={0.6}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

function FloatingWord({ word, position, color, index }) {
  const ref = useRef();
  const phase = useMemo(() => Math.random() * Math.PI * 2, []);
  const speed = useMemo(() => 0.15 + Math.random() * 0.15, []);

  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.elapsedTime;
      ref.current.position.y = position[1] + Math.sin(t * speed + phase) * 0.2;
    }
  });

  return (
    <group ref={ref} position={position}>
      <Text fontSize={2.2} fontWeight={900} color={color} anchorX="center" anchorY="middle"
        transparent opacity={0.9} toneMapped={false}>
        {word}
      </Text>
      <ParticleBurst targetPos={[position[0], position[1] - 0.5, position[2] - 1]} color={color} count={index === 0 ? 250 : 180} />
    </group>
  );
}

export default function LogoReveal() {
  return (
    <Canvas camera={{ position: [0, 0, 10], fov: 40 }} dpr={[1, 2]}
      style={{ width: '100%', height: '100%', background: '#050510' }}>
      <ambientLight intensity={0.2} />
      <pointLight position={[5, 5, 5]} intensity={1} />
      <pointLight position={[-5, -3, 5]} intensity={0.5} color="#7744ff" />

      <FloatingWord word={WORDS[0]} position={[0, 1.2, 0]} color={COLORS[0]} index={0} />
      <FloatingWord word={WORDS[1]} position={[0, -1.2, 0]} color={COLORS[1]} index={1} />

      <Sparkles count={200} scale={12} size={0.6} speed={0.2} opacity={0.2} color="#4488ff" />

      <OrbitControls autoRotate autoRotateSpeed={0.3} enableZoom={false} enablePan={false}
        maxPolarAngle={Math.PI / 2} />

      <EffectComposer>
        <Bloom mipmapBlur luminanceThreshold={0.2} luminanceSmoothing={0.9} intensity={0.7} />
      </EffectComposer>
    </Canvas>
  );
}
