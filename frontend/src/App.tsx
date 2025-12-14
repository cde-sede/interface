import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ApiDocs from './components/ApiDocs';
import Admin from './components/Admin';
import './App.css';

function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/docs" element={<ApiDocs />} />
				<Route path="/admin" element={<Admin />} />
				<Route path="/" element={<Navigate to="/docs" replace />} />
			</Routes>
		</BrowserRouter>
	);
}

export default App;
