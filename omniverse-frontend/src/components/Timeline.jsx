import { useState } from 'react';
import './Timeline.css';

function Timeline({ duration, currentTime, isPlaying, playbackSpeed = 1, onTimeChange, onPlayPause, onReset, onSpeedChange, keyframes }) {
  const [isDragging, setIsDragging] = useState(false);
  
  const speedOptions = [0.5, 1, 2, 4, 8];
  
  // Scale keyframe times to match 60-second duration
  const originalDuration = keyframes && keyframes.length > 0 ? 
    keyframes[keyframes.length - 1].time : duration;
  const timeScale = originalDuration / duration;
  
  const scaledKeyframes = keyframes.map(kf => ({
    ...kf,
    scaledTime: kf.time / timeScale
  }));
  
  const handleSpeedClick = () => {
    const currentIndex = speedOptions.indexOf(playbackSpeed);
    const nextIndex = (currentIndex + 1) % speedOptions.length;
    onSpeedChange(speedOptions[nextIndex]);
  };

  const handleSliderChange = (e) => {
    onTimeChange(parseFloat(e.target.value));
  };

  const handleSliderMouseDown = () => {
    setIsDragging(true);
  };

  const handleSliderMouseUp = () => {
    setIsDragging(false);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCurrentEvent = () => {
    if (!scaledKeyframes || scaledKeyframes.length === 0) return null;

    for (let i = scaledKeyframes.length - 1; i >= 0; i--) {
      if (currentTime >= scaledKeyframes[i].scaledTime) {
        return scaledKeyframes[i];
      }
    }
    return scaledKeyframes[0];
  };

  const currentEvent = getCurrentEvent();

  return (
    <div className="timeline-container">
      <div className="timeline-header">
        <div className="current-event">
          {currentEvent && (
            <>
              <span className="event-label">Current Event:</span>
              <span className="event-name">{currentEvent.label}</span>
              <span className="event-time">{new Date(currentEvent.timestamp).toLocaleTimeString()}</span>
            </>
          )}
        </div>
      </div>

      <div className="timeline-controls">
        <button className="control-btn reset-btn" onClick={onReset} title="Reset to Start">
          ⏮
        </button>
        <button className="control-btn play-pause-btn" onClick={onPlayPause} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button className="control-btn speed-btn" onClick={handleSpeedClick} title="Change Playback Speed">
          {playbackSpeed}×
        </button>
        <div className="time-display">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      <div className="timeline-slider-container">
        <input
          type="range"
          min="0"
          max={duration}
          step="0.1"
          value={currentTime}
          onChange={handleSliderChange}
          onMouseDown={handleSliderMouseDown}
          onMouseUp={handleSliderMouseUp}
          onTouchStart={handleSliderMouseDown}
          onTouchEnd={handleSliderMouseUp}
          className="timeline-slider"
        />
        
        {/* Keyframe markers */}
        <div className="keyframe-markers">
          {scaledKeyframes.map((kf, idx) => (
            <div
              key={idx}
              className="keyframe-marker"
              style={{
                left: `${(kf.scaledTime / duration) * 100}%`,
              }}
              title={`${kf.label} - ${new Date(kf.timestamp).toLocaleTimeString()}`}
            />
          ))}
        </div>
      </div>

      <div className="timeline-events">
        {scaledKeyframes.map((kf, idx) => (
          <div
            key={idx}
            className={`timeline-event ${currentTime >= kf.scaledTime ? 'completed' : ''} ${
              currentEvent && currentEvent.time === kf.time ? 'active' : ''
            }`}
            onClick={() => onTimeChange(kf.scaledTime)}
            title={`Jump to ${kf.label}`}
          >
            <div className="event-dot"></div>
            <div className="event-info">
              <span className="event-label-small">{kf.label}</span>
              <span className="event-time-small">{formatTime(kf.scaledTime)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Timeline;

