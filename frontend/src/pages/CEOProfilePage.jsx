import { useState, useEffect, useCallback } from "react"
import axios from "axios"
import { useParams, useNavigate } from "react-router-dom"

const API = "http://localhost:8000"

function Section({ title, children }) {
  return (
    <div className="glass-panel" style={{ padding: "20px 24px", marginBottom: 20 }}>
      <h3 style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 16 }}>{title}</h3>
      {children}
    </div>
  )
}

// ── Red Flags Panel ────────────────────────────────────────────────────────

const SEVERITY_META = {
  high:   { color: "#E64D4D", label: "High Risk",  bg: "rgba(230,77,77,0.08)" },
  medium: { color: "#E6A817", label: "Medium Risk", bg: "rgba(230,168,23,0.08)" },
  low:    { color: "#40cef3", label: "Low Risk",    bg: "rgba(64,206,243,0.08)" },
}

function RedFlagsPanel({ data }) {
  if (!data) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading...</p>

  const sev = SEVERITY_META[data.severity] || { color: "#1D9E75", label: "Clean", bg: "rgba(29,158,117,0.08)" }

  return (
    <div>
      {/* Summary badge */}
      <div style={{ padding: "12px 18px", borderRadius: 8, background: sev.bg, border: `1px solid ${sev.color}33`, marginBottom: data.flags.length ? 16 : 0 }}>
        <span style={{ fontWeight: 700, color: sev.color, fontSize: 14 }}>{data.summary}</span>
      </div>

      {/* Individual flags */}
      {data.flags.map(f => {
        const m = SEVERITY_META[f.severity] || SEVERITY_META.low
        return (
          <div key={f.id} style={{ padding: "12px 16px", borderRadius: 8, background: m.bg, border: `1px solid ${m.color}33`, marginTop: 10, display: "flex", gap: 12, alignItems: "flex-start" }}>
            <span style={{ fontSize: 22 }}>{f.emoji}</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: m.color }}>{f.label}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>{f.detail}</div>
            </div>
            <div style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 10, background: `${m.color}20`, color: m.color, whiteSpace: "nowrap" }}>
              {m.label}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Collaboration Panel ────────────────────────────────────────────────────

function ScoreMeter({ label, value, max = 100, color }) {
  const pct = Math.min((value / max) * 100, 100)
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ position: "relative", width: 64, height: 64, margin: "0 auto 8px" }}>
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="26" fill="none" stroke="var(--surface-high)" strokeWidth="6" />
          <circle cx="32" cy="32" r="26" fill="none" stroke={color} strokeWidth="6"
            strokeDasharray={`${2 * Math.PI * 26}`}
            strokeDashoffset={`${2 * Math.PI * 26 * (1 - pct / 100)}`}
            strokeLinecap="round"
            style={{ transform: "rotate(-90deg)", transformOrigin: "32px 32px", transition: "stroke-dashoffset 1s ease" }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color, fontFamily: "var(--font-display)" }}>{value}</div>
      </div>
      <div style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>{label}</div>
    </div>
  )
}

function CollaborationPanel({ data }) {
  if (!data) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading...</p>
  if (data.error) return <p style={{ color: "#E64D4D", fontSize: 13 }}>⚠️ {data.error}</p>

  const color = data.label_color || "#888"

  return (
    <div>
      {/* Main score */}
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 24 }}>
        <div style={{ position: "relative", width: 100, height: 100, flexShrink: 0 }}>
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--surface-high)" strokeWidth="8" />
            <circle cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8"
              strokeDasharray={`${2 * Math.PI * 42}`}
              strokeDashoffset={`${2 * Math.PI * 42 * (1 - data.collab_score / 100)}`}
              strokeLinecap="round"
              style={{ transform: "rotate(-90deg)", transformOrigin: "50px 50px", transition: "stroke-dashoffset 1s ease" }} />
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <div style={{ fontSize: 26, fontWeight: 900, color, fontFamily: "var(--font-display)", lineHeight: 1 }}>{data.collab_score}</div>
            <div style={{ fontSize: 9, color, fontWeight: 700 }}>/ 100</div>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800, color, fontFamily: "var(--font-display)", marginBottom: 4 }}>{data.collab_label}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {[
              ["🔀 PRs to Others", data.prs_to_others],
              ["🐛 Issues Opened", data.issues_opened],
              ["👥 Followers",     data.followers],
              ["🏢 Orgs",          data.orgs_count],
            ].map(([lbl, val]) => (
              <div key={lbl} style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {lbl}: <span style={{ color: "var(--text-main)", fontWeight: 700 }}>{val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <ScoreMeter label="Stars Recv" value={data.stars_received}  max={Math.max(data.stars_received * 2, 10)} color="#E6A817" />
        <ScoreMeter label="Forked By"  value={data.forked_by_others} max={Math.max(data.forked_by_others * 2, 10)} color="#d095ff" />
        <ScoreMeter label="Gists"      value={data.public_gists}    max={20} color="#40cef3" />
        <ScoreMeter label="Following"  value={data.following}       max={Math.max(data.following * 2, 10)} color="#1D9E75" />
      </div>

      {/* Contributed repos */}
      {data.top_contributed_repos?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8 }}>Contributed to (others' repos)</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {data.top_contributed_repos.map(r => (
              <a key={r} href={`https://github.com/${r}`} target="_blank" rel="noreferrer"
                style={{ fontSize: 11, padding: "3px 10px", borderRadius: 10, background: "rgba(29,158,117,0.08)", color: "#1D9E75", border: "1px solid rgba(29,158,117,0.2)", textDecoration: "none", fontWeight: 600 }}>
                {r}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Growth Trajectory Panel ────────────────────────────────────────────────

function GrowthPanel({ data }) {
  if (!data) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading...</p>
  if (data.error) return <p style={{ color: "#E64D4D", fontSize: 13 }}>⚠️ {data.error}</p>

  const color = data.trajectory_color || "#888"
  const maxRepos = Math.max(...(data.timeline || []).map(t => t.repos), 1)

  return (
    <div>
      {/* Trajectory badge */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div style={{ padding: "12px 20px", borderRadius: 10, background: `${color}18`, border: `1px solid ${color}33`, display: "inline-flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 900, color, fontFamily: "var(--font-display)" }}>{data.trajectory}</span>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          {[
            ["Tier",       data.current_tier],
            ["Total Repos", data.total_repos],
            ["New Langs",  data.tech_expansion],
          ].map(([lbl, val]) => (
            <div key={lbl} style={{ textAlign: "center", padding: "8px 16px", borderRadius: 8, background: "var(--surface-high)" }}>
              <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: "var(--font-display)" }}>{val}</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Signal list */}
      <div style={{ marginBottom: 20 }}>
        {data.signals.map((s, i) => (
          <div key={i} style={{ padding: "8px 14px", marginBottom: 6, borderRadius: 6, background: "var(--surface-high)", fontSize: 13, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color }}>•</span> {s}
          </div>
        ))}
      </div>

      {/* New languages */}
      {data.new_languages?.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8 }}>New Languages (last 6 months)</div>
          <div style={{ display: "flex", gap: 6 }}>
            {data.new_languages.map(l => (
              <span key={l} style={{ fontSize: 12, padding: "4px 12px", borderRadius: 20, background: `${color}15`, color, border: `1px solid ${color}30`, fontWeight: 600 }}>🆕 {l}</span>
            ))}
          </div>
        </div>
      )}

      {/* Mini chart: monthly repo activity */}
      {data.timeline?.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8 }}>Repo Creation Timeline</div>
          <div style={{ display: "flex", gap: 3, alignItems: "flex-end", height: 50 }}>
            {data.timeline.map(t => (
              <div key={t.period} title={`${t.period}: ${t.repos} repos`}
                style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{
                  width: "100%", borderRadius: "2px 2px 0 0",
                  height: `${Math.max((t.repos / maxRepos) * 44, t.repos > 0 ? 4 : 1)}px`,
                  background: `${color}${Math.round(30 + (t.repos / maxRepos) * 180).toString(16)}`,
                  transition: "height 0.4s ease",
                }} />
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ fontSize: 9, color: "var(--text-muted)" }}>{data.timeline[0]?.period}</span>
            <span style={{ fontSize: 9, color: "var(--text-muted)" }}>{data.timeline[data.timeline.length - 1]?.period}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function CEOProfilePage() {
  const { login } = useParams()
  const navigate  = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData]       = useState(null)
  const [candidate, setCandidate] = useState(null)
  const [error, setError]     = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [profileRes, candidatesRes] = await Promise.all([
        axios.get(`${API}/candidates/${login}/full-profile`),
        axios.get(`${API}/candidates`),
      ])
      setData(profileRes.data)
      const cands = candidatesRes.data?.candidates || []
      setCandidate(cands.find(c => c.login === login) || null)
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to load profile")
    }
    setLoading(false)
  }, [login])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <div className="animate-in" style={{ maxWidth: 860, margin: "0 auto", padding: "40px 24px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28 }}>
        <button onClick={() => navigate(-1)} style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}>← Back</button>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 24 }}>📋 CEO Report <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>@{login}</span></h1>
          {candidate && <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>{candidate.name} · {candidate.location}</p>}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => navigate(`/enrich/${login}`)} style={{ padding: "8px 14px", borderRadius: 6, background: "rgba(64,206,243,0.08)", color: "var(--secondary-color)", border: "1px solid rgba(64,206,243,0.2)", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>🔬 Deep Analysis</button>
          <button onClick={() => window.print()} style={{ padding: "8px 14px", borderRadius: 6, background: "rgba(29,158,117,0.08)", color: "#1D9E75", border: "1px solid rgba(29,158,117,0.2)", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>🖨️ Print Report</button>
        </div>
      </div>

      {error && (
        <div style={{ padding: "14px 20px", borderRadius: 8, background: "rgba(230,77,77,0.1)", border: "1px solid rgba(230,77,77,0.3)", color: "#E64D4D", marginBottom: 20 }}>❌ {error}</div>
      )}

      {loading ? (
        <div className="glass-panel" style={{ padding: 80, textAlign: "center" }}>
          <div style={{ width: 40, height: 40, border: "4px solid rgba(208,149,255,0.2)", borderTopColor: "var(--primary-color)", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 1s linear infinite" }} />
          <p style={{ color: "var(--text-muted)" }}>Running CEO intelligence analysis for @{login}...</p>
          <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 6 }}>Fetching events, repos, and growth data (~15s first run)</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : data && (
        <>
          <Section title="🚨 Red Flag Detector">
            <RedFlagsPanel data={data.red_flags} />
          </Section>

          <Section title="🤝 Collaboration Score">
            <CollaborationPanel data={data.collaboration} />
          </Section>

          <Section title="📈 Growth Trajectory">
            <GrowthPanel data={data.growth} />
          </Section>
        </>
      )}
    </div>
  )
}
