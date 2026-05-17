import { useState, useEffect } from "react"
import axios from "axios"
import { useNavigate } from "react-router-dom"
import CandidateTable from "../components/CandidateTable"
import FilterPanel from "../components/FilterPanel"
import PipelineControl from "../components/PipelineControl"
import WeekSelector from "../components/WeekSelector"
import EmailComposer from "../components/EmailComposer"
import ReportExporter from "../components/ReportExporter"
import SavedFilters from "../components/SavedFilters"

const API = "http://localhost:8000"

export default function Dashboard() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [stats, setStats] = useState({})
  const [weeks, setWeeks] = useState([])
  const [dates, setDates] = useState([])
  const [selectedWeek, setSelectedWeek] = useState("all")
  const [filters, setFilters] = useState({ domain: "", min_score: 0, has_linkedin: false, has_cv: false })
  const [shortlisted, setShortlisted] = useState(new Set())
  const [showEmailer, setShowEmailer] = useState(false)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)

  const [dateMode, setDateMode] = useState(null)

  const fetchCandidates = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.domain) params.domain = filters.domain
      if (filters.min_score) params.min_score = filters.min_score
      if (filters.has_linkedin) params.has_linkedin = true
      if (filters.has_cv) params.has_cv = true

      let url
      if (dateMode?.type === "date") {
        url = `${API}/candidates/by-date`
        params.date = dateMode.value
      } else if (dateMode?.type === "week") {
        url = `${API}/candidates/by-week`
        params.week = dateMode.value
      } else if (selectedWeek === "all") {
        url = `${API}/candidates`
      } else {
        url = `${API}/candidates/week/${selectedWeek}`
      }

      const res = await axios.get(url, { params })
      setCandidates(res.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const fetchStats = async () => {
    try { const r = await axios.get(`${API}/stats`); setStats(r.data) }
    catch (e) { console.error(e) }
  }

  const fetchWeeks = async () => {
    try { const r = await axios.get(`${API}/weeks`); setWeeks(r.data) }
    catch (e) { console.error(e) }
  }

  const fetchDates = async () => {
    try { const r = await axios.get(`${API}/dates`); setDates(r.data) }
    catch (e) { console.error(e) }
  }

  useEffect(() => { fetchStats(); fetchWeeks(); fetchDates() }, [])
  useEffect(() => { fetchCandidates() }, [filters, selectedWeek, dateMode])

  const handleQuickWeekChange = (w) => { setDateMode(null); setSelectedWeek(w) }
  const handleDateSelect = (date) => { setDateMode({ type: "date", value: date }); setSelectedWeek("") }
  const handleWeekRangeSelect = (week) => { setDateMode({ type: "week", value: week }); setSelectedWeek("") }

  const toggleShortlist = (login) => {
    setShortlisted(prev => {
      const next = new Set(prev)
      next.has(login) ? next.delete(login) : next.add(login)
      return next
    })
  }

  const shortlistedCandidates = candidates.filter(c => shortlisted.has(c.login))

  const handleExportCSV = async () => {
    setExporting(true)
    try {
      const params = new URLSearchParams()
      if (filters.domain) params.set("domain", filters.domain)
      if (filters.min_score) params.set("min_score", filters.min_score)
      if (filters.has_linkedin) params.set("has_linkedin", "true")
      if (filters.has_cv) params.set("has_cv", "true")
      const url = `${API}/candidates/export/csv?${params.toString()}`
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", "candidates.csv")
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (e) { console.error(e) }
    setExporting(false)
  }

  const handleCompare = () => {
    const logins = [...shortlisted].slice(0, 2)
    navigate(`/compare?a=${logins[0]}&b=${logins[1] || ""}`)
  }

  return (
    <div className="animate-in" style={{ maxWidth: 1300, margin: "0 auto", padding: "40px 24px" }}>

      {/* Header */}
      <div className="glass-panel" style={{
        padding: "24px 32px",
        display: "flex", justifyContent: "space-between",
        alignItems: "center", marginBottom: 32,
        borderLeft: "4px solid var(--primary-color)"
      }}>
        <div>
          <h1 style={{ fontSize: 28, letterSpacing: "-0.5px", color: "var(--text-main)" }}>
            Candidate Discovery <span style={{ color: "var(--primary-color)", fontWeight: 400 }}>Agent</span>
          </h1>
          <div style={{ display: "flex", gap: 16, marginTop: 8, color: "var(--text-muted)", fontSize: 15, fontFamily: "var(--font-body)" }}>
            <span>✨ <b>{stats.total || 0}</b> total candidates</span>
            <span>📈 Avg Score: <b>{((stats.avg_score || 0) * 100).toFixed(0)}</b></span>
            <span>📅 <b>{dates.length}</b> processing days</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          {/* ML Training Button */}
          <button
            onClick={() => navigate("/ml-training")}
            className="float-hover"
            style={{ padding: "10px 18px", background: "rgba(208,149,255,0.1)", color: "var(--primary-color)", borderRadius: 8, fontWeight: 600, fontSize: 14, border: "1px solid rgba(208,149,255,0.3)" }}
          >
            🧠 ML Training
          </button>


          {/* Role-Fit Scorer */}
          <button
            onClick={() => navigate("/role-fit")}
            className="float-hover"
            style={{ padding: "10px 18px", background: "rgba(29,158,117,0.08)", color: "#1D9E75", borderRadius: 8, fontWeight: 600, fontSize: 14, border: "1px solid rgba(29,158,117,0.25)" }}
          >
            🎯 Role-Fit Scorer
          </button>

          {/* CSV Export */}
          <button
            onClick={handleExportCSV}
            disabled={exporting}
            className="float-hover"
            style={{ padding: "10px 18px", background: "rgba(64,206,243,0.1)", color: "var(--secondary-color)", borderRadius: 8, fontWeight: 600, fontSize: 14, border: "1px solid rgba(64,206,243,0.2)" }}
          >
            {exporting ? "⏳ Exporting..." : "⬇️ Export CSV"}
          </button>

          {/* Compare (shows when 2+ shortlisted) */}
          {shortlisted.size >= 2 && (
            <button
              onClick={handleCompare}
              className="float-hover"
              style={{ padding: "10px 18px", background: "rgba(29,158,117,0.12)", color: "#1D9E75", borderRadius: 8, fontWeight: 600, fontSize: 14, border: "1px solid rgba(29,158,117,0.3)" }}
            >
              ⚖️ Compare {shortlisted.size > 2 ? "Top 2" : ""}
            </button>
          )}

          {/* Email shortlisted */}
          {shortlisted.size > 0 && (
            <button
              className="float-hover"
              onClick={() => setShowEmailer(true)}
              style={{ padding: "10px 20px", background: "linear-gradient(135deg, var(--primary-color), var(--primary-dim))", color: "#fff", borderRadius: 8, fontWeight: 600, fontSize: 14, boxShadow: "0 4px 15px rgba(208, 149, 255, 0.3)" }}
            >
              📧 Send to {shortlisted.size} Selected
            </button>
          )}

          <PipelineControl onComplete={() => { fetchCandidates(); fetchStats(); fetchWeeks(); fetchDates() }} />
        </div>
      </div>

      <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
        {/* Sidebar */}
        <div style={{ width: 300, display: "flex", flexDirection: "column", gap: 20 }}>

          <div className="glass-panel" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 16, color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>Time Period</h3>
            <WeekSelector weeks={weeks} selected={selectedWeek} onChange={handleQuickWeekChange} dates={dates} onDateSelect={handleDateSelect} onWeekRangeSelect={handleWeekRangeSelect} />
          </div>

          <div className="glass-panel" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 16, color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>Filters</h3>
            <FilterPanel filters={filters} setFilters={setFilters} stats={stats} />
          </div>

          {/* Saved Filter Presets */}
          <div className="glass-panel" style={{ padding: 20 }}>
            <SavedFilters currentFilters={filters} onLoad={(f) => setFilters(f)} />
          </div>

          <div className="glass-panel" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 16, color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>📧 Email Report</h3>
            <ReportExporter />
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1 }}>
          {dateMode && (
            <div style={{
              marginBottom: 16, padding: "10px 16px", borderRadius: 6,
              background: "rgba(64, 206, 243, 0.08)", border: "1px solid rgba(64, 206, 243, 0.2)",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontSize: 13, color: "var(--secondary-color)", fontWeight: 500 }}>
                🔍 Filtered by {dateMode.type === "date" ? `date: ${dateMode.value}` : `week: ${dateMode.value}`}
                {" "}— {candidates.length} candidate{candidates.length !== 1 ? "s" : ""}
              </span>
              <button onClick={() => { setDateMode(null); setSelectedWeek("all") }}
                style={{ fontSize: 12, padding: "4px 12px", borderRadius: 4, background: "var(--surface-high)", color: "var(--text-muted)", border: "1px solid var(--border-ghost)", cursor: "pointer" }}>
                ✕ Clear
              </button>
            </div>
          )}

          {loading
            ? (
              <div className="glass-panel" style={{ padding: 100, textAlign: "center" }}>
                <div className="spinner" style={{ width: 40, height: 40, border: "4px solid rgba(64, 206, 243, 0.2)", borderTopColor: "var(--secondary-color)", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 1s linear infinite" }}></div>
                <p style={{ color: "var(--text-muted)" }}>Initializing scan sequence...</p>
              </div>
            )
            : <CandidateTable candidates={candidates} shortlisted={shortlisted} onToggleShortlist={toggleShortlist} />
          }
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {showEmailer && (
        <EmailComposer candidates={shortlistedCandidates} onClose={() => setShowEmailer(false)} onSent={() => { setShowEmailer(false); setShortlisted(new Set()) }} />
      )}
    </div>
  )
}
