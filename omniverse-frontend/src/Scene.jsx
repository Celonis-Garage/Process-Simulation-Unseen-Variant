import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Sphere, Box, Line } from '@react-three/drei';
import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';

function OrderSphere({ position, label, itemsReceivedRatio }) {
  const meshRef = useRef();
  
  // Determine color based on items received
  const getColor = () => {
    if (itemsReceivedRatio >= 1.0) return '#10b981'; // Green - all items received
    if (itemsReceivedRatio > 0) return '#f59e0b'; // Amber/Yellow - partial
    return '#9ca3af'; // Gray - no items yet
  };
  
  useFrame((state) => {
    // Gentle floating animation
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  return (
    <group position={position}>
      <Sphere ref={meshRef} args={[0.4, 32, 32]}>
        <meshStandardMaterial 
          color={getColor()} 
          emissive={getColor()} 
          emissiveIntensity={0.3}
          metalness={0.3}
          roughness={0.4}
        />
      </Sphere>
    </group>
  );
}

function ItemSphere({ position, color }) {
  const meshRef = useRef();
  const size = 0.15; // Smaller than order sphere
  
  useFrame((state) => {
    // Gentle floating animation (slightly different from order)
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2.5 + Math.random()) * 0.08;
    }
  });

  return (
    <Sphere ref={meshRef} args={[size, 16, 16]} position={position}>
      <meshStandardMaterial 
        color={color} 
        emissive={color}
        emissiveIntensity={0.2}
        metalness={0.2}
        roughness={0.5}
      />
    </Sphere>
  );
}

// Station component with context-appropriate 3D shapes
function Location({ position, label, isActive, type }) {
  const isMain = type === 'main';
  
  // Determine station type from label
  const getStationType = (label) => {
    const labelLower = label.toLowerCase();
    if (labelLower.includes('receive') || labelLower.includes('customer') || labelLower.includes('order')) return 'reception';
    if (labelLower.includes('validate') || labelLower.includes('check')) return 'validation';
    if (labelLower.includes('credit') || labelLower.includes('approve')) return 'office';
    if (labelLower.includes('schedule') || labelLower.includes('fulfillment')) return 'planning';
    if (labelLower.includes('pick') || labelLower.includes('warehouse')) return 'warehouse';
    if (labelLower.includes('pack') || labelLower.includes('items')) return 'packing';
    if (labelLower.includes('ship') || labelLower.includes('label')) return 'shipping';
    if (labelLower.includes('invoice') || labelLower.includes('payment')) return 'accounting';
    if (labelLower.includes('reject')) return 'rejection';
    if (labelLower.includes('return')) return 'returns';
    if (labelLower.includes('discount')) return 'discount';
    return 'generic';
  };
  
  const stationType = getStationType(label);
  
  // Color scheme for different station types
  const getStationColor = () => {
    switch(stationType) {
      case 'reception': return '#6366f1'; // Indigo
      case 'validation': return '#8b5cf6'; // Purple
      case 'office': return '#0ea5e9'; // Sky blue
      case 'planning': return '#06b6d4'; // Cyan
      case 'warehouse': return '#10b981'; // Green
      case 'packing': return '#f59e0b'; // Amber
      case 'shipping': return '#ef4444'; // Red
      case 'accounting': return '#ec4899'; // Pink
      case 'rejection': return '#dc2626'; // Dark red
      case 'returns': return '#f97316'; // Orange
      case 'discount': return '#84cc16'; // Lime
      default: return '#6b7280'; // Gray
    }
  };
  
  const baseColor = getStationColor();
  const emissiveColor = isActive ? '#3b82f6' : baseColor;
  
  // Render different 3D shapes based on station type
  const renderStationShape = () => {
    const material = (
      <meshStandardMaterial 
        color={baseColor} 
        emissive={emissiveColor}
        emissiveIntensity={isActive ? 0.5 : 0.2}
        metalness={0.4}
        roughness={0.5}
      />
    );
    
    switch(stationType) {
      case 'reception':
        // Reception desk - flat box with a counter (3x scale)
        return (
          <>
            <Box args={[3.0, 0.9, 1.8]} position={[0, 0.45, 0]}>{material}</Box>
            <Box args={[2.4, 0.45, 1.5]} position={[0, 1.14, 0]}>{material}</Box>
          </>
        );
      
      case 'warehouse':
        // Warehouse - large building-like structure with shelving (3x scale)
        return (
          <>
            <Box args={[3.6, 2.4, 2.4]} position={[0, 1.2, 0]}>{material}</Box>
            <Box args={[3.0, 1.8, 0.9]} position={[0, 0.9, -0.9]}>{material}</Box>
            <Box args={[3.0, 1.8, 0.9]} position={[0, 0.9, 0.9]}>{material}</Box>
          </>
        );
      
      case 'packing':
        // Packing station - table with boxes on top (3x scale)
        return (
          <>
            <Box args={[3.0, 0.6, 1.8]} position={[0, 0.3, 0]}>{material}</Box>
            <Box args={[0.9, 0.9, 0.9]} position={[-0.6, 1.05, 0]}>{material}</Box>
            <Box args={[0.75, 0.75, 0.75]} position={[0.6, 0.99, 0.3]}>{material}</Box>
          </>
        );
      
      case 'shipping':
        // Shipping - truck/loading dock shape (3x scale)
        return (
          <>
            <Box args={[2.4, 1.5, 1.8]} position={[0, 0.75, 0]}>{material}</Box>
            <Box args={[1.2, 0.9, 1.2]} position={[1.5, 0.45, 0]}>{material}</Box>
          </>
        );
      
      case 'office':
      case 'validation':
        // Office desk - simple desk with monitor (3x scale)
        return (
          <>
            <Box args={[2.4, 0.6, 1.5]} position={[0, 0.3, 0]}>{material}</Box>
            <Box args={[0.9, 0.9, 0.15]} position={[0, 1.05, 0.3]}>{material}</Box>
          </>
        );
      
      case 'planning':
        // Planning station - desk with documents (flat boxes) (3x scale)
        return (
          <>
            <Box args={[2.7, 0.6, 1.8]} position={[0, 0.3, 0]}>{material}</Box>
            <Box args={[0.6, 0.06, 0.9]} position={[-0.6, 0.63, 0]}>{material}</Box>
            <Box args={[0.6, 0.06, 0.9]} position={[0.6, 0.63, 0]}>{material}</Box>
          </>
        );
      
      case 'accounting':
        // Accounting - computer workstation (3x scale)
        return (
          <>
            <Box args={[2.1, 0.6, 1.5]} position={[0, 0.3, 0]}>{material}</Box>
            <Box args={[1.2, 1.2, 0.15]} position={[0, 1.2, 0.3]}>{material}</Box>
            <Box args={[0.3, 0.6, 0.3]} position={[0, 0.9, -0.3]}>{material}</Box>
          </>
        );
      
      case 'rejection':
      case 'returns':
        // Returns/Rejection - cross or X-shape (3x scale)
        return (
          <>
            <Box args={[2.4, 0.6, 0.6]} position={[0, 0.9, 0]} rotation={[0, 0, Math.PI/4]}>{material}</Box>
            <Box args={[2.4, 0.6, 0.6]} position={[0, 0.9, 0]} rotation={[0, 0, -Math.PI/4]}>{material}</Box>
          </>
        );
      
      case 'discount':
        // Discount - star-like shape (3x scale)
        return (
          <>
            <Box args={[1.8, 0.9, 0.6]} position={[0, 0.9, 0]}>{material}</Box>
            <Box args={[0.6, 0.9, 1.8]} position={[0, 0.9, 0]}>{material}</Box>
          </>
        );
      
      default:
        // Generic - simple box (3x scale)
        return <Box args={[1.8, 1.8, 1.8]} position={[0, 0.9, 0]}>{material}</Box>;
    }
  };
  
  return (
    <group position={position}>
      {renderStationShape()}
      
      {/* Label below the station on ground plane (adjusted for 3x larger stations) */}
      <Text
        position={[0, 0.02, 2.5]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.7}
        color={isActive ? "#3b82f6" : "#1f2937"}
        anchorX="center"
        anchorY="middle"
        maxWidth={5.5}
        fontWeight="bold"
      >
        {label}
      </Text>
    </group>
  );
}

function SupplierLocation({ position, label, country }) {
  const supplierColor = '#10b981'; // Green for suppliers
  
  const material = (
    <meshStandardMaterial 
      color={supplierColor} 
      emissive={supplierColor}
      emissiveIntensity={0.25}
      metalness={0.3}
      roughness={0.6}
    />
  );
  
  return (
    <group position={position}>
      {/* Factory/Building structure - main building (3x scale) */}
      <Box args={[1.8, 1.2, 1.5]} position={[0, 0.6, 0]}>{material}</Box>
      
      {/* Chimney/Tower (3x scale) */}
      <Box args={[0.45, 0.9, 0.45]} position={[0.6, 1.65, 0.45]}>{material}</Box>
      
      {/* Side wing (3x scale) */}
      <Box args={[0.9, 0.75, 1.2]} position={[-1.05, 0.375, 0]}>{material}</Box>
      
      {/* Loading dock (3x scale) */}
      <Box args={[1.2, 0.3, 0.6]} position={[0, 0.15, -1.05]}>{material}</Box>
      
      {/* Label on ground plane below the supplier (adjusted for 3x scale) */}
      <Text
        position={[0, 0.02, 2.2]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.65}
        color="#059669"
        anchorX="center"
        anchorY="middle"
        maxWidth={5.0}
        fontWeight="bold"
      >
        {label}
      </Text>
    </group>
  );
}

// L-shaped path for deviations
function LShapedPath({ start, end, color }) {
  // Create L-shape: start -> corner -> end
  const corner = [end[0], start[1], start[2]]; // Horizontal first, then vertical
  const points = [
    new THREE.Vector3(...start),
    new THREE.Vector3(...corner),
    new THREE.Vector3(...end)
  ];
  
  return (
    <Line
      points={points}
      color={color}
      lineWidth={2}
      dashed={true}
      dashScale={0.5}
      dashSize={0.1}
      gapSize={0.1}
    />
  );
}

// Progressive path for supplier connections - shows only traveled portion
function DiagonalPath({ start, end, color, progress = 1 }) {
  // Ensure we have valid points
  if (!start || !end || start.length < 3 || end.length < 3) return null;
  
  const startVec = new THREE.Vector3(...start);
  const endVec = new THREE.Vector3(...end);
  
  // Clamp progress to valid range
  const clampedProgress = Math.min(1, Math.max(0.01, progress)); // Minimum 0.01 to ensure visibility
  
  // Interpolate to show only the traveled portion
  const currentEnd = new THREE.Vector3().lerpVectors(startVec, endVec, clampedProgress);
  
  const points = [startVec, currentEnd];
  
  return (
    <Line
      points={points}
      color={color}
      lineWidth={4}
      dashed={false}
      opacity={0.9}
      transparent={true}
    />
  );
}

// Progressive path for main order - shows only traveled portion
function ProcessPath({ keyframes, currentTime }) {
  if (!keyframes || keyframes.length < 2) return null;

  // Build progressive path based on current time
  const traveledPoints = [];
  
  // Always start with first point if animation has started
  if (currentTime > 0) {
    traveledPoints.push(new THREE.Vector3(...keyframes[0].position));
  }
  
  for (let i = 0; i < keyframes.length - 1; i++) {
    const curr = keyframes[i];
    const next = keyframes[i + 1];
    
    if (currentTime > curr.time) {
      // Already passed this point
      if (i > 0) { // Don't add first point twice
        traveledPoints.push(new THREE.Vector3(...curr.position));
      }
      
      if (currentTime < next.time) {
        // Currently between curr and next - interpolate
        const t = (currentTime - curr.time) / (next.time - curr.time);
        const interpPos = [
          curr.position[0] + (next.position[0] - curr.position[0]) * t,
          curr.position[1] + (next.position[1] - curr.position[1]) * t,
          curr.position[2] + (next.position[2] - curr.position[2]) * t,
        ];
        traveledPoints.push(new THREE.Vector3(...interpPos));
        break;
      }
    }
  }
  
  // Add final point if animation complete
  if (currentTime >= keyframes[keyframes.length - 1].time) {
    traveledPoints.push(new THREE.Vector3(...keyframes[keyframes.length - 1].position));
  }
  
  // Need at least 2 points to draw a line
  if (traveledPoints.length < 2) return null;
  
  return (
    <Line
      points={traveledPoints}
      color="#ea580c"
      lineWidth={5}
      dashed={false}
      opacity={1}
    />
  );
}

function AnimatedOrder({ keyframes, currentTime, itemsReceivedRatio }) {
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

  return <OrderSphere position={position} label={currentEvent} itemsReceivedRatio={itemsReceivedRatio} />;
}

function AnimatedItemInstance({ itemData, instanceIndex, totalInstances, currentTime }) {
  const [position, setPosition] = useState([0, 0, 0]);
  const [showItem, setShowItem] = useState(false);

  // Add slight offset for multiple instances of same item
  const offset = instanceIndex - (totalInstances - 1) / 2;
  const xOffset = offset * 0.3;
  // Stagger departure for each instance - increased to 5 seconds for clear separation
  const instanceDelay = instanceIndex * 5; // 5 seconds between each sphere

  useEffect(() => {
    if (!itemData || !itemData.keyframes || itemData.keyframes.length === 0) return;

    const keyframes = itemData.keyframes;
    let prevKeyframe = keyframes[0];
    let nextKeyframe = keyframes[0];

    // Adjust times for this instance
    const adjustedTime = currentTime - instanceDelay;

    for (let i = 0; i < keyframes.length; i++) {
      if (keyframes[i].time <= adjustedTime) {
        prevKeyframe = keyframes[i];
        nextKeyframe = keyframes[i + 1] || keyframes[i];
      } else {
        break;
      }
    }

    // Hide item after it merges with order
    if (prevKeyframe.status === 'merged') {
      setShowItem(false);
      return;
    }

    // Show item when it starts moving
    setShowItem(prevKeyframe.status !== 'waiting' || adjustedTime > keyframes[1]?.time);

    // Interpolate between keyframes
    if (prevKeyframe.time === nextKeyframe.time) {
      setPosition([prevKeyframe.position[0] + xOffset, prevKeyframe.position[1], prevKeyframe.position[2]]);
    } else {
      const t = (adjustedTime - prevKeyframe.time) / (nextKeyframe.time - prevKeyframe.time);
      const smoothT = Math.min(1, Math.max(0, t));

      const interpolatedPos = [
        prevKeyframe.position[0] + (nextKeyframe.position[0] - prevKeyframe.position[0]) * smoothT + xOffset,
        prevKeyframe.position[1] + (nextKeyframe.position[1] - prevKeyframe.position[1]) * smoothT,
        prevKeyframe.position[2] + (nextKeyframe.position[2] - prevKeyframe.position[2]) * smoothT,
      ];

      setPosition(interpolatedPos);
    }
  }, [currentTime, itemData, xOffset, instanceDelay]);

  if (!showItem || !itemData) return null;

  return <ItemSphere position={position} color={itemData.color} />;
}

function AnimatedItem({ itemData, currentTime }) {
  if (!itemData) return null;

  const quantity = itemData.quantity || 1;
  
  // Calculate path progress based on first instance
  let pathProgress = 0;
  if (itemData.keyframes && itemData.keyframes.length >= 3) {
    const startTime = itemData.keyframes[1].time; // departure time
    const endTime = itemData.keyframes[2].time; // arrival time
    
    if (currentTime >= startTime) {
      if (currentTime >= endTime) {
        pathProgress = 1;
      } else {
        pathProgress = (currentTime - startTime) / (endTime - startTime);
      }
    }
  }
  
  // Create multiple spheres based on quantity
  const instances = [];
  for (let i = 0; i < quantity; i++) {
    instances.push(
      <AnimatedItemInstance 
        key={i}
        itemData={itemData}
        instanceIndex={i}
        totalInstances={quantity}
        currentTime={currentTime}
      />
    );
  }

  return (
    <>
      {/* Draw progressive path from supplier to warehouse */}
      {itemData.keyframes && itemData.keyframes.length >= 3 && pathProgress >= 0.01 && (
        <DiagonalPath 
          start={itemData.keyframes[0].position}
          end={itemData.keyframes[2].position}
          color={itemData.color}
          progress={pathProgress}
        />
      )}
      {instances}
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

  // Scale animation to 60 seconds total (from original duration)
  const TARGET_DURATION = 60; // 60 seconds
  const originalDuration = animation?.duration || 660;
  const timeScale = originalDuration / TARGET_DURATION;

  // Scale current time to original timeline for calculations
  const scaledCurrentTime = currentTime * timeScale;

  useEffect(() => {
    if (!isPlaying || !animation) return;

    const interval = setInterval(() => {
      onTimeUpdate((prev) => {
        const next = prev + (0.1 * playbackSpeed);
        return next >= TARGET_DURATION ? 0 : next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, animation, onTimeUpdate]);

  // Calculate items received ratio (for order sphere color)
  const calculateItemsReceivedRatio = () => {
    if (!item_paths || item_paths.length === 0) return 0;
    
    const packTime = animation?.keyframes?.find(kf => kf.event === 'Pack Items')?.time || Infinity;
    
    if (scaledCurrentTime >= packTime) return 1.0; // All items received at pack time
    
    let receivedCount = 0;
    item_paths.forEach(item => {
      const arrivalTime = item.keyframes?.find(kf => kf.status === 'arrived')?.time;
      if (arrivalTime && scaledCurrentTime >= arrivalTime) {
        receivedCount++;
      }
    });
    
    return receivedCount / item_paths.length;
  };

  const itemsReceivedRatio = calculateItemsReceivedRatio();

  // Determine active location based on current time
  const activeLocation = animation?.keyframes?.find(
    (kf, idx) => {
      const nextKf = animation.keyframes[idx + 1];
      return scaledCurrentTime >= kf.time && (!nextKf || scaledCurrentTime < nextKf.time);
    }
  );
  
  // Safety check: if essential data is missing, don't render
  if (!animation || !locations || !animation.keyframes) {
    return null;
  }

  return (
    <Canvas
      camera={{ position: [0, 35, 30], fov: 70 }}
      style={{ background: '#f3f4f6' }}
    >
      {/* Lighting - adjusted for light theme */}
      <ambientLight intensity={0.9} />
      <directionalLight position={[10, 15, 5]} intensity={1.3} castShadow />
      <pointLight position={[-10, 10, -10]} intensity={0.5} color="#60a5fa" />

      {/* Ground plane - wider to accommodate 2x spacing */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[120, 50]} />
        <meshStandardMaterial color="#f0f0f0" />
      </mesh>

      {/* Grid - wider and more divisions */}
      <gridHelper args={[120, 60, '#cccccc', '#e0e0e0']} position={[0, 0.01, 0]} />

      {/* Process locations */}
      {locations.map((loc, idx) => (
        <Location
          key={idx}
          position={loc.position}
          label={loc.label}
          type={loc.type}
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

      {/* Process path - progressive */}
      <ProcessPath keyframes={animation.keyframes} currentTime={scaledCurrentTime} />

      {/* Animated order */}
      <AnimatedOrder
        keyframes={animation.keyframes}
        currentTime={scaledCurrentTime}
        itemsReceivedRatio={itemsReceivedRatio}
      />

      {/* Animated items */}
      {item_paths.map((itemData, idx) => (
        <AnimatedItem
          key={idx}
          itemData={itemData}
          currentTime={scaledCurrentTime}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={10}
        maxDistance={80}
        maxPolarAngle={Math.PI / 2.2}
      />
    </Canvas>
  );
}

export default Scene;
