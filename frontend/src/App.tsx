import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { CollegeDashboard } from './pages/CollegeDashboard';
import { StudentUploadPage } from './pages/StudentUploadPage';
import { UploadBatchesPage } from './pages/UploadBatchesPage';
import { StudentRecordsPage } from './pages/StudentRecordsPage';
import { ComplianceDashboard } from './pages/ComplianceDashboard';
import { VerificationPage } from './pages/VerificationPage';
import { AuditLogPage } from './pages/AuditLogPage';
import { DashboardLayout } from './layouts/DashboardLayout';
import { authService } from './services/api';
import { User } from './types';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => authService.getCurrentUser());

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Public login page */}
        <Route
          path="/login"
          element={
            currentUser ? (
              <Navigate
                to={
                  currentUser.role === 'compliance_officer'
                    ? '/compliance'
                    : currentUser.role === 'verifier'
                    ? '/verification'
                    : '/college-dashboard'
                }
                replace
              />
            ) : (
              <LoginPage onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        {/* Public QR Code Verification Direct Landing Page */}
        <Route
          path="/verify"
          element={
            <div className="min-h-screen bg-slate-900 text-slate-100 p-6 flex flex-col items-center justify-center">
              <div className="max-w-2xl w-full">
                <VerificationPage />
              </div>
            </div>
          }
        />

        {/* Protected Dashboard Routes */}
        <Route
          element={
            currentUser ? (
              <DashboardLayout currentUser={currentUser} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        >
          <Route
            index
            element={
              <Navigate
                to={
                  currentUser?.role === 'compliance_officer'
                    ? '/compliance'
                    : currentUser?.role === 'verifier'
                    ? '/verification'
                    : '/college-dashboard'
                }
                replace
              />
            }
          />
          <Route path="/college-dashboard" element={<CollegeDashboard currentUser={currentUser} />} />
          <Route path="/upload" element={<StudentUploadPage currentUser={currentUser} />} />
          <Route path="/batches" element={<UploadBatchesPage currentUser={currentUser} />} />
          <Route path="/students" element={<StudentRecordsPage currentUser={currentUser} />} />
          <Route path="/compliance" element={<ComplianceDashboard />} />
          <Route path="/verification" element={<VerificationPage />} />
          <Route path="/audit" element={<AuditLogPage />} />
        </Route>

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
