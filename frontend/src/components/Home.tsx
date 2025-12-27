import { useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import { ThemePicker } from './ThemePicker';
import { ToastNotification, ConfirmDialog, LoginForm } from './admin/components';
import type { Toast } from './admin/components';
import DSLRenderer from './admin/DSLRenderer';
import type { PageDSL, RichTextComponent } from './admin/dsl/types';
import './Home.css';

interface ConfirmDialogState {
	message: string;
	onConfirm: () => void;
	onCancel: () => void;
}

function Home() {
	const [socket, setSocket] = useState<Socket | null>(null);
	const [toasts, setToasts] = useState<Toast[]>([]);
	const [showLoginModal, setShowLoginModal] = useState(false);
	const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState | null>(null);

	const [authError, setAuthError] = useState<string | null>(null);
	const [loginError, setLoginError] = useState<string | null>(null);
	const [isLoggingIn, setIsLoggingIn] = useState(false);
	const [isAuthenticated, setIsAuthenticated] = useState(false);

	const [pageData, setPageData] = useState<PageDSL | null>(null);
	const [selectedPage] = useState<string>('home');

	const showToast = (message: string | RichTextComponent, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
		const id = Date.now();
		setToasts(prev => [...prev, { id, message, type }]);
		setTimeout(() => {
			setToasts(prev => prev.filter(t => t.id !== id));
		}, 5000);
	};

	const showConfirm = (message: string): Promise<boolean> => {
		return new Promise((resolve) => {
			setConfirmDialog({
				message,
				onConfirm: () => {
					setConfirmDialog(null);
					resolve(true);
				},
				onCancel: () => {
					setConfirmDialog(null);
					resolve(false);
				}
			});
		});
	};

	// Check if user is already authenticated
	useEffect(() => {
		const token = localStorage.getItem('auth_token');
		if (token) {
			setIsAuthenticated(true);
		} else {
			setAuthError('Authentication required. Please log in.');
		}
	}, []);

	// Fetch page data function
	const fetchPageData = () => {
		if (!selectedPage || authError) return;

		const token = localStorage.getItem('auth_token');
		if (!token) return;

		fetch(`/content/home`, {
			headers: {
				'Authorization': `Bearer ${token}`
			}
		})
			.then(res => {
				if (res.status === 401 || res.status === 403) {
					setAuthError('Session expired. Please log in again.');
					localStorage.removeItem('auth_token');
					return null;
				}
				return res.json();
			})
			.then(data => {
				if (data) setPageData(data);
			})
			.catch(err => console.error(`Failed to fetch ${selectedPage}:`, err));
	};

	// Fetch page data on mount
	useEffect(() => {
		fetchPageData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [selectedPage, authError]);

	// Socket.IO connection
	useEffect(() => {
		const token = localStorage.getItem('auth_token');

		const socketInstance: Socket = io({
			auth: token ? { token } : undefined
		});

		socketInstance.on('connect', () => {
			// console.log('[Socket.IO] Connected to server');
			socketInstance.emit('home');
			showToast('Connected to server', 'success');
			// Refetch page data when backend reconnects (e.g., after Flask restart)
			fetchPageData();
		});

		socketInstance.on('disconnect', (_reason) => {
			// console.log('[Socket.IO] Disconnected:', reason);
			showToast('Disconnected from server', 'warning');
		});

		socketInstance.on('connect_error', (error) => {
			console.error('[Socket.IO] Connection error:', error);
			showToast('Connection error', 'error');
		});

		setSocket(socketInstance);

		return () => {
			// console.log('[Socket.IO] Cleaning up connection');
			socketInstance.disconnect();
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const handleLogin = (username: string, password: string) => {
		setLoginError(null);
		setIsLoggingIn(true);

		fetch('/api/v1/auth/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username, password })
		})
			.then(res => res.json())
			.then(data => {
				if (data.error) {
					setLoginError(data.error);
					setIsLoggingIn(false);
				} else if (data.token) {
					localStorage.setItem('auth_token', data.token);
					setIsLoggingIn(false);
					setIsAuthenticated(true);
					setShowLoginModal(false);
					setAuthError(null);
					showToast('Login successful', 'success');
					// Reconnect socket with auth
					if (socket) {
						socket.disconnect();
						const newSocket = io({
							auth: { token: data.token }
						});
						newSocket.on('connect', () => {
							newSocket.emit('home');
						});
						setSocket(newSocket);
					}
				} else {
					setLoginError('Login failed. Please try again.');
					setIsLoggingIn(false);
				}
			})
			.catch(err => {
				setLoginError(`Login failed: ${err.message}`);
				setIsLoggingIn(false);
			});
	};

	const handleLogout = () => {
		localStorage.removeItem('auth_token');
		setIsAuthenticated(false);
		setAuthError('Authentication required. Please log in.');
		showToast('Logged out successfully', 'info');
		// Reconnect socket without auth
		if (socket) {
			socket.disconnect();
			const newSocket = io();
			newSocket.on('connect', () => {
				newSocket.emit('home');
			});
			setSocket(newSocket);
		}
	};

	return (
		<div className="home-page">
			<header className="home-header">
				<div className="header-content">
					<div className="header-text">
						<h1>Home</h1>
						<p>Welcome to the interface</p>
					</div>
					<div className="header-actions">
						<ThemePicker />
						{isAuthenticated ? (
							<button
								className="login-button"
								onClick={handleLogout}
							>
								Logout
							</button>
						) : (
							<button
								className="login-button"
								onClick={() => setShowLoginModal(true)}
							>
								Login
							</button>
						)}
					</div>
				</div>
			</header>

			<main className="home-content">
				{pageData ? (
					<DSLRenderer
						dsl={pageData}
						socket={socket}
						currentPage={selectedPage}
						onShowToast={showToast}
						onShowConfirm={showConfirm}
						onNavigate={() => {}}
						onRefresh={() => {}}
					/>
				) : authError ? (
					<div className="auth-error">
						<p>{authError}</p>
						<button onClick={() => setShowLoginModal(true)}>Login</button>
					</div>
				) : null}
			</main>

			{/* Login Modal */}
			{showLoginModal && !isAuthenticated && (
				<div className="login-modal-overlay" onClick={() => setShowLoginModal(false)}>
					<div className="login-modal" onClick={(e) => e.stopPropagation()}>
						<button
							className="modal-close"
							onClick={() => setShowLoginModal(false)}
						>
							×
						</button>
						<LoginForm
							authError={authError ?? ''}
							loginError={loginError ?? ''}
							isLoggingIn={isLoggingIn}
							onLogin={handleLogin}
						/>
					</div>
				</div>
			)}

			{/* Confirm Dialog */}
			{confirmDialog && (
				<ConfirmDialog
					message={confirmDialog.message}
					onConfirm={confirmDialog.onConfirm}
					onCancel={confirmDialog.onCancel}
				/>
			)}

			{/* Toast Notifications */}
			<ToastNotification
				toasts={toasts}
				onClose={(id) => setToasts(prev => prev.filter(t => t.id !== id))}
			/>
		</div>
	);
}

export default Home;
