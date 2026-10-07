import { Fragment } from "react";
import { NavLink } from "react-router-dom";

import {
  LayoutDashboard,
  Activity,
  Bell,
  Grid3X3,
  ShieldAlert,
  Settings2,
  Radio,
  ChevronRight,
} from "lucide-react";

function Sidebar() {
  const links = [
    {
      path: "/",
      label: "Network Overview",
      icon: LayoutDashboard,
    },
    {
      path: "/network-health",
      label: "Network Health",
      icon: Activity,
    },
    {
      path: "/alerts",
      label: "Alerts & Events",
      icon: Bell,
    },
    {
      path: "/risk",
      label: "Risk Intelligence",
      icon: ShieldAlert,
    },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <Radio size={22} />
        </div>

        <div>
          <div className="brand-title">TELECOM NOC</div>
          <div className="brand-subtitle">Intelligence System</div>
        </div>
      </div>

      <div className="sidebar-section-title">
        COMMAND CENTER
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => {
          const Icon = link.icon;

          return (
            <Fragment key={link.path}>
              <NavLink
                to={link.path}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={19} />
                <span>{link.label}</span>
                <ChevronRight
                  className="nav-arrow"
                  size={15}
                />
              </NavLink>
            </Fragment>
          );
        })}

        <NavLink
          to="/grid"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Grid3X3 size={18} />
          <span>Grid Explorer</span>
          <ChevronRight
            className="nav-arrow"
            size={15}
          />
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <strong>System Online</strong>
            <small>All services operational</small>
          </div>
        </div>

        <div className="version">
          NEXUS NOC
          <span>v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;