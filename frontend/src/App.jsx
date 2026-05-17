import { Routes, Route } from "react-router-dom"
import Dashboard from "./pages/Dashboard"
import CandidateDetails from "./pages/CandidateDetails"
import MLTraining from "./pages/MLTraining"
import CompareView from "./pages/CompareView"
import EnrichmentView from "./pages/EnrichmentView"
import DuplicateDetector from "./pages/DuplicateDetector"
import RoleFitPage from "./pages/RoleFitPage"
import CEOProfilePage from "./pages/CEOProfilePage"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/candidate/:login" element={<CandidateDetails />} />
      <Route path="/ml-training" element={<MLTraining />} />
      <Route path="/compare" element={<CompareView />} />
      <Route path="/enrich/:login" element={<EnrichmentView />} />
      <Route path="/duplicates" element={<DuplicateDetector />} />
      <Route path="/role-fit" element={<RoleFitPage />} />
      <Route path="/profile/:login" element={<CEOProfilePage />} />
    </Routes>
  )
}