import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, MeshTransmissionMaterial, Environment, OrbitControls, Bloom, EffectComposer } from '@react-three/drei';
import * as THREE from 'three';

const COLORS = ['#00ccff', '#7744ff', '#ff3388', '#00ff99', '#ff6600'];

function Gem({ position, color, index }) {
  const ref = useRef();
  const phase = useMemo(() => Math.random() * Math.PI * 2, []);

  const geometries = [
    <icosahedronGeometry args={[1, 0]} />,
    <octahedronGeometry args={[1]} />,
    <torusKnotGeometry args={[0.8, 0.3, 64, 8]} />,
    <dodecahedronGeometry args={[1]} />,
  ];
  const Geo = geometries[index % geometries.length];

  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.elapsedTime;
      ref.current.rotation.x = t * 0.2 + phase;
      ref.current.rotation.y = t * 0.3 + phase;
      // Pulse scale
      const s = 1 + 0.05 * Math.sin(t * 0.5 + phase);
      ref.current.scale.setScalar(s);
    }
  });

  return (
    <Float position={position} speed={0.5 + index * 0.1} rotationIntensity={0.3} floatIntensity={0.6}>
      <mesh ref={ref}>
        {Geo}
        <MeshTransmissionMaterial
          color={color}
          roughness={0.1}
          thickness={1.2}
          ior={1.5}
          chromaticAberration={0.6}
          anisotropy={0.3}
          distortion={0.4}
          distortionScale={0.8}
          temporalDistortion={0.2}
          clearcoat={1}
          envMapIntensity={1.5}
          transparent opacity={0.85}
        />
      </mesh>
    </Float>
  );
}

function Ring({ radius, color, speed }) {
  const ref = useRef();
  const points = useMemo(() => {
    const pts = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      pts.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius * 0.3, 0));
    }
    return pts;
  }, [radius]);

  useFrame((state) => {
    if (ref.current) ref.current.rotation.z = state.clock.elapsedTime * speed;
  });

  return (
    <mesh ref={ref}>
      <tubeGeometry args={[new THREE.CatmullRomCurve3(points, true), 64, 0.02, 8, true]} />
      <meshBasicMaterial color={color} transparent opacity={0.15} />
    </mesh>
  );
}

export default function Glassmorphism() {
  return (
    <Canvas camera={{ position: [0, 0, 9], fov: 40 }} dpr={[1, 2]}
      style={{ width: '100%', height: '100%', background: '#080816' }}>
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={2} />
      <pointLight position={[-5, -3, 5]} intensity={1} color="#7744ff" />

      <Environment preset="sunset" />

      {[0, 1, 2, 3, 4].map(i => (
        <Gem key={i}
          position={[
            (i - 2) * 2.2,
            Math.sin(i * 1.5) * 0.8,
            -1 + Math.sin(i * 0.7) * 0.5,
          ]}
          color={COLORS[i]}
          index={i}
        />
      ))}

      <Ring radius={4} color="#00ccff" speed={0.1} />
      <Ring radius={3.2} color="#7744ff" speed={-0.08} />
      <Ring radius={2.4} color="#ff3388" speed={0.06} />

      <OrbitControls autoRotate autoRotateSpeed={0.3} enableZoom={false} enablePan={false}
        maxPolarAngle={Math.PI / 2.1} />

      <EffectComposer>
        <Bloom mipmapBlur luminanceThreshold={0.3} luminanceSmoothing={0.8} intensity={0.6} />
      </EffectComposer>
    </Canvas>
  );
}
