import {
  Activity,
  Clock3,
  Grid3X3,
  Trophy,
} from "lucide-react";

const icons = {
  activity: Activity,
  peak: Clock3,
  grids: Grid3X3,
  highest: Trophy,
};

function StatusCard({
  title,
  value,
  description,
  type,
  accent,
}) {
  const Icon = icons[type] || Activity;

  return (
    <div className={`metric-card ${accent}`}>
      <div className="metric-card-top">
        <div className="metric-icon">
          <Icon size={20} />
        </div>

        <span className="metric-label">{title}</span>
      </div>

      <div className="metric-value">{value}</div>

      <div className="metric-description">
        {description}
      </div>

      <div className="metric-line">
        <span></span>
      </div>
    </div>
  );
}

export default StatusCard;