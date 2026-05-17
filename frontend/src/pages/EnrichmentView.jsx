import { useState, useEffect, useCallback } from "react"
import axios from "axios"
import { useParams, useNavigate } from "react-router-dom"

const API = "http://localhost:8000"

const ARCHETYPE_META = {
  "Night Owl":       { emoji: "🦉", color: "#7c3aed", bg: "rgba(124,58,237,0.12)" },
  "Weekend Warrior": { emoji: "🏄", color: "#0ea5e9", bg: "rgba(14,165,233,0.12)" },
  "Daily Coder":     { emoji: "⚡", color: "#1D9E75", bg: "rgba(29,158,117,0.12)" },
  "Sprinter":        { emoji: "🚀", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
  "Balanced":        { emoji: "⚖️", color: "#d095ff", bg: "rgba(208,149,255,0.12)" },
  "No Data":         { emoji: "❓", color: "#888",    bg: "rgba(128,128,128,0.1)" },
}

const GRADE_META = {
  A: { color: "#1D9E75", label: "Excellent" },
  B: { color: "#40cef3", label: "Good" },
  C: { color: "#E6A817", label: "Average" },
  D: { color: "#ffa44c", label: "Below Avg" },
  E: { color: "#E64D4D", label: "Poor" },
  F: { color: "#888",    label: "Very Poor" },
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

function Section({ title, children }) {
  return (
    <div className="glass-panel" style={{ padding: "20px 24px", marginBottom: 20 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 16 }}>{title}</h3>
      {children}
    </div>
  )
}

function CommitHeatmap({ pattern }) {
  if (!pattern || pattern.archetype === "No Data") {
    return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No commit data available in the lookback window.</p>
  }

  const archetypeMeta = ARCHETYPE_META[pattern.archetype] || ARCHETYPE_META["Balanced"]
  const maxHourCount  = Math.max(...(pattern.heatmap_hours || []).map(h => h.count), 1)
  const maxDayCount   = Math.max(...(pattern.heatmap_days || []).map(d => d.count), 1)

  return (
    <div>
      {/* Archetype Badge */}
      <div style={{
        display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 20,
        padding: "12px 20px", borderRadius: 10,
        background: archetypeMeta.bg, border: `1px solid ${archetypeMeta.color}44`,
      }}>
        <span style={{ fontSize: 28 }}>{archetypeMeta.emoji}</span>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: archetypeMeta.color, fontFamily: "var(--font-display)" }}>
            {pattern.archetype}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            {pattern.total_analyzed} commits analyzed · Peak: {pattern.peak_day} {pattern.peak_hour !== null ? `${pattern.peak_hour}:00` : ""}
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          ["🌙 Night Ratio",    `${(pattern.night_ratio * 100).toFixed(0)}%`],
          ["📅 Weekend Ratio",  `${(pattern.weekend_ratio * 100).toFixed(0)}%`],
          ["📆 Active Days",    pattern.distinct_days],
        ].map(([lbl, val]) => (
          <div key={lbl} style={{ textAlign: "center", padding: "12px 8px", borderRadius: 8, background: "var(--surface-high)" }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text-main)", fontFamily: "var(--font-display)" }}>{val}</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 3 }}>{lbl}</div>
          </div>
        ))}
      </div>

      {/* Hour of Day Heatmap */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, marginBottom: 8 }}>COMMITS BY HOUR OF DAY</div>
        <div style={{ display: "flex", gap: 3, alignItems: "flex-end", height: 60 }}>
          {(pattern.heatmap_hours || []).map(({ hour, count }) => {
            const pct = count / maxHourCount
            const isNight = hour >= 22 || hour < 5
            return (
              <div key={hour} title={`${hour}:00 — ${count} commits`}
                style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                <div style={{
                  width: "100%", borderRadius: "2px 2px 0 0",
                  height: `${Math.max(pct * 52, count > 0 ? 4 : 2)}px`,
                  background: isNight
                    ? `rgba(124,58,237,${0.3 + pct * 0.7})`
                    : `rgba(64,206,243,${0.2 + pct * 0.8})`,
                  transition: "height 0.4s ease",
                }} />
                {(hour % 6 === 0) && (
                  <div style={{ fontSize: 9, color: "var(--text-muted)", whiteSpace: "nowrap" }}>{hour}h</div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Day of Week Bars */}
      <div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, marginBottom: 8 }}>COMMITS BY DAY OF WEEK</div>
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end", height: 60 }}>
          {(pattern.heatmap_days || []).map(({ day, count }) => {
            const pct = count / maxDayCount
            const isWeekend = day === "Saturday" || day === "Sunday"
            return (
              <div key={day} title={`${day}: ${count} commits`}
                style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <div style={{
                  width: "100%", borderRadius: "3px 3px 0 0",
                  height: `${Math.max(pct * 52, count > 0 ? 4 : 2)}px`,
                  background: isWeekend
                    ? `rgba(14,165,233,${0.3 + pct * 0.7})`
                    : `rgba(208,149,255,${0.2 + pct * 0.8})`,
                }} />
                <div style={{ fontSize: 10, color: "var(--text-muted)" }}>{day.slice(0, 3)}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function CodeQualityPanel({ quality, onRefresh }) {
  if (!quality) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading...</p>
  if (quality.error) return <p style={{ color: "#E64D4D", fontSize: 13 }}>⚠️ {quality.error}</p>

  // Detect old single-repo cache format (missing repo_count)
  const isOldFormat = quality.repo_count === undefined && quality.repo_analyzed !== undefined
  if (isOldFormat) {
    return (
      <div style={{ textAlign: "center", padding: "30px 20px" }}>
        <div style={{ fontSize: 32, marginBottom: 10 }}>🔄</div>
        <p style={{ color: "var(--text-muted)", marginBottom: 16, fontSize: 14 }}>
          This candidate was analyzed with an older version. Click below to run the full multi-repo analysis.
        </p>
        <button onClick={onRefresh} style={{
          padding: "10px 24px", borderRadius: 8, fontWeight: 700, fontSize: 14,
          background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))",
          color: "#fff", border: "none", cursor: "pointer",
        }}>🔬 Re-analyze All Repos</button>
      </div>
    )
  }

  const gradeColor = GRADE_META[quality.overall_grade]?.color || "#888"
  const gradeLabel = GRADE_META[quality.overall_grade]?.label || ""
  const langs      = Object.entries(quality.language_breakdown || {}).slice(0, 10)
  const maxLangPct = Math.max(...langs.map(([, v]) => v.pct), 1)

  // Colors for language bars
  const langColors = ["#d095ff","#40cef3","#1D9E75","#E6A817","#ffa44c","#E64D4D","#7c3aed","#0ea5e9","#f59e0b","#10b981"]

  return (
    <div>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 24 }}>
        <div style={{
          width: 88, height: 88, borderRadius: 14, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", flexShrink: 0,
          background: `${gradeColor}20`, border: `2px solid ${gradeColor}`,
        }}>
          <div style={{ fontSize: 40, fontWeight: 900, color: gradeColor, fontFamily: "var(--font-display)", lineHeight: 1 }}>
            {quality.overall_grade}
          </div>
          <div style={{ fontSize: 9, color: gradeColor, fontWeight: 700 }}>{gradeLabel}</div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {[
              ["📁 Repos",       quality.repo_count          ?? "—"],
              ["✅ With Tests",  quality.repos_with_tests    ?? "—"],
              ["📄 Test Files",  quality.total_test_files    ?? "—"],
              ["🛠️ Tools",       quality.all_tools?.length   ?? 0],
            ].map(([lbl, val]) => (

              <div key={lbl} style={{ textAlign: "center", padding: "10px 6px", borderRadius: 8, background: "var(--surface-high)" }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: "var(--text-main)", fontFamily: "var(--font-display)" }}>{val}</div>
                <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{lbl}</div>
              </div>
            ))}
          </div>
          {quality.complexity_grade && (
            <div style={{ marginTop: 10, fontSize: 12, color: "var(--text-muted)" }}>
              Python complexity (radon): <span style={{ color: GRADE_META[quality.complexity_grade]?.color, fontWeight: 700 }}>{quality.complexity_grade}</span>
            </div>
          )}
        </div>
      </div>

      {/* Language breakdown */}
      {langs.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 12 }}>
            Language Breakdown (across all repos)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {langs.map(([lang, info], i) => (
              <div key={lang}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-main)" }}>{lang}</span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {info.pct}% · {(info.bytes / 1024).toFixed(0)} KB
                  </span>
                </div>
                <div style={{ height: 6, borderRadius: 3, background: "var(--surface-high)", overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: 3,
                    width: `${(info.pct / maxLangPct) * 100}%`,
                    background: langColors[i % langColors.length],
                    transition: "width 0.6s ease",
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools & Frameworks */}
      {quality.all_tools?.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 10 }}>
            Tools & Frameworks Detected
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {quality.all_tools.map(tool => (
              <span key={tool} style={{
                fontSize: 12, padding: "5px 12px", borderRadius: 20, fontWeight: 600,
                background: "rgba(64,206,243,0.08)", color: "var(--secondary-color)",
                border: "1px solid rgba(64,206,243,0.2)",
              }}>{tool}</span>
            ))}
          </div>
        </div>
      )}

      {/* Per-repo table */}
      {quality.per_repo?.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", marginBottom: 10 }}>
            Top Repos Analyzed
          </div>
          <div style={{ maxHeight: 280, overflowY: "auto", borderRadius: 8, border: "1px solid var(--border-ghost)" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ background: "var(--surface-high)" }}>
                  {["Repo", "Language", "⭐", "Files", "Tests", "Tools"].map(h => (
                    <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: "var(--text-muted)", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 1, borderBottom: "1px solid var(--border-ghost)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {quality.per_repo.map(r => (
                  <tr key={r.name} style={{ borderBottom: "1px solid var(--border-ghost)" }}>
                    <td style={{ padding: "9px 12px", fontWeight: 600, color: "var(--text-main)" }}>
                      <a href={`https://github.com/${r.name}`} target="_blank" rel="noreferrer"
                        style={{ color: "var(--secondary-color)", textDecoration: "none" }}>
                        {r.name}
                      </a>
                    </td>
                    <td style={{ padding: "9px 12px", color: "var(--text-muted)" }}>{r.language}</td>
                    <td style={{ padding: "9px 12px", color: "var(--text-muted)" }}>{r.stars}</td>
                    <td style={{ padding: "9px 12px", color: "var(--text-muted)" }}>{r.file_count}</td>
                    <td style={{ padding: "9px 12px" }}>
                      <span style={{ color: r.has_tests ? "#1D9E75" : "var(--text-muted)", fontWeight: 600 }}>
                        {r.has_tests ? `✅ ${r.test_count}` : "—"}
                      </span>
                    </td>
                    <td style={{ padding: "9px 12px", color: "var(--text-muted)", maxWidth: 200 }}>
                      {r.tools.slice(0, 4).join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}


function LiveProjectsPanel({ live }) {
  if (!live) return <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading...</p>
  if (!live.has_live_project) return (
    <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No deployed projects detected.</p>
  )
  return (
    <div>
      <div style={{ marginBottom: 12, fontSize: 13, color: "#1D9E75", fontWeight: 600 }}>
        🌍 {live.live_count} live project{live.live_count !== 1 ? "s" : ""} found
      </div>
      {live.live_projects.map((p, i) => (
        <div key={i} style={{ padding: "12px 16px", borderRadius: 8, background: "var(--surface-high)", marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-main)" }}>{p.name}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                {p.platform} · ⭐ {p.stars}
              </div>
            </div>
            {p.url && (
              <a href={p.url} target="_blank" rel="noreferrer" style={{
                fontSize: 12, padding: "5px 12px", borderRadius: 6,
                background: "rgba(29,158,117,0.12)", color: "#1D9E75",
                border: "1px solid rgba(29,158,117,0.3)", fontWeight: 600, textDecoration: "none",
              }}>
                🔗 Open
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function EnrichmentView() {
  const { login } = useParams()
  const navigate  = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [quality, setQuality] = useState(null)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async (forceRefresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const qualUrl = forceRefresh
        ? `${API}/candidates/${login}/code-quality?refresh=true`
        : `${API}/candidates/${login}/code-quality`
      // Run main enrich + code quality in parallel
      const [enrichRes, qualRes] = await Promise.all([
        axios.get(`${API}/candidates/${login}/enrich`),
        axios.get(qualUrl),
      ])
      setData(enrichRes.data)
      setQuality(qualRes.data)
    } catch (e) {
      setError(e?.response?.data?.error || "Failed to load enrichment data")
    }
    setLoading(false)
  }, [login])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <div className="animate-in" style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
        <button onClick={() => navigate(-1)} style={{ padding: "8px 16px", borderRadius: 6, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", fontSize: 13 }}>← Back</button>
        <div>
          <h1 style={{ fontSize: 24 }}>
            🔬 Deep Analysis <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>@{login}</span>
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
            Behavioral pattern, code quality, and deployment analysis
          </p>
        </div>
        <button onClick={fetchData} style={{ marginLeft: "auto", padding: "8px 16px", borderRadius: 6, background: "rgba(208,149,255,0.1)", color: "var(--primary-color)", border: "1px solid rgba(208,149,255,0.3)", fontSize: 13, fontWeight: 600 }}>
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div style={{ padding: "14px 20px", borderRadius: 8, background: "rgba(230,77,77,0.1)", border: "1px solid rgba(230,77,77,0.3)", color: "#E64D4D", marginBottom: 20 }}>
          ❌ {error}
        </div>
      )}

      {loading ? (
        <div className="glass-panel" style={{ padding: 80, textAlign: "center" }}>
          <div style={{ width: 40, height: 40, border: "4px solid rgba(208,149,255,0.2)", borderTopColor: "var(--primary-color)", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 1s linear infinite" }} />
          <p style={{ color: "var(--text-muted)" }}>Analyzing @{login}... (first load may take ~10s)</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : data && (
        <>
          {/* Staleness Banner */}
          {data.staleness && (
            <div style={{
              marginBottom: 20, padding: "14px 20px", borderRadius: 8,
              background: `${data.staleness.color}18`, border: `1px solid ${data.staleness.color}44`,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontWeight: 700, fontSize: 15, color: data.staleness.color }}>
                {data.staleness.staleness_label}
              </span>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                {data.staleness.days_since_active != null
                  ? `Last active ${data.staleness.days_since_active} days ago (${data.staleness.last_active_date})`
                  : "No activity data"}
                {data.staleness.is_actively_searching && " · 🎯 Actively job searching!"}
              </span>
            </div>
          )}

          <Section title="🕐 Commit Pattern Analysis">
            <CommitHeatmap pattern={data.pattern} />
          </Section>

          <Section title="🔬 Code Quality Score">
            <CodeQualityPanel quality={quality} onRefresh={() => fetchData(true)} />
          </Section>

          <Section title="🌍 Live Projects">
            <LiveProjectsPanel live={data.live} />
          </Section>
        </>
      )}
    </div>
  )
}
