import * as THREE from 'three';
import gsap from 'gsap';

export class RanchoEngine {
  constructor(options = {}) {
    this.width = options.width || 1080;
    this.height = options.height || 1920;
    this.fps = options.fps || 60;
    this.duration = options.duration || 8;
    this.autoRecord = options.autoRecord || false;
    
    this.clock = new THREE.Clock();
    this.isRecording = false;
    this.recordedChunks = [];
    this.mediaRecorder = null;
    this.onComplete = options.onComplete || (() => {});
    
    this.init();
  }

  init() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x050510);
    
    this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 0.1, 1000);
    this.camera.position.set(0, 0, 10);
    
    this.renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      preserveDrawingBuffer: true 
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(1);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    this.scene.add(this.ambientLight);
    
    this.directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    this.directionalLight.position.set(5, 5, 5);
    this.scene.add(this.directionalLight);
  }

  addToScene(object) {
    this.scene.add(object);
  }

  setupLights(warm = true) {
    this.ambientLight.intensity = warm ? 0.3 : 0.5;
    
    if (warm) {
      const warmLight = new THREE.PointLight(0xffa500, 2, 20);
      warmLight.position.set(0, 2, 0);
      this.scene.add(warmLight);
      
      const coolLight = new THREE.DirectionalLight(0x4488ff, 0.5);
      coolLight.position.set(-5, 3, -5);
      this.scene.add(coolLight);
    }
  }

  animateCamera(keyframes) {
    const tl = gsap.timeline();
    
    keyframes.forEach(kf => {
      const target = kf.target || this.camera.position;
      tl.to(target, {
        x: kf.x,
        y: kf.y,
        z: kf.z,
        duration: kf.duration || 1,
        ease: kf.ease || 'power2.inOut'
      }, kf.startTime || '<');
    });
    
    return tl;
  }

  startRecording() {
    const stream = this.renderer.domElement.captureStream(this.fps);
    
    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'video/webm;codecs=vp9',
      videoBitsPerSecond: 50000000
    });
    
    this.recordedChunks = [];
    
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.recordedChunks.push(e.data);
      }
    };
    
    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
      this.onComplete(blob);
    };
    
    this.mediaRecorder.start();
    this.isRecording = true;
    this.clock.start();
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
  }

  render(callback) {
    const elapsed = this.clock.getElapsedTime();
    
    if (callback) {
      callback(elapsed, this.duration);
    }
    
    this.renderer.render(this.scene, this.camera);
    
    if (this.isRecording && elapsed >= this.duration) {
      this.stopRecording();
      return;
    }
    
    requestAnimationFrame(() => this.render(callback));
  }

  getCanvas() {
    return this.renderer.domElement;
  }

  mount(container) {
    container.appendChild(this.renderer.domElement);
  }
}

export class Clip {
  constructor(options = {}) {
    this.duration = options.duration || 5;
    this.name = options.name || 'Untitled Clip';
    this.group = new THREE.Group();
  }

  build(scene, camera) {
    throw new Error('Clip.build() must be implemented');
  }

  animate(elapsed, duration, camera, scene) {
  }

  getObject() {
    return this.group;
  }
}
