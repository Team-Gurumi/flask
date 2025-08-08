// src/pages/Home/ProviderDetailPage.tsx
import React from 'react';
import { useParams } from 'react-router-dom';

const ProviderDetailPage = () => {
  const { id } = useParams();
  return <h1>공급자 상세 페이지 (ID: {id})</h1>;
};

export default ProviderDetailPage;
