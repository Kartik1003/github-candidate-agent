import { useState, useEffect } from "react"

const STORAGE_KEY = "candidate_agent_filter_presets"

export default function SavedFilters({ currentFilters, onLoad }) {
  const [presets, setPresets] = useState([])
  const [newName, setNewName] = useState("")
  const [showInput, setShowInput] = useState(false)

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")
      setPresets(stored)
    } catch { setPresets([]) }
  }, [])

  const save = () => {
    const name = newName.trim()
    if (!name) return
    const preset = { name, filters: currentFilters, savedAt: new Date().toISOString() }
    const updated = [preset, ...presets.filter(p => p.name !== name)]
    setPresets(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    setNewName("")
    setShowInput(false)
  }

  const remove = (name) => {
    const updated = presets.filter(p => p.name !== name)
    setPresets(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const summarise = (filters) => {
    const parts = []
    if (filters.domain) parts.push(filters.domain.replace(/_/g, " "))
    if (filters.min_score > 0) parts.push(`≥${Math.round(filters.min_score * 100)}%`)
    if (filters.has_linkedin) parts.push("LinkedIn")
    if (filters.has_cv) parts.push("CV")
    return parts.length > 0 ? parts.join(" · ") : "All candidates"
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <label style={{ fontSize: 11, fontWeight: 700, fontFamily: "var(--font-display)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>
          Saved Presets
        </label>
        <button
          onClick={() => setShowInput(!showInput)}
          style={{ fontSize: 11, padding: "4px 10px", borderRadius: 5, background: "var(--surface-high)", color: "var(--primary-color)", border: "1px solid rgba(208,149,255,0.3)", fontWeight: 600, cursor: "pointer" }}
        >
          💾 Save Current
        </button>
      </div>

      {showInput && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <input
            type="text"
            placeholder="Preset name..."
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === "Enter" && save()}
            autoFocus
            style={{ flex: 1, padding: "8px 12px", borderRadius: 6, border: "1px solid var(--border-ghost)", background: "var(--surface-high)", color: "var(--text-main)", fontSize: 12, fontFamily: "var(--font-body)", outline: "none" }}
          />
          <button
            onClick={save}
            style={{ padding: "8px 14px", borderRadius: 6, background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "#fff", fontWeight: 700, fontSize: 12, cursor: "pointer" }}
          >
            ✓
          </button>
        </div>
      )}

      {presets.length === 0 ? (
        <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "12px 0" }}>
          No presets saved yet
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {presets.map(p => (
            <div
              key={p.name}
              className="float-hover"
              style={{ padding: "10px 12px", borderRadius: 6, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", cursor: "pointer" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }} onClick={() => onLoad(p.filters)}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-main)", marginBottom: 2 }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{summarise(p.filters)}</div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); remove(p.name) }}
                  style={{ fontSize: 11, padding: "2px 7px", borderRadius: 4, background: "transparent", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", cursor: "pointer", marginLeft: 8 }}
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
