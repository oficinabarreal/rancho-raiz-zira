import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sparkles, Bloom, EffectComposer } from '@react-three/drei';
import * as THREE from 'three';

function Galaxy() {
  const ref = useRef();
  const count = 3000;

  const [positions, colors, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const siz = new Float32Array(count);

    const colorA = new THREE.Color('#00ccff');
    const colorB = new THREE.Color('#ff3388');
    const colorC = new THREE.Color('#7744ff');

    for (let i = 0; i < count; i++) {
      const radius = Math.pow(Math.random(), 1.5) * 7;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      pos[i*3] = radius * Math.sin(phi) * Math.cos(theta);
      pos[i*3+1] = radius * Math.sin(phi) * Math.sin(theta) * 0.5;
      pos[i*3+2] = radius * Math.cos(phi);

      const t = radius / 7;
      const mix = t < 0.5
        ? colorA.clone().lerp(colorC, t * 2)
        : colorC.clone().lerp(colorB, (t - 0.5) * 2);

      col[i*3] = mix.r;
      col[i*3+1] = mix.g;
      col[i*3+2] = mix.b;

      siz[i] = 0.02 + Math.random() * 0.06;
    }
    return [pos, col, siz];
  }, []);

  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    g.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    return g;
  }, [positions, colors, sizes]);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.04;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.02) * 0.1;
    }
  });

  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial
        size={0.06}
        vertexColors
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

function SpiralArms() {
  const ref = useRef();
  const count = 1200;

  const [positions, colors] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const colorA = new THREE.Color('#00ff99');
    const colorB = new THREE.Color('#4488ff');

    for (let i = 0; i < count; i++) {
      const t = i / count;
      const angle = t * Math.PI * 8;
      const radius = t * 5;
      const arm = i % 2 === 0 ? 1 : -1;

      pos[i*3] = Math.cos(angle + arm * 0.5) * radius;
      pos[i*3+1] = (Math.random() - 0.5) * 1.5;
      pos[i*3+2] = Math.sin(angle + arm * 0.5) * radius;

      const c = colorA.clone().lerp(colorB, t);
      col[i*3] = c.r;
      col[i*3+1] = c.g;
      col[i*3+2] = c.b;
    }
    return [pos, col];
  }, []);

  const geo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    return g;
  }, [positions, colors]);

  useFrame((state) => {
    if (ref.current) ref.current.rotation.y = state.clock.elapsedTime * 0.06;
  });

  return (
    <points ref={ref} geometry={geo}>
      <pointsMaterial size={0.04} vertexColors transparent opacity={0.6}
        blending={THREE.AdditiveBlending} depthWrite={false} sizeAttenuation />
    </points>
  );
}

export default function ParticleGalaxy() {
  return (
    <Canvas camera={{ position: [0, 1, 8], fov: 50 }} dpr={[1, 2]}
      style={{ width: '100%', height: '100%', background: '#030308' }}>
      <Galaxy />
      <SpiralArms />

      <Sparkles count={200} scale={12} size={0.5} speed={0.1} opacity={0.15} color="#4488ff" />

      <OrbitControls autoRotate autoRotateSpeed={0.2} enableZoom={false} enablePan={false}
        maxPolarAngle={Math.PI / 1.8} />

      <EffectComposer>
        <Bloom mipmapBlur luminanceThreshold={0.1} luminanceSmoothing={0.9} intensity={0.5} />
      </EffectComposer>
    </Canvas>
  );
}
