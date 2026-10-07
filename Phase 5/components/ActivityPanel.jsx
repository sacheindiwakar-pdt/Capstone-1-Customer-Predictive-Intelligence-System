function ActivityPanel({ peakHour, totalActivity }) {
  const bars = [32, 45, 38, 56, 48, 68, 61, 76, 58, 84, 72, 91];

  return (
    <div className="panel activity-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">NETWORK ACTIVITY</div>
          <h2>Traffic Intensity</h2>
        </div>

        <div className="live-badge">
          <span></span>
          DATA AVAILABLE
        </div>
      </div>

      <div className="activity-summary">
        <div>
          <span>Total Activity</span>
          <strong>{totalActivity}</strong>
        </div>

        <div className="peak-highlight">
          <span>Peak Period</span>
          <strong>{peakHour}</strong>
        </div>
      </div>

      <div className="activity-chart">
        {bars.map((height, index) => (
          <div className="bar-wrapper" key={index}>
            <div
              className="activity-bar"
              style={{ height: `${height}%` }}
            >
              <span></span>
            </div>

            <small>{index * 2}:00</small>
          </div>
        ))}
      </div>

      <div className="chart-footer">
        <span>Activity intensity visualization</span>
        <span>Peak: {peakHour}</span>
      </div>
    </div>
  );
}

export default ActivityPanel;