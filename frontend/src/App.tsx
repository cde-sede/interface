import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ApiDocs from './components/ApiDocs';
import Admin from './components/Admin';
import Home from './components/Home';
import './App.css';

function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/" element={<Home />} />
				<Route path="/docs" element={<ApiDocs />} />
				<Route path="/admin" element={<Admin />} />
			</Routes>
		</BrowserRouter>
	);
}

export default App;
