import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-mark">T</div>
            <div>
              <h1>TALASH</h1>
              <p>Milestone 3</p>
            </div>
          </div>
          <nav className="nav-list">
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/candidates">Candidates</NavLink>
            <NavLink to="/analysis">Analysis</NavLink>
            <NavLink to="/reports">Reports</NavLink>
            <NavLink to="/settings">Settings</NavLink>
          </nav>
        </div>
        <div className="sidebar-footer">
          <span>{auth.display_name || auth.user}</span>
          <button className="ghost-button" onClick={handleLogout}>Sign out</button>
        </div>
      </aside>
      <main className="main-panel">
        <Outlet />
      </main>
    </div>
  );
}
