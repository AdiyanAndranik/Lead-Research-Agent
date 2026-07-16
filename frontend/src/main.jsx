import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import NewRun from './pages/NewRun'
import RunDetail from './pages/RunDetail'
import EmailReview from './pages/EmailReview'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewRun />} />
          <Route path="/runs/:runId" element={<RunDetail />} />
          <Route path="/runs/:runId/review" element={<EmailReview />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </StrictMode>
)

