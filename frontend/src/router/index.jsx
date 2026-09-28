import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { Dashboard } from '../pages/Dashboard';
import { Companies } from '../pages/Companies';
import { CompanyWorkspace } from '../pages/CompanyWorkspace';
import { DutySlips } from '../pages/DutySlips';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'companies',
        element: <Companies />,
      },
      {
        path: 'companies/:id',
        element: <CompanyWorkspace />,
      },
      {
        path: 'duty-slips',
        element: <DutySlips />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
