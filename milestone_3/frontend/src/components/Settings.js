import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const defaultSettings = {
  displayName: "Recruiter Admin",
  email: "recruiter@talash.com",
  timezone: "Asia/Karachi",
  defaultView: "/",
  notifyEmail: true,
  notifyDigest: true,
  strictValidation: false,
  autoEmail: true,
};

export default function Settings() {
  const { auth = {} } = useAuth();
  const [status, setStatus] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState(defaultSettings);
  const [initialData, setInitialData] = useState(defaultSettings);

useEffect(() => {
    if (!auth || auth.loading) {
      return;
    }

    const email = auth.email
      ?? (typeof auth.user === "string"
        ? auth.user.includes("@")
          ? auth.user
          : `${auth.user}@talash.com`
        : defaultSettings.email);

    const displayName = auth.display_name ?? auth.displayName ?? defaultSettings.displayName;

    const synced = {
      ...defaultSettings,
      displayName,
      email,
    };

    setFormData(synced);
    setInitialData(synced);
  }, [auth]);

  const handleSave = () => {
    setStatus("");
    setIsSaving(true);

    setTimeout(() => {
      setIsSaving(false);
      setStatus("Settings updated successfully.");
      setInitialData(formData);
    }, 800);
  };

  const handleReset = () => {
    setFormData(initialData);
    setStatus("");
  };

  return (
    <div className="page-stack">
      <div className="dashboard-header">
        <div>
          <h2 className="page-title">Settings</h2>
          <p className="page-subtitle">Manage profile, roles, and notification preferences</p>
        </div>
        <Link className="primary-button" to="/">Back to dashboard</Link>
      </div>

      <section className="panel">
        <div className="panel-header"><h3>SETTINGS CONFIGURATION</h3></div>
        <div className="settings-panel">
          <h3 style={{ margin: "0 0 16px", color: "#0f1b2d", letterSpacing: "0.12em", fontSize: "0.75rem" }}>
            Profile Preferences
          </h3>

          <div className="settings-grid">
          <div className="settings-field">
            <label htmlFor="displayName">Display Name</label>
            <input
              id="displayName"
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
            />
          </div>
          <div className="settings-field">
            <label htmlFor="emailAddress">Work Email</label>
            <input
              id="emailAddress"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div className="settings-field">
            <label htmlFor="timezone">Timezone</label>
            <select
              id="timezone"
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
            >
              <option value="Asia/Karachi">Asia/Karachi</option>
              <option value="UTC">UTC</option>
              <option value="Europe/London">Europe/London</option>
            </select>
          </div>
          <div className="settings-field">
            <label htmlFor="defaultView">Default Landing Page</label>
            <select
              id="defaultView"
              value={formData.defaultView}
              onChange={(e) => setFormData({ ...formData, defaultView: e.target.value })}
            >
              <option value="/">Dashboard</option>
              <option value="/candidates">Candidates</option>
              <option value="/reports">Reports</option>
            </select>
          </div>
        </div>

        <div className="settings-toggle-row">
          <label className="settings-toggle">
            <input type="checkbox" checked={formData.notifyEmail} onChange={() => setFormData({ ...formData, notifyEmail: !formData.notifyEmail })} />
            <span>Email alerts for flagged candidates</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" checked={formData.notifyDigest} onChange={() => setFormData({ ...formData, notifyDigest: !formData.notifyDigest })} />
            <span>Daily summary digest</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" checked={formData.strictValidation} onChange={() => setFormData({ ...formData, strictValidation: !formData.strictValidation })} />
            <span>Strict profile validation mode</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" checked={formData.autoEmail} onChange={() => setFormData({ ...formData, autoEmail: !formData.autoEmail })} />
            <span>Auto-generate missing info emails</span>
          </label>
        </div>

        <div className="header-actions" style={{ marginTop: "16px" }}>
            <button type="button" className="primary-button" onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Settings"}
            </button>
            <button type="button" className="secondary-button" onClick={handleReset}>
              Reset
            </button>
          </div>

          <p className="status-msg">{status}</p>
        </div>
      </section>
    </div>
  );
}