import * as THREE from 'three';
import { Clip } from '../engine/RanchoEngine.js';
import gsap from 'gsap';

export class GlassLettersClip extends Clip {
  constructor(options = {}) {
    super({ ...options, name: 'Glass Letters', duration: options.duration || 5 });
    this.text = options.text || 'RANCHO RAIZ';
    this.letters = [];
  }

  build(scene, camera) {
    const letterGroup = new THREE.Group();
    
    const glassMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      metalness: 0.0,
      roughness: 0.05,
      transmission: 0.95,
      thickness: 0.5,
      ior: 1.5,
      transparent: true,
      opacity: 0.8,
      clearcoat: 1.0,
      clearcoatRoughness: 0.0,
    });
    
    const neonColors = [0x00ccff, 0x00ff99, 0xff3388, 0x7744ff, 0xff6600, 0x00ddff];
    
    const chars = this.text.split('');
    const spacing = 1.2;
    const totalWidth = (chars.length - 1) * spacing;
    
    chars.forEach((char, i) => {
      if (char === ' ') return;
      
      const letterMesh = this.createLetterMesh(char, glassMaterial, neonColors[i % neonColors.length]);
      letterMesh.position.x = -totalWidth / 2 + i * spacing;
      
      this.letters.push({
        mesh: letterMesh,
        originalX: letterMesh.position.x,
        originalY: letterMesh.position.y,
        originalZ: letterMesh.position.z,
        index: i
      });
      
      letterGroup.add(letterMesh);
    });
    
    const glowGeometry = new THREE.SphereGeometry(0.05, 8, 8);
    for (let i = 0; i < 20; i++) {
      const color = neonColors[i % neonColors.length];
      const glowMaterial = new THREE.MeshBasicMaterial({ color });
      const glow = new THREE.Mesh(glowGeometry, glowMaterial);
      
      glow.position.set(
        (Math.random() - 0.5) * totalWidth,
        (Math.random() - 0.5) * 3,
        (Math.random() - 0.5) * 2
      );
      
      glow.userData = {
        originalPos: glow.position.clone(),
        speed: 0.5 + Math.random() * 1,
        offset: Math.random() * Math.PI * 2
      };
      
      letterGroup.add(glow);
      this.letters.push({ mesh: glow, isParticle: true });
    }
    
    this.group = letterGroup;
    scene.add(this.group);
  }

  createLetterMesh(char, material, glowColor) {
    const size = 0.6;
    const geometries = {
      'A': new THREE.ConeGeometry(size * 0.6, size * 1.5, 4),
      'B': new THREE.BoxGeometry(size * 0.8, size * 1.4, size * 0.3),
      'C': new THREE.TorusGeometry(size * 0.5, size * 0.15, 8, 20, Math.PI * 1.5),
      'D': new THREE.CylinderGeometry(size * 0.3, size * 0.3, size * 1.2, 16),
      'E': new THREE.BoxGeometry(size * 0.8, size * 1.4, size * 0.3),
      'F': new THREE.BoxGeometry(size * 0.7, size * 1.3, size * 0.3),
      'G': new THREE.TorusGeometry(size * 0.5, size * 0.15, 8, 24),
      'H': new THREE.BoxGeometry(size * 0.8, size * 1.4, size * 0.3),
      'I': new THREE.CylinderGeometry(size * 0.15, size * 0.15, size * 1.4, 8),
      'J': new THREE.CylinderGeometry(size * 0.25, size * 0.25, size * 1.2, 12),
      'K': new THREE.ConeGeometry(size * 0.6, size * 1.4, 4),
      'L': new THREE.BoxGeometry(size * 0.7, size * 1.2, size * 0.3),
      'M': new THREE.ConeGeometry(size * 0.7, size * 1.4, 4),
      'N': new THREE.CylinderGeometry(size * 0.2, size * 0.2, size * 1.3, 8),
      'O': new THREE.TorusGeometry(size * 0.5, size * 0.15, 8, 24),
      'P': new THREE.CylinderGeometry(size * 0.3, size * 0.3, size * 1.2, 16),
      'Q': new THREE.TorusGeometry(size * 0.5, size * 0.15, 8, 28),
      'R': new THREE.CylinderGeometry(size * 0.3, size * 0.3, size * 1.2, 16),
      'S': new THREE.TorusGeometry(size * 0.4, size * 0.12, 8, 20),
      'T': new THREE.BoxGeometry(size * 0.9, size * 1.1, size * 0.3),
      'U': new THREE.CylinderGeometry(size * 0.4, size * 0.4, size * 1.0, 16),
      'V': new THREE.ConeGeometry(size * 0.5, size * 1.3, 4),
      'W': new THREE.BoxGeometry(size * 1.0, size * 1.2, size * 0.3),
      'X': new THREE.BoxGeometry(size * 0.8, size * 0.8, size * 0.3),
      'Y': new THREE.ConeGeometry(size * 0.4, size * 1.2, 4),
      'Z': new THREE.BoxGeometry(size * 0.8, size * 1.0, size * 0.3),
    };
    
    const geometry = geometries[char.toUpperCase()] || new THREE.BoxGeometry(size * 0.6, size * 1.0, size * 0.3);
    const mesh = new THREE.Mesh(geometry, material);
    
    const glowGeom = new THREE.SphereGeometry(size * 0.8, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({ 
      color: glowColor, 
      transparent: true, 
      opacity: 0.15 
    });
    const glow = new THREE.Mesh(glowGeom, glowMat);
    mesh.add(glow);
    
    const edgesGeom = new THREE.EdgesGeometry(geometry);
    const edgesMat = new THREE.LineBasicMaterial({ 
      color: glowColor,
      transparent: true,
      opacity: 0.6
    });
    const edges = new THREE.LineSegments(edgesGeom, edgesMat);
    mesh.add(edges);
    
    return mesh;
  }

  animate(elapsed, duration, camera, scene) {
    const progress = elapsed / duration;
    
    this.letters.forEach((letter, i) => {
      if (letter.isParticle) {
        const ud = letter.mesh.userData;
        letter.mesh.position.y = ud.originalPos.y + Math.sin(elapsed * ud.speed + ud.offset) * 0.5;
        letter.mesh.position.x = ud.originalPos.x + Math.cos(elapsed * ud.speed * 0.7 + ud.offset) * 0.3;
        return;
      }
      
      const delay = letter.index * 0.05;
      const localProgress = Math.max(0, Math.min(1, (progress - delay) / 0.6));
      
      if (localProgress > 0 && localProgress < 1) {
        const eased = 1 - Math.pow(1 - localProgress, 3);
        letter.mesh.position.y = letter.originalY + Math.sin(elapsed * 3 + i) * 0.1 * eased;
        letter.mesh.rotation.z = Math.sin(elapsed * 2 + i * 0.5) * 0.05 * eased;
      }
      
      letter.mesh.rotation.y += 0.003;
    });
    
    if (progress > 0.2 && progress < 0.8) {
      const scale = 1 + Math.sin((progress - 0.2) / 0.6 * Math.PI) * 0.1;
      this.group.scale.setScalar(scale);
    }
    
    this.group.rotation.y = Math.sin(elapsed * 0.3) * 0.15;
    this.group.rotation.x = Math.sin(elapsed * 0.2) * 0.05;
  }
}
