// src/pages/Mypage/ResultPage.tsx
import React from 'react';
import { useParams } from 'react-router-dom';

const ResultPage = () => {
  const { jobId } = useParams();
  return <h1>작업 결과 페이지 (Job ID: {jobId})</h1>;
};

export default ResultPage;
