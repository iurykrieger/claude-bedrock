"use client";

import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  radius: number;
  color: string;
  vx: number;
  vy: number;
  depth: number;
}

const NODE_COLORS = ["#a882ff", "#a882ff", "#e8754a", "#c4a8ff", "#f09070", "#34d399"];
const LINE_COLOR = [168, 130, 255];
const CONNECTION_DIST_DESKTOP = 150;
const CONNECTION_DIST_MOBILE = 100;
const MOUSE_DIST = 200;

export function GraphCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    let nodes: Node[] = [];
    let mouse = { x: -9999, y: -9999, active: false };
    let isMobile = window.innerWidth < 768;
    let nodeCount = isMobile ? 35 : 70;
    let connectionDist = isMobile ? CONNECTION_DIST_MOBILE : CONNECTION_DIST_DESKTOP;

    function resize() {
      const parent = canvas!.parentElement;
      if (!parent) return;
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function initNodes() {
      nodes = [];
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      for (let i = 0; i < nodeCount; i++) {
        const radius = 1 + Math.random() * 3.5;
        nodes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          radius,
          color: NODE_COLORS[Math.floor(Math.random() * NODE_COLORS.length)],
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          depth: 1 - ((radius - 1) / 3.5) * 0.6,
        });
      }
    }

    function draw() {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      ctx!.clearRect(0, 0, w, h);

      // Connection lines
      ctx!.lineWidth = 0.5;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const distSq = dx * dx + dy * dy;
          if (distSq < connectionDist * connectionDist) {
            const dist = Math.sqrt(distSq);
            const alpha = 0.04 * (1 - dist / connectionDist);
            ctx!.beginPath();
            ctx!.strokeStyle = `rgba(${LINE_COLOR[0]},${LINE_COLOR[1]},${LINE_COLOR[2]},${alpha})`;
            ctx!.moveTo(nodes[i].x, nodes[i].y);
            ctx!.lineTo(nodes[j].x, nodes[j].y);
            ctx!.stroke();
          }
        }
      }

      // Mouse connections
      if (mouse.active) {
        for (const node of nodes) {
          const dx = node.x - mouse.x;
          const dy = node.y - mouse.y;
          const distSq = dx * dx + dy * dy;
          if (distSq < MOUSE_DIST * MOUSE_DIST) {
            const dist = Math.sqrt(distSq);
            const alpha = 0.2 * (1 - dist / MOUSE_DIST);
            ctx!.beginPath();
            ctx!.strokeStyle = `rgba(${LINE_COLOR[0]},${LINE_COLOR[1]},${LINE_COLOR[2]},${alpha})`;
            ctx!.lineWidth = 1;
            ctx!.moveTo(mouse.x, mouse.y);
            ctx!.lineTo(node.x, node.y);
            ctx!.stroke();
          }
        }
        ctx!.lineWidth = 0.5;
        ctx!.beginPath();
        ctx!.arc(mouse.x, mouse.y, 3, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${LINE_COLOR[0]},${LINE_COLOR[1]},${LINE_COLOR[2]},0.3)`;
        ctx!.fill();
      }

      // Draw nodes
      for (const node of nodes) {
        if (mouse.active) {
          const dx = mouse.x - node.x;
          const dy = mouse.y - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < MOUSE_DIST && dist > 1) {
            const force = 0.005 * (1 - dist / MOUSE_DIST);
            node.vx += (dx / dist) * force;
            node.vy += (dy / dist) * force;
            const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
            if (speed > 0.4) {
              node.vx = (node.vx / speed) * 0.4;
              node.vy = (node.vy / speed) * 0.4;
            }
          }
        }

        // Glow
        ctx!.beginPath();
        ctx!.arc(node.x, node.y, node.radius * 2.5, 0, Math.PI * 2);
        ctx!.fillStyle = node.color + "08";
        ctx!.fill();

        // Core
        ctx!.beginPath();
        ctx!.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx!.fillStyle = node.color;
        ctx!.fill();

        // Move
        node.x += node.vx * node.depth;
        node.y += node.vy * node.depth;
        if (node.x < -20) node.x = w + 20;
        if (node.x > w + 20) node.x = -20;
        if (node.y < -20) node.y = h + 20;
        if (node.y > h + 20) node.y = -20;
      }

      if (isVisible) {
        animationRef.current = requestAnimationFrame(draw);
      }
    }

    function handleMouseMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      mouse = { x: e.clientX - rect.left, y: e.clientY - rect.top, active: true };
    }

    function handleMouseLeave() {
      mouse = { ...mouse, active: false };
    }

    function handleResize() {
      isMobile = window.innerWidth < 768;
      nodeCount = isMobile ? 35 : 70;
      connectionDist = isMobile ? CONNECTION_DIST_MOBILE : CONNECTION_DIST_DESKTOP;
      resize();
      initNodes();
    }

    // Respect prefers-reduced-motion
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Pause animation when off-viewport
    let isVisible = true;
    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisible = entry.isIntersecting;
        if (isVisible && !prefersReduced) {
          animationRef.current = requestAnimationFrame(draw);
        } else {
          cancelAnimationFrame(animationRef.current);
        }
      },
      { threshold: 0 }
    );
    observer.observe(canvas);

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);
    window.addEventListener("resize", handleResize);

    resize();
    initNodes();

    if (!prefersReduced) {
      draw();
    } else {
      // Draw a single static frame
      draw();
      cancelAnimationFrame(animationRef.current);
    }

    return () => {
      cancelAnimationFrame(animationRef.current);
      observer.disconnect();
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full opacity-60"
      aria-hidden="true"
    />
  );
}
