import { useEffect, useRef } from "react";
import * as THREE from "three";

import "./sphere.css";

function AustinSphere({ state }) {
  const mountRef = useRef(null);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    const mount = mountRef.current;

    if (!mount) {
      return;
    }

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
      45,
      mount.clientWidth / mount.clientHeight,
      0.1,
      100
    );

    camera.position.z = 4.5;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    });

    renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, 2)
    );

    renderer.setSize(
      mount.clientWidth,
      mount.clientHeight
    );

    renderer.setClearColor(
      0x000000,
      0
    );

    renderer.domElement.style.position = "absolute";
    renderer.domElement.style.inset = "0";
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.zIndex = "0";
    renderer.domElement.style.pointerEvents = "none";

    mount.appendChild(
      renderer.domElement
    );

    const particleCount = 7000;

    const positions = new Float32Array(
      particleCount * 3
    );

    const sizes = new Float32Array(
      particleCount
    );

    for (
      let i = 0;
      i < particleCount;
      i++
    ) {
      const radius = 1.55;

      const theta =
        Math.random() * Math.PI * 2;

      const phi =
        Math.acos(
          2 * Math.random() - 1
        );

      const variation =
        0.9 +
        Math.random() * 0.18;

      positions[i * 3] =
        radius *
        variation *
        Math.sin(phi) *
        Math.cos(theta);

      positions[i * 3 + 1] =
        radius *
        variation *
        Math.sin(phi) *
        Math.sin(theta);

      positions[i * 3 + 2] =
        radius *
        variation *
        Math.cos(phi);

      sizes[i] =
        0.45 +
        Math.random() * 0.9;
    }

    const geometry =
      new THREE.BufferGeometry();

    geometry.setAttribute(
      "position",
      new THREE.BufferAttribute(
        positions,
        3
      )
    );

    geometry.setAttribute(
      "size",
      new THREE.BufferAttribute(
        sizes,
        1
      )
    );

    const material =
      new THREE.ShaderMaterial({
        transparent: true,

        depthWrite: false,

        blending:
          THREE.AdditiveBlending,

        uniforms: {
          uTime: {
            value: 0
          }
        },

        vertexShader: `
          attribute float size;

          uniform float uTime;

          varying float vAlpha;

          void main() {

            vec3 p = position;

            float wave =
              sin(
                p.y * 4.0 +
                uTime * 1.2
              ) * 0.025;

            p += normalize(p) * wave;

            vec4 mvPosition =
              modelViewMatrix *
              vec4(p, 1.0);

            gl_PointSize =
              size *
              (90.0 / -mvPosition.z);

            gl_Position =
              projectionMatrix *
              mvPosition;

            vAlpha = size;
          }
        `,

        fragmentShader: `
          varying float vAlpha;

          void main() {

            vec2 uv =
              gl_PointCoord - 0.5;

            float distance =
              length(uv);

            float glow =
              1.0 -
              smoothstep(
                0.0,
                0.5,
                distance
              );

            gl_FragColor =
              vec4(
                0.15,
                0.75,
                1.0,
                glow * 0.9
              );
          }
        `
      });

    const particles =
      new THREE.Points(
        geometry,
        material
      );

    scene.add(
      particles
    );

    const coreGeometry =
      new THREE.SphereGeometry(
        1.25,
        48,
        48
      );

    const coreMaterial =
      new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0.035,
        wireframe: true
      });

    const core =
      new THREE.Mesh(
        coreGeometry,
        coreMaterial
      );

    scene.add(
      core
    );

    const clock =
      new THREE.Clock();

    let animationFrame;

    function animate() {
      animationFrame =
        requestAnimationFrame(
          animate
        );

      const elapsed =
        clock.getElapsedTime();

      const currentState =
        stateRef.current;

      const speed =
        currentState === "thinking"
          ? 0.006
          : currentState === "responding"
            ? 0.004
            : 0.0018;

      particles.rotation.x +=
        speed * 0.8;

      particles.rotation.y +=
        speed;

      particles.rotation.z +=
        speed * 0.45;

      core.rotation.x -=
        speed * 0.5;

      core.rotation.y +=
        speed * 0.7;

      const pulse =
        currentState === "thinking"
          ? 1 +
            Math.sin(elapsed * 5) *
            0.045
          : 1 +
            Math.sin(elapsed * 1.5) *
            0.012;

      particles.scale.setScalar(
        pulse
      );

      material.uniforms.uTime.value =
        elapsed;

      renderer.render(
        scene,
        camera
      );
    }

    animate();

    function handleResize() {
      const width =
        mount.clientWidth;

      const height =
        mount.clientHeight;

      if (
        width <= 0 ||
        height <= 0
      ) {
        return;
      }

      camera.aspect =
        width / height;

      camera.updateProjectionMatrix();

      renderer.setSize(
        width,
        height
      );
    }

    window.addEventListener(
      "resize",
      handleResize
    );

    return () => {
      cancelAnimationFrame(
        animationFrame
      );

      window.removeEventListener(
        "resize",
        handleResize
      );

      geometry.dispose();
      material.dispose();

      coreGeometry.dispose();
      coreMaterial.dispose();

      renderer.dispose();

      if (
        renderer.domElement.parentNode ===
        mount
      ) {
        mount.removeChild(
          renderer.domElement
        );
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="austin-sphere"
    />
  );
}

export default AustinSphere;