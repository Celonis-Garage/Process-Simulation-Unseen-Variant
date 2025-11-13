import { useState, useEffect, useRef } from 'react';
import './NarrationBox.css';

function NarrationBox({ currentEvent, sceneData, currentTime }) {
  const [narration, setNarration] = useState('Starting simulation...');
  const [isLoading, setIsLoading] = useState(false);
  const [displayText, setDisplayText] = useState('');
  const previousEventRef = useRef(null);
  const typingIntervalRef = useRef(null);

  // Fetch narration from backend when event changes
  useEffect(() => {
    if (!currentEvent || !sceneData) return;

    // Only fetch new narration if the event actually changed
    if (previousEventRef.current?.event === currentEvent.event) {
      return;
    }

    previousEventRef.current = currentEvent;
    fetchNarration(currentEvent, sceneData);
  }, [currentEvent, sceneData]);

  // Typewriter effect for displaying narration
  useEffect(() => {
    if (narration) {
      setDisplayText('');
      let currentIndex = 0;
      
      // Clear any existing interval
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
      }

      // Typing speed (milliseconds per character)
      const typingSpeed = 20;
      
      typingIntervalRef.current = setInterval(() => {
        if (currentIndex < narration.length) {
          setDisplayText(narration.slice(0, currentIndex + 1));
          currentIndex++;
        } else {
          clearInterval(typingIntervalRef.current);
        }
      }, typingSpeed);

      return () => {
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current);
        }
      };
    }
  }, [narration]);

  const fetchNarration = async (event, scene) => {
    setIsLoading(true);

    try {
      // Extract event-specific data for narration
      // Only send the user who performed THIS event, not all users
      const eventUser = event.user || (scene.entities?.users?.[0] || 'System');
      
      // For items and suppliers, only mention if relevant to this specific event
      const isItemRelevant = ['Generate Pick List', 'Pack Items', 'Ship Order', 'Receive Customer Order'].includes(event.event || event.label);
      const isSupplierRelevant = ['Approve Order', 'Schedule Order Fulfillment', 'Generate Pick List'].includes(event.event || event.label);
      
      const eventData = {
        event_name: event.event || event.label,
        timestamp: event.timestamp,
        case_id: scene.case_id,
        order_value: scene.order_info?.order_value,
        order_status: scene.order_info?.order_status,
        user: eventUser, // Single user, not array
        items: isItemRelevant ? (scene.entities?.items || []) : [],
        suppliers: isSupplierRelevant ? (scene.entities?.suppliers || []) : [],
        variant_id: scene.variant_id,
        current_time: currentTime
      };

      const response = await fetch('http://localhost:8000/api/narration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch narration: ${response.status}`);
      }

      const data = await response.json();
      setNarration(data.narration);
    } catch (error) {
      console.error('Error fetching narration:', error);
      // Fallback narration in bullet format
      const eventUser = event.user || 'System';
      setNarration(
        `• Action: ${event.event || event.label}\n` +
        `• By: ${eventUser}`
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="narration-box">
      <div className="narration-header">
        <span className="narration-title">Process Updates</span>
        {isLoading && <span className="narration-loading">●</span>}
      </div>
      <div className="narration-content">
        <div className="narration-text">
          {displayText}
          {displayText.length < narration.length && (
            <span className="typing-cursor">|</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default NarrationBox;

