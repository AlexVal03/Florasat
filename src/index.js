// This file is the entry point of the application. It initializes the application, sets up the main components, and handles the rendering of the user interface.

import React from 'react';
import ReactDOM from 'react-dom';
import App from './components/App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);