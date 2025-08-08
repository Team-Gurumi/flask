import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import ProviderDetailPage from '../pages/ProviderDetailPage';
import ResultPage from '../pages/ResultPage';

const AppRouter = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/provider/:id" element={<ProviderDetailPage />} />
        <Route path="/result/:jobId" element={<ResultPage />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;
