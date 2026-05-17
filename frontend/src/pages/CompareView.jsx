import { useState, useEffect } from "react"
import axios from "axios"
import { useSearchParams, useNavigate } from "react-router-dom"

const API = "http://localhost:8000"

const SCORE_KEYS = ["project_quality", "consistency", "tech_stack", "documentation", "open_source"]
const SCORE_LABELS = { project_quality: "Projects", consistency: "Consistency", tech_stack: "Tech Stack", documentation: "Docs", open_source: "Open Source" }
const SCORE_COLORS = ["#d095ff", "#40cef3", "#1D9E75", "#E6A817", "#E64D4D"]

function ScoreBar({ label, value, max = 30, color }) {
  const pct = Math.round((value / max) * 100)
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>{value}</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: "var(--surface-high)", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, borderRadius: 3, background: color, transition: "width 0.6s ease" }} />
      </div>
    </div>
  )
}

function CandidateColumn({ candidate, onRemove }) {
  if (!candidate) return (
    <div className="glass-panel" style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", flex: 1 }}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>👤</div>
      <p style={{ fontSize: 14 }}>No candidate loaded</p>
    </div>
  )

  const score = Math.round(candidate.scoring?.score * 100 || 0)
  const breakdown = candidate.scoring?.breakdown || {}
  const scoreColor = score >= 60 ? "#1D9E75" : score >= 35 ? "#E6A817" : "#E64D4D"
  const links = candidate.links || {}
  const langs = candidate.activity?.top_languages || []

  return (
    <div className="glass-panel" style={{ flex: 1, overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-ghost)", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ fontSize: 18, color: "var(--text-main)", marginBottom: 4 }}>{candidate.name || candidate.login}</h2>
          <a href={`https://github.com/${candidate.login}`} target="_blank" rel="noreferrer"
            style={{ fontSize: 13, color: "var(--secondary-color)", textDecoration: "none" }}>
            @{candidate.login}
          </a>
        </div>
        <button onClick={onRemove} style={{ padding: "4px 10px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 12 }}>✕</button>
      </div>

      <div style={{ padding: "20px 24px" }}>
        {/* Big Score */}
        <div style={{ textAlign: "center", marginBottom: 24, padding: "20px 0", borderRadius: 8, background: "var(--surface-high)" }}>
          <div style={{ fontSize: 52, fontWeight: 800, color: scoreColor, fontFamily: "var(--font-display)", lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, fontWeight: 600 }}>MATCH SCORE</div>
        </div>

        {/* Domain Badge */}
        <div style={{ marginBottom: 20 }}>
          <span style={{ fontSize: 12, padding: "6px 14px", borderRadius: 20, background: "rgba(208, 149, 255, 0.1)", border: "1px solid rgba(208, 149, 255, 0.3)", color: "var(--primary-color)", fontWeight: 600 }}>
            {(candidate.category?.primary_domain || "").replace(/_/g, " ")}
          </span>
        </div>

        {/* GitHub Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 20 }}>
          {[
            ["⭐ Repos", candidate.activity?.repo_count ?? "—"],
            ["📝 Commits", candidate.activity?.commit_count ?? "—"],
            ["👥 Followers", candidate.activity?.followers ?? "—"],
          ].map(([lbl, val]) => (
            <div key={lbl} style={{ textAlign: "center", padding: "10px 6px", borderRadius: 6, background: "var(--surface-high)" }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-main)" }}>{val}</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{lbl}</div>
            </div>
          ))}
        </div>

        {/* Score Breakdown */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 12 }}>Score Breakdown</div>
          {SCORE_KEYS.map((k, i) => (
            <ScoreBar key={k} label={SCORE_LABELS[k]} value={breakdown[k] || 0}
              max={k === "project_quality" ? 30 : k === "consistency" ? 25 : k === "tech_stack" ? 20 : k === "documentation" ? 15 : 10}
              color={SCORE_COLORS[i]} />
          ))}
        </div>

        {/* Languages */}
        {langs.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 10 }}>Languages</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {langs.slice(0, 8).map(l => (
                <span key={l} style={{ fontSize: 11, padding: "4px 10px", borderRadius: 20, background: "var(--surface-high)", color: "var(--text-muted)", fontWeight: 600 }}>{l}</span>
              ))}
            </div>
          </div>
        )}

        {/* Links */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {links.linkedin && <a href={links.linkedin} target="_blank" rel="noreferrer" style={{ fontSize: 12, padding: "6px 14px", borderRadius: 6, background: "rgba(10,102,194,0.15)", color: "#4a9fd5", border: "1px solid rgba(10,102,194,0.3)", fontWeight: 600, textDecoration: "none" }}>LinkedIn</a>}
          {links.portfolio && <a href={links.portfolio} target="_blank" rel="noreferrer" style={{ fontSize: 12, padding: "6px 14px", borderRadius: 6, background: "rgba(64,206,243,0.1)", color: "var(--secondary-color)", border: "1px solid rgba(64,206,243,0.2)", fontWeight: 600, textDecoration: "none" }}>Portfolio</a>}
          {links.resume && <a href={links.resume} target="_blank" rel="noreferrer" style={{ fontSize: 12, padding: "6px 14px", borderRadius: 6, background: "rgba(230,168,23,0.1)", color: "#E6A817", border: "1px solid rgba(230,168,23,0.2)", fontWeight: 600, textDecoration: "none" }}>CV</a>}
        </div>

        {/* Summary */}
        {candidate.scoring?.rationale && (
          <div style={{ marginTop: 20, padding: "12px 16px", borderRadius: 8, background: "var(--surface-high)", fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>
            {candidate.scoring.rationale}
          </div>
        )}
      </div>
    </div>
  )
}

export default function CompareView() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [allCandidates, setAllCandidates] = useState([])
  const [selected, setSelected] = useState([null, null])
  const [searchA, setSearchA] = useState("")
  const [searchB, setSearchB] = useState("")

  useEffect(() => {
    axios.get(`${API}/candidates`).then(res => {
      setAllCandidates(res.data)
      const a = searchParams.get("a")
      const b = searchParams.get("b")
      if (a || b) {
        const found = (login) => res.data.find(c => c.login === login) || null
        setSelected([a ? found(a) : null, b ? found(b) : null])
      }
    })
  }, [])

  const setSlot = (idx, login) => {
    const c = allCandidates.find(c => c.login === login) || null
    setSelected(prev => { const next = [...prev]; next[idx] = c; return next })
  }

  const filtered = (q) => allCandidates.filter(c =>
    (c.name || "").toLowerCase().includes(q.toLowerCase()) ||
    c.login.toLowerCase().includes(q.toLowerCase())
  ).slice(0, 8)

  const scoreA = Math.round((selected[0]?.scoring?.score || 0) * 100)
  const scoreB = Math.round((selected[1]?.scoring?.score || 0) * 100)

  return (
    <div className="animate-in" style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button onClick={() => navigate("/")} style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}>← Back</button>
        <div>
          <h1 style={{ fontSize: 26 }}>⚖️ Compare <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>Candidates</span></h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>Select two candidates to compare side by side</p>
        </div>
      </div>

      {/* Pickers */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        {[0, 1].map(idx => (
          <div key={idx} className="glass-panel" style={{ padding: "16px 20px" }}>
            <label style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", display: "block", marginBottom: 10 }}>
              Candidate {idx + 1}
            </label>
            <input
              type="text"
              placeholder="Search by name or @login..."
              value={idx === 0 ? searchA : searchB}
              onChange={e => idx === 0 ? setSearchA(e.target.value) : setSearchB(e.target.value)}
              style={{ width: "100%", padding: "10px 14px", borderRadius: 6, border: "1px solid var(--border-ghost)", background: "var(--surface-high)", color: "var(--text-main)", fontSize: 13, fontFamily: "var(--font-body)", outline: "none" }}
            />
            {(idx === 0 ? searchA : searchB).length > 0 && (
              <div style={{ marginTop: 6, borderRadius: 6, border: "1px solid var(--border-ghost)", overflow: "hidden", background: "var(--surface-mid)" }}>
                {filtered(idx === 0 ? searchA : searchB).map(c => (
                  <div key={c.login} onClick={() => { setSlot(idx, c.login); idx === 0 ? setSearchA("") : setSearchB("") }}
                    className="float-hover"
                    style={{ padding: "10px 14px", cursor: "pointer", borderBottom: "1px solid var(--border-ghost)", display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{c.name || c.login}</span>
                    <span style={{ fontSize: 12, color: "var(--secondary-color)" }}>@{c.login}</span>
                  </div>
                ))}
                {filtered(idx === 0 ? searchA : searchB).length === 0 && (
                  <div style={{ padding: "10px 14px", fontSize: 13, color: "var(--text-muted)" }}>No results</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Winner Banner */}
      {selected[0] && selected[1] && (
        <div style={{ marginBottom: 24, padding: "14px 20px", borderRadius: 8, textAlign: "center",
          background: scoreA > scoreB ? "rgba(29,158,117,0.1)" : scoreB > scoreA ? "rgba(208,149,255,0.1)" : "rgba(64,206,243,0.1)",
          border: `1px solid ${scoreA > scoreB ? "rgba(29,158,117,0.3)" : scoreB > scoreA ? "rgba(208,149,255,0.3)" : "rgba(64,206,243,0.3)"}`,
          fontSize: 15, fontWeight: 700,
          color: scoreA > scoreB ? "#1D9E75" : scoreB > scoreA ? "var(--primary-color)" : "var(--secondary-color)",
        }}>
          {scoreA === scoreB ? "🤝 Tie!" : `🏆 ${scoreA > scoreB ? (selected[0].name || selected[0].login) : (selected[1].name || selected[1].login)} wins with score ${Math.max(scoreA, scoreB)}`}
        </div>
      )}

      {/* Comparison Columns */}
      <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
        <CandidateColumn candidate={selected[0]} onRemove={() => setSelected(prev => [null, prev[1]])} />
        <CandidateColumn candidate={selected[1]} onRemove={() => setSelected(prev => [prev[0], null])} />
      </div>
    </div>
  )
}
