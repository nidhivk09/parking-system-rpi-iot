// src/App.js
import React, { useEffect, useState } from "react";
import { ref, onValue } from "firebase/database";
import { database } from "./firebase";
import "./App.css";

// ── Icons (inline SVG to avoid dependencies) ─────────────────
const CarIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
    <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/>
  </svg>
);

const PulseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
);

// ── Slot Card Component ───────────────────────────────────────
function SlotCard({ slotId, data, index }) {
  const occupied = data?.occupied ?? false;
  const distance = data?.distance_cm ?? "—";
  const label = data?.label ?? slotId;

  return (
    <div
      className={`slot-card ${occupied ? "occupied" : "available"}`}
      style={{ "--delay": `${index * 0.08}s` }}
    >
      <div className="slot-header">
        <span className="slot-label">{label}</span>
        <span className={`slot-badge ${occupied ? "badge-occupied" : "badge-available"}`}>
          {occupied ? "Occupied" : "Available"}
        </span>
      </div>

      <div className="slot-visual">
        <div className={`slot-icon-wrap ${occupied ? "icon-occupied" : "icon-available"}`}>
          <CarIcon />
        </div>
        {!occupied && <div className="pulse-ring" />}
      </div>

      <div className="slot-meta">
        <div className="meta-item">
          <span className="meta-label">Distance</span>
          <span className="meta-value">
            {distance !== "—" ? `${distance} cm` : "—"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Status</span>
          <span className={`meta-value ${occupied ? "text-red" : "text-green"}`}>
            {occupied ? "● In Use" : "● Free"}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Summary Bar ───────────────────────────────────────────────
function SummaryBar({ summary }) {
  const total = summary?.total ?? 0;
  const available = summary?.available ?? 0;
  const occupied = summary?.occupied ?? 0;
  const fillPercent = total > 0 ? (occupied / total) * 100 : 0;

  return (
    <div className="summary-bar">
      <div className="summary-stats">
        <div className="stat-block">
          <span className="stat-num available-color">{available}</span>
          <span className="stat-label">Available</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-block">
          <span className="stat-num occupied-color">{occupied}</span>
          <span className="stat-label">Occupied</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-block">
          <span className="stat-num">{total}</span>
          <span className="stat-label">Total</span>
        </div>
      </div>
      <div className="fill-bar-wrap">
        <div className="fill-bar-label">
          <span>Occupancy</span>
          <span>{Math.round(fillPercent)}%</span>
        </div>
        <div className="fill-bar-track">
          <div
            className={`fill-bar-fill ${fillPercent > 75 ? "fill-high" : fillPercent > 40 ? "fill-mid" : "fill-low"}`}
            style={{ width: `${fillPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────
function App() {
  const [parkingData, setParkingData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const parkingRef = ref(database, "parking");

    const unsubscribe = onValue(
      parkingRef,
      (snapshot) => {
        const data = snapshot.val();
        setConnected(true);
        setLastUpdated(new Date());
        setError(null);
        if (data) {
          setParkingData(data);
        } else {
          // No data yet - set empty structure
          setParkingData({ slots: {}, summary: { total: 0, available: 0, occupied: 0 } });
        }
      },
      (err) => {
        console.error("Firebase error:", err);
        setError("Unable to connect to database.");
        setConnected(false);
      }
    );

    return () => unsubscribe();
  }, []);

  const slots = parkingData?.slots ?? {};
  const summary = parkingData?.summary ?? {};

  const formatTime = (date) => {
    if (!date) return "—";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="brand-icon">P</div>
            <div>
              <h1 className="brand-title">SmartPark</h1>
              <p className="brand-sub">Live Parking Monitor</p>
            </div>
          </div>
          <div className="header-status">
            <span className={`live-dot ${connected ? "dot-live" : "dot-offline"}`} />
            <span className="live-label">{connected ? "Live" : "Offline"}</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        {/* Error State */}
        {error && (
          <div className="error-banner">
            ⚠ {error} — Check your Firebase config in <code>.env</code>
          </div>
        )}

        {/* Loading State */}
        {!parkingData && !error && (
          <div className="loading-wrap">
            <div className="loading-spinner" />
            <p>Connecting to parking sensors…</p>
          </div>
        )}

        {/* Data Loaded */}
        {parkingData && (
          <>
            <SummaryBar summary={summary} />

            <div className="section-title">
              <h2>Parking Slots</h2>
              <div className="last-updated">
                <PulseIcon />
                <span>Updated {formatTime(lastUpdated)}</span>
              </div>
            </div>

            <div className="slots-grid">
              {Object.keys(slots).length === 0 ? (
                <div className="no-slots-message">
                  <p>No parking slots configured yet.</p>
                  <p>Run the simulator: <code>cd raspberry-pi && python simulator.py</code></p>
                </div>
              ) : (
                Object.entries(slots).map(([slotId, data], idx) => (
                  <SlotCard key={slotId} slotId={slotId} data={data} index={idx} />
                ))
              )}
            </div>
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>SmartPark · Powered by Raspberry Pi + Firebase · Real-time sensor data</p>
      </footer>
    </div>
  );
}

export default App;
