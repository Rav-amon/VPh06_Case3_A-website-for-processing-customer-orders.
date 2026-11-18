import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AdminLoginPage } from '@/pages/admin/AdminLoginPage';
import { AdminPanelPage } from '@/pages/admin/AdminPanelPage';
import { HomePage } from '@/pages/HomePage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<AdminPanelPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
