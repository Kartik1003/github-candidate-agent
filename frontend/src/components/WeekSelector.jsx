import { useState } from "react"

const inputStyle = {
  width: "100%", padding: "9px 12px", borderRadius: "var(--border-radius)",
  border: "1px solid var(--border-ghost)", fontSize: 13,
  background: "var(--surface-high)", color: "var(--text-main)",
  fontFamily: "var(--font-body)", outline: "none", cursor: "pointer",
  colorScheme: "dark",
}

const labelStyle = {
  fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)",
  color: "var(--text-muted)", display: "block", marginBottom: 6,
  textTransform: "uppercase", letterSpacing: "1px",
}

const pillStyle = (active) => ({
  padding: "7px 14px", borderRadius: 6, fontSize: 12, cursor: "pointer",
  fontWeight: 600, border: `1px solid ${active ? "transparent" : "var(--border-ghost)"}`,
  background: active ? "linear-gradient(135deg, var(--primary-color), var(--primary-dim))" : "var(--surface-high)",
  color: active ? "#fff" : "var(--text-main)",
  boxShadow: active ? "0 4px 12px rgba(208, 149, 255, 0.3)" : "none",
})

export default function WeekSelector({ weeks, selected, onChange, dates, onDateSelect, onWeekRangeSelect }) {
  const [mode, setMode] = useState("quick") // "quick" | "date" | "week"
  const [pickedDate, setPickedDate] = useState("")
  const [pickedWeek, setPickedWeek] = useState("")

  const handleDateChange = (e) => {
    const d = e.target.value
    setPickedDate(d)
    if (d && onDateSelect) onDateSelect(d)
  }

  const handleWeekChange = (e) => {
    const w = e.target.value  // "2026-W18"
    setPickedWeek(w)
    if (w && onWeekRangeSelect) onWeekRangeSelect(w)
  }

  const handleQuickSelect = (w) => {
    setPickedDate("")
    setPickedWeek("")
    setMode("quick")
    onChange(w)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Mode Tabs */}
      <div style={{ display: "flex", gap: 6 }}>
        {[
          { key: "quick", label: "Quick" },
          { key: "date", label: "By Date" },
          { key: "week", label: "By Week" },
        ].map(m => (
          <button key={m.key} onClick={() => setMode(m.key)}
            style={{
              flex: 1, padding: "6px 0", borderRadius: 5, fontSize: 11,
              fontWeight: 700, cursor: "pointer", letterSpacing: "0.5px",
              background: mode === m.key ? "var(--surface-high)" : "transparent",
              color: mode === m.key ? "var(--primary-color)" : "var(--text-muted)",
              border: `1px solid ${mode === m.key ? "var(--border-ghost)" : "transparent"}`,
            }}>
            {m.label}
          </button>
        ))}
      </div>

      {/* Quick Select (existing week pills) */}
      {mode === "quick" && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="float-hover" onClick={() => handleQuickSelect("all")}
            style={pillStyle(selected === "all")}>
            All Time
          </button>
          {weeks.map(w => (
            <button key={w} className="float-hover" onClick={() => handleQuickSelect(w)}
              style={pillStyle(selected === w)}>
              {w}
            </button>
          ))}
          {weeks.length === 0 && (
            <span style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>
              No processing dates found
            </span>
          )}
        </div>
      )}

      {/* Date Picker */}
      {mode === "date" && (
        <div>
          <label style={labelStyle}>Select Date</label>
          <input type="date" value={pickedDate} onChange={handleDateChange}
            style={inputStyle} />
          {pickedDate && (
            <div style={{
              marginTop: 8, fontSize: 12, color: "var(--secondary-color)",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--secondary-color)" }} />
              Showing results for {pickedDate}
            </div>
          )}
        </div>
      )}

      {/* Week Picker */}
      {mode === "week" && (
        <div>
          <label style={labelStyle}>Select Week</label>
          <input type="week" value={pickedWeek} onChange={handleWeekChange}
            style={inputStyle} />
          {pickedWeek && (
            <div style={{
              marginTop: 8, fontSize: 12, color: "var(--secondary-color)",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--secondary-color)" }} />
              Showing results for {pickedWeek}
            </div>
          )}
        </div>
      )}
    </div>
  )
}