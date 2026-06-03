import * as THREE from 'three';
import { Clip } from '../engine/RanchoEngine.js';
import gsap from 'gsap';

export class ParticleTextClip extends Clip {
  constructor(options = {}) {
    super({ ...options, name: 'Particle Text', duration: options.duration || 6 });
    this.text = options.text || 'RANCHO';
    this.particleCount = options.particleCount || 3500;
    this.particles = [];
    this.targetPositions = [];
  }

  build(scene, camera) {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.font = 'bold 140px system-ui, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.text, canvas.width / 2, canvas.height / 2);
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    const textPixels = [];
    
    for (let y = 0; y < canvas.height; y += 2) {
      for (let x = 0; x < canvas.width; x += 2) {
        const i = (y * canvas.width + x) * 4;
        if (imageData[i] > 128) {
          textPixels.push({
            x: (x - canvas.width / 2) / 45,
            y: -(y - canvas.height / 2) / 45
          });
        }
      }
    }

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(this.particleCount * 3);
    const colors = new Float32Array(this.particleCount * 3);
    const sizes = new Float32Array(this.particleCount);
    
    const neonColors = [
      new THREE.Color(0x00ccff),
      new THREE.Color(0x00ff99),
      new THREE.Color(0xff3388),
      new THREE.Color(0x7744ff)
    ];

    for (let i = 0; i < this.particleCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 8 + Math.random() * 6;
      
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 2;
      
      const color = neonColors[Math.floor(Math.random() * neonColors.length)];
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
      
      sizes[i] = 0.08 + Math.random() * 0.1;
      
      const targetPixel = textPixels[i % textPixels.length];
      this.targetPositions.push({
        x: targetPixel ? targetPixel.x : (Math.random() - 0.5) * 4,
        y: targetPixel ? targetPixel.y : (Math.random() - 0.5) * 2,
        z: 0
      });
      
      this.particles.push({
        originalX: positions[i * 3],
        originalY: positions[i * 3 + 1],
        originalZ: positions[i * 3 + 2]
      });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 }
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float uTime;
        
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * 300.0 / -mvPosition.z;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        
        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          
          float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
          vec3 glow = vColor * (1.0 + 0.5 * sin(uTime * 2.0));
          
          gl_FragColor = vec4(glow, alpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    this.particleSystem = new THREE.Points(geometry, material);
    this.group.add(this.particleSystem);
    scene.add(this.group);
    
    this.material = material;
  }

  animate(elapsed, duration, camera, scene) {
    const positions = this.particleSystem.geometry.attributes.position.array;
    const progress = elapsed / duration;
    
    for (let i = 0; i < this.particleCount; i++) {
      const p = this.particles[i];
      const t = this.targetPositions[i];
      
      let phase = 0;
      if (progress < 0.3) {
        phase = progress / 0.3;
        phase = 1 - Math.pow(1 - phase, 3);
        positions[i * 3] = p.originalX + (t.x - p.originalX) * phase;
        positions[i * 3 + 1] = p.originalY + (t.y - p.originalY) * phase;
        positions[i * 3 + 2] = p.originalZ + (t.z - p.originalZ) * phase;
      } else if (progress > 0.7) {
        phase = (progress - 0.7) / 0.3;
        phase = phase * phase;
        positions[i * 3] = t.x + (p.originalX - t.x) * phase;
        positions[i * 3 + 1] = t.y + (p.originalY - t.y) * phase;
        positions[i * 3 + 2] = t.z + (p.originalZ - t.z) * phase;
      } else {
        positions[i * 3] = t.x + Math.sin(elapsed * 2 + i * 0.01) * 0.02;
        positions[i * 3 + 1] = t.y + Math.cos(elapsed * 1.5 + i * 0.02) * 0.02;
      }
    }
    
    this.particleSystem.geometry.attributes.position.needsUpdate = true;
    this.material.uniforms.uTime.value = elapsed;
    
    this.group.rotation.y = Math.sin(elapsed * 0.5) * 0.1;
  }
}
