import { useState, useRef } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"

const API = "http://localhost:8000"

const DOMAINS = [
  { value: "", label: "Any Domain" },
  { value: "backend", label: "Backend" },
  { value: "frontend", label: "Frontend" },
  { value: "ai_ml", label: "AI / ML" },
  { value: "devops", label: "DevOps" },
  { value: "mobile", label: "Mobile" },
  { value: "full_stack", label: "Full Stack" },
]

const PRESET_ROLES = [
  {
    title: "Python Backend Engineer",
    required: ["Python", "FastAPI", "PostgreSQL"],
    nice_to_have: ["Docker", "Redis", "TypeScript"],
    min_commits: 20, min_stars: 0, needs_tests: true, domain: "backend",
  },
  {
    title: "Frontend React Developer",
    required: ["React", "TypeScript", "JavaScript"],
    nice_to_have: ["Next.js", "Jest", "GraphQL"],
    min_commits: 15, min_stars: 0, needs_tests: false, domain: "frontend",
  },
  {
    title: "ML / AI Engineer",
    required: ["Python", "ML"],
    nice_to_have: ["TensorFlow", "PyTorch", "Docker", "SQL"],
    min_commits: 10, min_stars: 2, needs_tests: false, domain: "ai_ml",
  },
  {
    title: "DevOps / SRE",
    required: ["Docker", "GitHub Actions"],
    nice_to_have: ["Kubernetes", "Terraform", "Python"],
    min_commits: 10, min_stars: 0, needs_tests: false, domain: "devops",
  },
]

const MATCH_COLORS = {
  "Strong Match": "#1D9E75",
  "Good Fit":     "#40cef3",
  "Partial Fit":  "#E6A817",
  "Poor Fit":     "#E64D4D",
}

function TagInput({ label, tags, setTags, placeholder }) {
  const [val, setVal] = useState("")
  const addTag = (e) => {
    if ((e.key === "Enter" || e.key === ",") && val.trim()) {
      e.preventDefault()
      if (!tags.includes(val.trim())) setTags([...tags, val.trim()])
      setVal("")
    }
  }
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, display: "block", marginBottom: 8 }}>
        {label}
      </label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: "10px 12px", borderRadius: 8, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", minHeight: 44 }}>
        {tags.map(t => (
          <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 10px", borderRadius: 20, background: "rgba(208,149,255,0.12)", color: "var(--primary-color)", fontSize: 12, fontWeight: 600, border: "1px solid rgba(208,149,255,0.25)" }}>
            {t}
            <span onClick={() => setTags(tags.filter(x => x !== t))} style={{ cursor: "pointer", opacity: 0.7, fontSize: 14 }}>×</span>
          </span>
        ))}
        <input
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={addTag}
          placeholder={tags.length === 0 ? placeholder : "Add more..."}
          style={{ border: "none", background: "transparent", outline: "none", color: "var(--text-main)", fontSize: 13, flex: 1, minWidth: 100 }}
        />
      </div>
      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>Press Enter or comma to add</div>
    </div>
  )
}

function BreakdownBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{label}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color }}>{value}%</span>
      </div>
      <div style={{ height: 5, borderRadius: 3, background: "var(--surface-high)", overflow: "hidden" }}>
        <div style={{ width: `${value}%`, height: "100%", borderRadius: 3, background: color, transition: "width 0.5s ease" }} />
      </div>
    </div>
  )
}

export default function RoleFitPage() {
  const navigate = useNavigate()
  const [role, setRole]     = useState({ title: "", required: [], nice_to_have: [], min_commits: 0, min_stars: 0, needs_tests: false, domain: "", needs_live_project: false })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [error, setError] = useState(null)

  const applyPreset = (preset) => setRole({ ...role, ...preset, domain: preset.domain || "" })

  const run = async () => {
    if (!role.title) { setError("Please enter a role title"); return }
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const payload = { ...role, domain: role.domain || null }
      const res = await axios.post(`${API}/role-fit`, payload)
      setResults(res.data)
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to compute role fit")
    }
    setLoading(false)
  }

  const topResults = results?.candidates?.slice(0, 30) || []

  return (
    <div className="animate-in" style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button onClick={() => navigate("/")} style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}>← Back</button>
        <div>
          <h1 style={{ fontSize: 26 }}>🎯 Role-Fit <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>Scorer</span></h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>Define your job requirements → every candidate gets a % match score</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: results ? "380px 1fr" : "1fr", gap: 24 }}>
        {/* ── Left: Role Builder ── */}
        <div>
          <div className="glass-panel" style={{ padding: "24px" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 16 }}>⚡ Quick Presets</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
              {PRESET_ROLES.map(p => (
                <button key={p.title} onClick={() => applyPreset(p)} style={{ padding: "6px 12px", borderRadius: 6, fontSize: 12, fontWeight: 600, background: "rgba(64,206,243,0.08)", color: "var(--secondary-color)", border: "1px solid rgba(64,206,243,0.2)", cursor: "pointer" }}>
                  {p.title}
                </button>
              ))}
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: 1, display: "block", marginBottom: 8 }}>Role Title *</label>
              <input value={role.title} onChange={e => setRole({...role, title: e.target.value})}
                placeholder="e.g. Senior Backend Engineer"
                style={{ width: "100%", padding: "10px 12px", borderRadius: 8, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", color: "var(--text-main)", fontSize: 13, boxSizing: "border-box" }} />
            </div>

            <TagInput label="Required Skills *" tags={role.required} setTags={v => setRole({...role, required: v})} placeholder="Python, FastAPI, PostgreSQL..." />
            <TagInput label="Nice to Have" tags={role.nice_to_have} setTags={v => setRole({...role, nice_to_have: v})} placeholder="Docker, Redis..." />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>MIN COMMITS</label>
                <input type="number" min="0" value={role.min_commits} onChange={e => setRole({...role, min_commits: +e.target.value})}
                  style={{ width: "100%", padding: "8px 10px", borderRadius: 6, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", color: "var(--text-main)", fontSize: 13, boxSizing: "border-box" }} />
              </div>
              <div>
                <label style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>MIN STARS</label>
                <input type="number" min="0" value={role.min_stars} onChange={e => setRole({...role, min_stars: +e.target.value})}
                  style={{ width: "100%", padding: "8px 10px", borderRadius: 6, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", color: "var(--text-main)", fontSize: 13, boxSizing: "border-box" }} />
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>DOMAIN</label>
              <select value={role.domain} onChange={e => setRole({...role, domain: e.target.value})}
                style={{ width: "100%", padding: "9px 12px", borderRadius: 6, background: "var(--surface-high)", border: "1px solid var(--border-ghost)", color: "var(--text-main)", fontSize: 13 }}>
                {DOMAINS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>

            <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--text-main)", cursor: "pointer" }}>
                <input type="checkbox" checked={role.needs_tests} onChange={e => setRole({...role, needs_tests: e.target.checked})}
                  style={{ accentColor: "var(--primary-color)", width: 16, height: 16 }} />
                Must have tests
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--text-main)", cursor: "pointer" }}>
                <input type="checkbox" checked={role.needs_live_project} onChange={e => setRole({...role, needs_live_project: e.target.checked})}
                  style={{ accentColor: "var(--primary-color)", width: 16, height: 16 }} />
                Must have live project
              </label>
            </div>

            {error && <div style={{ padding: "10px 14px", borderRadius: 6, background: "rgba(230,77,77,0.1)", color: "#E64D4D", fontSize: 13, marginBottom: 12 }}>❌ {error}</div>}

            <button onClick={run} disabled={loading} style={{
              width: "100%", padding: "14px", borderRadius: 10, fontSize: 16, fontWeight: 800,
              background: loading ? "var(--surface-high)" : "linear-gradient(135deg, var(--primary-color), var(--primary-dim))",
              color: loading ? "var(--text-muted)" : "#fff", border: "none", cursor: loading ? "not-allowed" : "pointer",
              boxShadow: loading ? "none" : "0 4px 20px rgba(208,149,255,0.3)",
            }}>
              {loading ? "⏳ Scoring all candidates..." : "🎯 Score All Candidates"}
            </button>
          </div>
        </div>

        {/* ── Right: Results ── */}
        {results && (
          <div style={{ minWidth: 0 }}>

            {/* Summary header */}
            <div style={{ marginBottom: 18, display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
              <div>
                <div style={{ fontSize: 20, fontWeight: 800, color: "var(--text-main)", fontFamily: "var(--font-display)" }}>
                  {results.role.title}
                </div>
                <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 3 }}>
                  {results.count} candidates scored
                  {results.role.required?.length > 0 && ` · requires: ${results.role.required.join(", ")}`}
                </div>
              </div>
              {/* Summary pills */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {["Strong Match", "Good Fit", "Partial Fit", "Poor Fit"].map(l => {
                  const n = topResults.filter(c => c.role_fit?.match_label === l).length
                  if (!n) return null
                  const col = MATCH_COLORS[l]
                  return (
                    <div key={l} style={{ padding: "6px 14px", borderRadius: 20, background: `${col}15`, color: col, fontSize: 12, fontWeight: 700, border: `1px solid ${col}40` }}>
                      <span style={{ fontSize: 15, fontWeight: 900 }}>{n}</span> {l}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Candidate cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12, maxHeight: "calc(100vh - 240px)", overflowY: "auto", paddingRight: 6 }}>
              {topResults.map((c, idx) => {
                const fit   = c.role_fit || {}
                const color = MATCH_COLORS[fit.match_label] || "#888"
                const isExp = expanded === c.login
                const pct   = fit.match_pct ?? 0
                const circumference = 2 * Math.PI * 22

                return (
                  <div key={c.login} style={{
                    borderRadius: 10,
                    background: "#1c2028",
                    border: `1px solid ${isExp ? color : "rgba(69,72,79,0.4)"}`,
                    marginBottom: 2,
                    animation: `fadeIn 0.25s ease both ${idx * 0.025}s`,
                  }}>
                    {/* Match bar at top — full width track, colored fill */}
                    <div style={{ height: 4, background: "#22262f", borderRadius: "10px 10px 0 0" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: "10px 10px 0 0", transition: "width 0.6s ease" }} />
                    </div>

                    {/* Card body */}
                    <div style={{ padding: "14px 18px" }}>
                      {/* Row 1: % + Name + badge + buttons */}
                      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                        {/* Big percentage */}
                        <div style={{ minWidth: 52, textAlign: "center", flexShrink: 0 }}>
                          <div style={{ fontSize: 22, fontWeight: 900, color, lineHeight: 1, fontFamily: "'Space Grotesk', sans-serif" }}>{pct}%</div>
                          <div style={{ fontSize: 10, color: "#a9abb3", marginTop: 2 }}>#{idx + 1}</div>
                        </div>

                        {/* Name + handle + label */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                            <span style={{ fontSize: 15, fontWeight: 700, color: "#ecedf6" }}>{c.name || c.login}</span>
                            <span style={{ fontSize: 12, color: "#a9abb3" }}>@{c.login}</span>
                            <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 10px", borderRadius: 20, background: color + "20", color, border: `1px solid ${color}50` }}>
                              {fit.match_label}
                            </span>
                          </div>
                          {/* Skill tags row */}
                          <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginTop: 8 }}>
                            {(fit.matched || []).slice(0, 5).map(m => (
                              <span key={m} style={{ fontSize: 11, padding: "2px 8px", borderRadius: 20, fontWeight: 600, background: "rgba(29,158,117,0.12)", color: "#1D9E75", border: "1px solid rgba(29,158,117,0.3)" }}>✓ {m}</span>
                            ))}
                            {(fit.missing || []).slice(0, 3).map(m => (
                              <span key={m} style={{ fontSize: 11, padding: "2px 8px", borderRadius: 20, fontWeight: 600, background: "rgba(230,77,77,0.10)", color: "#E64D4D", border: "1px solid rgba(230,77,77,0.3)" }}>✗ {m}</span>
                            ))}
                            {c.location && <span style={{ fontSize: 11, color: "#a9abb3" }}>📍 {c.location}</span>}
                          </div>
                        </div>

                        {/* Buttons */}
                        <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                          <button onClick={() => setExpanded(isExp ? null : c.login)} style={{
                            padding: "6px 13px", borderRadius: 6, fontSize: 12, fontWeight: 700,
                            background: isExp ? color + "25" : "rgba(208,149,255,0.08)",
                            color: isExp ? color : "#d095ff",
                            border: `1px solid ${isExp ? color + "55" : "rgba(208,149,255,0.25)"}`,
                            cursor: "pointer",
                          }}>{isExp ? "▲ Hide" : "▼ Details"}</button>
                          <button onClick={() => navigate(`/profile/${c.login}`)} style={{
                            padding: "6px 13px", borderRadius: 6, fontSize: 12, fontWeight: 700,
                            background: "rgba(29,158,117,0.08)", color: "#1D9E75",
                            border: "1px solid rgba(29,158,117,0.25)", cursor: "pointer",
                          }}>📋</button>
                        </div>
                      </div>

                      {/* Expanded section */}
                      {isExp && (
                        <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid rgba(69,72,79,0.3)" }}>
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                            <div>
                              <div style={{ fontSize: 10, fontWeight: 700, color: "#a9abb3", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Score Breakdown</div>
                              {[
                                ["Required Skills", fit.breakdown?.skills ?? 0, "#d095ff"],
                                ["Activity",        fit.breakdown?.activity ?? 0, "#40cef3"],
                                ["Code Quality",    fit.breakdown?.code_quality ?? 0, "#1D9E75"],
                                ["Nice-to-Have",    fit.breakdown?.nice_to_have ?? 0, "#f59e0b"],
                                ["Thresholds",      fit.breakdown?.thresholds ?? 0, "#E6A817"],
                              ].map(([lbl, val, col]) => (
                                <div key={lbl} style={{ marginBottom: 8 }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                                    <span style={{ fontSize: 11, color: "#a9abb3" }}>{lbl}</span>
                                    <span style={{ fontSize: 11, fontWeight: 700, color: col }}>{val}%</span>
                                  </div>
                                  <div style={{ height: 5, borderRadius: 3, background: "#22262f" }}>
                                    <div style={{ width: `${val}%`, height: "100%", borderRadius: 3, background: col }} />
                                  </div>
                                </div>
                              ))}
                            </div>
                            <div>
                              {fit.bonuses?.length > 0 && (
                                <div style={{ marginBottom: 12 }}>
                                  <div style={{ fontSize: 10, fontWeight: 700, color: "#a9abb3", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>⭐ Bonus Matched</div>
                                  <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                                    {fit.bonuses.map(b => <span key={b} style={{ fontSize: 11, padding: "2px 9px", borderRadius: 20, background: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.3)", fontWeight: 600 }}>{b}</span>)}
                                  </div>
                                </div>
                              )}
                              {fit.missing?.length > 0 && (
                                <div style={{ marginBottom: 12 }}>
                                  <div style={{ fontSize: 10, fontWeight: 700, color: "#E64D4D", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>✗ Missing Skills</div>
                                  <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                                    {fit.missing.map(m => <span key={m} style={{ fontSize: 11, padding: "2px 9px", borderRadius: 20, background: "rgba(230,77,77,0.1)", color: "#E64D4D", border: "1px solid rgba(230,77,77,0.3)", fontWeight: 600 }}>{m}</span>)}
                                  </div>
                                </div>
                              )}
                              {fit.flags?.length > 0 && (
                                <div>
                                  <div style={{ fontSize: 10, fontWeight: 700, color: "#E6A817", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>⚠️ Warnings</div>
                                  {fit.flags.map((f, i) => <div key={i} style={{ fontSize: 11, color: "#a9abb3", paddingBottom: 4 }}>{f}</div>)}
                                </div>
                              )}
                              {!fit.flags?.length && !fit.missing?.length && (
                                <div style={{ padding: 12, borderRadius: 8, background: "rgba(29,158,117,0.08)", border: "1px solid rgba(29,158,117,0.25)", fontSize: 13, color: "#1D9E75", fontWeight: 700, textAlign: "center" }}>✅ All requirements met!</div>
                              )}
                            </div>
                          </div>
                          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                            <button onClick={() => navigate(`/enrich/${c.login}`)} style={{ padding: "7px 14px", borderRadius: 6, fontSize: 12, fontWeight: 700, background: "rgba(64,206,243,0.08)", color: "#40cef3", border: "1px solid rgba(64,206,243,0.25)", cursor: "pointer" }}>🔬 Deep Analysis</button>
                            <button onClick={() => navigate(`/candidate/${c.login}`)} style={{ padding: "7px 14px", borderRadius: 6, fontSize: 12, fontWeight: 700, background: "#22262f", color: "#a9abb3", border: "1px solid rgba(69,72,79,0.4)", cursor: "pointer" }}>👤 Full Profile</button>
                            <button onClick={() => navigate(`/profile/${c.login}`)} style={{ padding: "7px 14px", borderRadius: 6, fontSize: 12, fontWeight: 700, background: "rgba(29,158,117,0.08)", color: "#1D9E75", border: "1px solid rgba(29,158,117,0.25)", cursor: "pointer" }}>📋 CEO Report</button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
