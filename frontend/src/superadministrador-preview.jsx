import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import SuperAdministrador from './pages/SuperAdministrador.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SuperAdministrador />
  </StrictMode>,
)