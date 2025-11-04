import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Sphere, Box, Line } from '@react-three/drei';
import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';

function OrderSphere({ position, label }) {
  const meshRef = useRef();
  
  useFrame((state) => {
    // Gentle floating animation
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[0.3, 32, 32]}>
        <meshStandardMaterial 
          color="#ea580c" 
          emissive="#ea580c" 
          emissiveIntensity={0.4}
          metalness={0.3}
          roughness={0.4}
        />
      </Sphere>
      {label && (
        <Text
          position={[0, 0.6, 0]}
          fontSize={0.2}
          color="#1f2937"
          anchorX="center"
          anchorY="middle"
        >
          Order
        </Text>
      )}
    </group>
  );
}

function ItemSphere({ position, label, color, quantity }) {
  const meshRef = useRef();
  const size = 0.15 + Math.log(quantity + 1) * 0.05; // Size based on quantity
  
  useFrame((state) => {
    // Gentle floating animation (slightly different from order)
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2.5 + Math.random()) * 0.08;
    }
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[size, 24, 24]}>
        <meshStandardMaterial 
          color={color} 
          emissive={color}
          emissiveIntensity={0.2}
          metalness={0.2}
          roughness={0.5}
        />
      </Sphere>
      {label && (
        <Text
          position={[0, size + 0.3, 0]}
          fontSize={0.12}
          color="#374151"
          anchorX="center"
          anchorY="middle"
          maxWidth={2}
        >
          {label}
          {quantity > 1 && ` (×${quantity})`}
        </Text>
      )}
    </group>
  );
}

function Location({ position, label, isActive }) {
  return (
    <group position={position}>
      <Box args={[0.5, 0.3, 0.5]}>
        <meshStandardMaterial 
          color={isActive ? "#3b82f6" : "#d1d5db"} 
          emissive={isActive ? "#3b82f6" : "#9ca3af"}
          emissiveIntensity={isActive ? 0.5 : 0.1}
          metalness={0.3}
          roughness={0.6}
        />
      </Box>
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.15}
        color="#1f2937"
        anchorX="center"
        anchorY="middle"
        maxWidth={2}
      >
        {label}
      </Text>
    </group>
  );
}

function SupplierLocation({ position, label, country }) {
  return (
    <group position={position}>
      <Box args={[0.4, 0.2, 0.4]}>
        <meshStandardMaterial 
          color="#10b981" 
          emissive="#10b981"
          emissiveIntensity={0.2}
          metalness={0.2}
          roughness={0.7}
        />
      </Box>
      <Text
        position={[0, -0.4, 0]}
        fontSize={0.12}
        color="#374151"
        anchorX="center"
        anchorY="middle"
        maxWidth={2.5}
      >
        {label}
      </Text>
      <Text
        position={[0, -0.6, 0]}
        fontSize={0.1}
        color="#6b7280"
        anchorX="center"
        anchorY="middle"
      >
        {country}
      </Text>
    </group>
  );
}

function ProcessPath({ keyframes }) {
  if (!keyframes || keyframes.length < 2) return null;

  const points = keyframes.map(kf => new THREE.Vector3(...kf.position));
  
  return (
    <Line
      points={points}
      color="#f59e0b"
      lineWidth={2}
      dashed={true}
      dashScale={0.5}
      dashSize={0.1}
      gapSize={0.1}
    />
  );
}

function ItemPath({ keyframes, color }) {
  if (!keyframes || keyframes.length < 2) return null;

  const points = keyframes.map(kf => new THREE.Vector3(...kf.position));
  
  return (
    <Line
      points={points}
      color={color}
      lineWidth={1.5}
      dashed={true}
      dashScale={0.3}
      dashSize={0.05}
      gapSize={0.05}
      opacity={0.5}
      transparent={true}
    />
  );
}

function AnimatedOrder({ keyframes, currentTime }) {
  const [position, setPosition] = useState([0, 0, 0]);
  const [currentEvent, setCurrentEvent] = useState(null);

  useEffect(() => {
    if (!keyframes || keyframes.length === 0) return;

    // Find the current position based on time
    let prevKeyframe = keyframes[0];
    let nextKeyframe = keyframes[0];

    for (let i = 0; i < keyframes.length; i++) {
      if (keyframes[i].time <= currentTime) {
        prevKeyframe = keyframes[i];
        nextKeyframe = keyframes[i + 1] || keyframes[i];
      } else {
        break;
      }
    }

    // Interpolate between keyframes
    if (prevKeyframe.time === nextKeyframe.time) {
      setPosition(prevKeyframe.position);
      setCurrentEvent(prevKeyframe.label);
    } else {
      const t = (currentTime - prevKeyframe.time) / (nextKeyframe.time - prevKeyframe.time);
      const smoothT = Math.min(1, Math.max(0, t)); // Clamp to [0, 1]

      const interpolatedPos = [
        prevKeyframe.position[0] + (nextKeyframe.position[0] - prevKeyframe.position[0]) * smoothT,
        prevKeyframe.position[1] + (nextKeyframe.position[1] - prevKeyframe.position[1]) * smoothT,
        prevKeyframe.position[2] + (nextKeyframe.position[2] - prevKeyframe.position[2]) * smoothT,
      ];

      setPosition(interpolatedPos);
      setCurrentEvent(smoothT < 0.5 ? prevKeyframe.label : nextKeyframe.label);
    }
  }, [currentTime, keyframes]);

  return <OrderSphere position={position} label={currentEvent} />;
}

function AnimatedItem({ itemData, currentTime }) {
  const [position, setPosition] = useState([0, 0, 0]);
  const [showLabel, setShowLabel] = useState(false);

  useEffect(() => {
    if (!itemData || !itemData.keyframes || itemData.keyframes.length === 0) return;

    const keyframes = itemData.keyframes;
    let prevKeyframe = keyframes[0];
    let nextKeyframe = keyframes[0];

    for (let i = 0; i < keyframes.length; i++) {
      if (keyframes[i].time <= currentTime) {
        prevKeyframe = keyframes[i];
        nextKeyframe = keyframes[i + 1] || keyframes[i];
      } else {
        break;
      }
    }

    // Show label when item is in transit or at warehouse
    setShowLabel(prevKeyframe.status !== 'waiting');

    // Interpolate between keyframes
    if (prevKeyframe.time === nextKeyframe.time) {
      setPosition(prevKeyframe.position);
    } else {
      const t = (currentTime - prevKeyframe.time) / (nextKeyframe.time - prevKeyframe.time);
      const smoothT = Math.min(1, Math.max(0, t));

      const interpolatedPos = [
        prevKeyframe.position[0] + (nextKeyframe.position[0] - prevKeyframe.position[0]) * smoothT,
        prevKeyframe.position[1] + (nextKeyframe.position[1] - prevKeyframe.position[1]) * smoothT,
        prevKeyframe.position[2] + (nextKeyframe.position[2] - prevKeyframe.position[2]) * smoothT,
      ];

      setPosition(interpolatedPos);
    }
  }, [currentTime, itemData]);

  if (!itemData) return null;

  return (
    <>
      <ItemPath keyframes={itemData.keyframes} color={itemData.color} />
      <ItemSphere 
        position={position} 
        label={showLabel ? itemData.name : null}
        color={itemData.color}
        quantity={itemData.quantity}
      />
    </>
  );
}

function Scene({ sceneData, currentTime, isPlaying, playbackSpeed = 1, onTimeUpdate }) {
  // Safely destructure with default values
  const { 
    animation, 
    locations, 
    item_paths = [], 
    supplier_locations = [] 
  } = sceneData || {};

  useEffect(() => {
    if (!isPlaying || !animation) return;

    const interval = setInterval(() => {
      onTimeUpdate((prev) => {
        const next = prev + (0.1 * playbackSpeed);
        return next >= animation.duration ? 0 : next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, animation, onTimeUpdate]);

  // Determine active location based on current time
  const activeLocation = animation?.keyframes?.find(
    (kf, idx) => {
      const nextKf = animation.keyframes[idx + 1];
      return currentTime >= kf.time && (!nextKf || currentTime < nextKf.time);
    }
  );
  
  // Safety check: if essential data is missing, don't render
  if (!animation || !locations || !animation.keyframes) {
    return null;
  }

  return (
    <Canvas
      camera={{ position: [0, 15, 15], fov: 60 }}
      style={{ background: '#f3f4f6' }}
    >
      {/* Lighting - adjusted for light theme */}
      <ambientLight intensity={0.8} />
      <directionalLight position={[10, 10, 5]} intensity={1.2} castShadow />
      <pointLight position={[-10, 10, -10]} intensity={0.6} color="#60a5fa" />

      {/* Ground plane - light colored */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
        <planeGeometry args={[50, 50]} />
        <meshStandardMaterial color="#e5e7eb" />
      </mesh>

      {/* Grid - subtle for light theme */}
      <gridHelper args={[50, 50, '#d1d5db', '#e5e7eb']} position={[0, -0.49, 0]} />

      {/* Process locations */}
      {locations.map((loc, idx) => (
        <Location
          key={idx}
          position={loc.position}
          label={loc.label}
          isActive={activeLocation && activeLocation.event === loc.name}
        />
      ))}

      {/* Supplier locations */}
      {supplier_locations.map((supplier, idx) => (
        <SupplierLocation
          key={idx}
          position={supplier.position}
          label={supplier.label}
          country={supplier.country}
        />
      ))}

      {/* Process path */}
      <ProcessPath keyframes={animation.keyframes} />

      {/* Animated order */}
      <AnimatedOrder
        keyframes={animation.keyframes}
        currentTime={currentTime}
      />

      {/* Animated items */}
      {item_paths.map((itemData, idx) => (
        <AnimatedItem
          key={idx}
          itemData={itemData}
          currentTime={currentTime}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={5}
        maxDistance={60}
        maxPolarAngle={Math.PI / 2.2}
      />
    </Canvas>
  );
}

export default Scene;
