import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

export const lightTheme = {
  '--bg-color': '#f8f9fa',
  '--bg-light': '#ffffff',
  '--bg-dark': '#212529',
  '--bg-dark-lighter': '#343a40',
  '--text-color': '#212529',
  '--text-color-secondary': '#6c757d',
  '--border-color': '#dee2e6',
  '--border-color-dark': '#495057',
  '--primary-color': '#4070f4',
  '--primary-color-dark': '#2952c8',
  '--secondary-color': '#6c757d',
  '--success-color': '#28a745',
  '--danger-color': '#dc3545',
  '--warning-color': '#ffc107',
  '--info-color': '#17a2b8',
  '--shadow-color': 'rgba(0, 0, 0, 0.1)',
};

export const darkTheme = {
  '--bg-color': '#212529',
  '--bg-light': '#343a40',
  '--bg-dark': '#121416',
  '--bg-dark-lighter': '#2c3237',
  '--text-color': '#f8f9fa',
  '--text-color-secondary': '#adb5bd',
  '--border-color': '#495057',
  '--border-color-dark': '#6c757d',
  '--primary-color': '#4070f4',
  '--primary-color-dark': '#2952c8',
  '--secondary-color': '#adb5bd',
  '--success-color': '#28a745',
  '--danger-color': '#dc3545',
  '--warning-color': '#ffc107',
  '--info-color': '#17a2b8',
  '--shadow-color': 'rgba(0, 0, 0, 0.3)',
};

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button 
      className={`theme-toggle-modern ${isDark ? 'dark' : 'light'}`}
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <div className="toggle-track">
        <div className="toggle-thumb">
          {isDark ? (
            <svg className="toggle-icon moon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg className="toggle-icon sun" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </div>
      </div>
    </button>
  );
};

export default ThemeToggle; 