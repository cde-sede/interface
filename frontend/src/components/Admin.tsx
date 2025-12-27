import { useState, useEffect, useRef } from 'react';
import './Admin.css';
import { ThemePicker } from './ThemePicker';
import { io, Socket } from 'socket.io-client';
import { ToastNotification, ConfirmDialog, LoginForm } from './admin/components';
import type { Toast } from './admin/components';
import DSLRenderer from './admin/DSLRenderer';
import type { PageDSL, RichTextComponent } from './admin/dsl/types';

interface MenuItem {
	id: string;
	label: string;
	icon: string;
}

interface MenuSection {
	id: string;
	label: string;
	items: MenuItem[];
}

interface MenuData {
	sections: MenuSection[];
}

interface PageData {
	title?: string;
	description?: string;
	[key: string]: any;
}

interface ConfirmDialogState {
	message: string;
	onConfirm: () => void;
	onCancel: () => void;
}

export default function Admin() {
	const [menu, setMenu] = useState<MenuSection[]>([]);
	const [selectedPage, setSelectedPage] = useState<string>('overview');
	const [pageData, setPageData] = useState<PageData | null>(null);
	const [loading, setLoading] = useState(false);
	const [refreshCounter, setRefreshCounter] = useState(0);
	const [authError, setAuthError] = useState<string | null>(null);
	const [loginError, setLoginError] = useState<string | null>(null);
	const [isLoggingIn, setIsLoggingIn] = useState(false);
	const [toasts, setToasts] = useState<Toast[]>([]);
	const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState | null>(null);
	const [menuRefreshTrigger, setMenuRefreshTrigger] = useState(0);
	const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
	const [socket, setSocket] = useState<Socket | null>(null);

	// Use ref to track current page for Socket.IO events
	const selectedPageRef = useRef(selectedPage);
	useEffect(() => {
		selectedPageRef.current = selectedPage;
	}, [selectedPage]);

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

	// Check authentication and load menu
	useEffect(() => {
		const token = localStorage.getItem('auth_token');
		if (!token) {
			setAuthError('Authentication required. Please log in.');
			return;
		}

		fetch('/admin/menu', {
			headers: {
				'Authorization': `Bearer ${token}`
			}
		})
			.then(res => {
				if (res.status === 401) {
					setAuthError('Authentication required. Please log in.');
					localStorage.removeItem('auth_token');
					return null;
				}
				if (res.status === 403) {
					setAuthError('Admin privileges required. You do not have access to this page.');
					return null;
				}
				if (!res.ok) {
					throw new Error('Failed to fetch menu');
				}
				return res.json();
			})
			.then((data: MenuData | null) => {
				if (data) {
					setMenu(data.sections);
					// Clear auth error on successful menu load
					if (authError) setAuthError(null);
				}
			})
			.catch(err => {
				console.error('Failed to fetch menu:', err);
				setAuthError('Failed to load admin panel. Please try again.');
			});
	}, [menuRefreshTrigger]);

	useEffect(() => {
		if (!selectedPage || authError) return;

		const token = localStorage.getItem('auth_token');
		if (!token) return;

		// Only show loading spinner if we don't have data yet (initial load)
		// This prevents blinking during refreshes
		if (!pageData) {
			setLoading(true);
		}

		fetch(`/admin/${selectedPage}`, {
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
			.catch(err => console.error(`Failed to fetch ${selectedPage}:`, err))
			.finally(() => setLoading(false));
	}, [selectedPage, authError, refreshCounter]);

	// Socket.IO connection for real-time updates
	// Keep connection persistent across page changes
	useEffect(() => {
		if (authError) {
			setSocket(null);
			return;
		}

		const token = localStorage.getItem('auth_token');
		if (!token) {
			setSocket(null);
			return;
		}

		const socketInstance: Socket = io({
			auth: { token }
		});

		socketInstance.on('connect', () => {
			// console.log('[Socket.IO] Connected, joining page room:', selectedPageRef.current);
			// Join the current page room on connect
			if (selectedPageRef.current) {
				socketInstance.emit('join_page', { page: selectedPageRef.current });
			}
		});

		socketInstance.on('disconnect', (_reason) => {
			// console.log('Socket.IO disconnected:', reason);
		});

		socketInstance.on('connect_error', (error) => {
			console.error('[Socket.IO] Connection error:', error);
		});

		// Add catch-all listener for debugging
		socketInstance.onAny((_eventName, ..._args) => {
			// console.log('[Socket.IO] Received ANY event:', eventName, args);
		});

		// Store socket in state for DSLRenderer to use
		setSocket(socketInstance);

		// Store socket in a ref for page change effect
		(window as any).__adminSocket = socketInstance;

		return () => {
			// console.log('Cleaning up Socket.IO connection');
			socketInstance.disconnect();
			delete (window as any).__adminSocket;
			setSocket(null);
		};
	}, [authError]);

	// Handle page room changes when selectedPage changes
	useEffect(() => {
		const socket = (window as any).__adminSocket;
		if (!socket || !socket.connected) return;

		// Leave the previous page room and join the new one
		// console.log('[Socket.IO] Switching to page:', selectedPage);
		socket.emit('leave_page', { page: selectedPageRef.current });
		socket.emit('join_page', { page: selectedPage });
	}, [selectedPage]);

	// Auto-refresh metrics every 3 seconds
	useEffect(() => {
		if (selectedPage !== 'metrics' || authError) return;

		const token = localStorage.getItem('auth_token');
		if (!token) return;

		const refreshMetrics = () => {
			fetch(`/admin/metrics`, {
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
				.catch(err => console.error('Failed to refresh metrics:', err));
		};

		// Refresh every 3 seconds
		const intervalId = setInterval(refreshMetrics, 500);

		return () => {
			clearInterval(intervalId);
		};
	}, [selectedPage, authError]);

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
					if (data.user && data.user.level < 1) {
						setLoginError('Admin privileges required. You do not have access to this page.');
						setIsLoggingIn(false);
						return;
					}
					localStorage.setItem('auth_token', data.token);
					setIsLoggingIn(false);
					// Trigger menu refresh
					setMenuRefreshTrigger(prev => prev + 1);
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

	const renderContent = () => {
		if (authError) {
			return (
				<LoginForm
					authError={authError}
					loginError={loginError}
					isLoggingIn={isLoggingIn}
					onLogin={handleLogin}
				/>
			);
		}

		if (loading) {
			return <div className="loading-state">Loading...</div>;
		}

		if (!pageData) {
			return <div className="empty-state">No data available</div>;
		}

		// Check if this is a DSL-based page
		if (pageData.type === 'page') {
			return (
				<DSLRenderer
					dsl={pageData as PageDSL}
					socket={socket}
					currentPage={selectedPage}
					onShowToast={showToast}
					onShowConfirm={showConfirm}
					onNavigate={(page) => setSelectedPage(page)}
					onRefresh={() => setRefreshCounter(prev => prev + 1)}
				/>
			);
		}

		// All pages should now use DSL
		// If we reach here, the page doesn't have DSL implementation yet
		return (
			<div className="page-content">
				<div className="page-header">
					<h2>{pageData?.title || 'Page Not Implemented'}</h2>
					<p className="page-description">
						{pageData?.description || `This page (${selectedPage}) needs to be migrated to DSL.`}
					</p>
				</div>
				{pageData?.error && (
					<div className="alert alert-error" style={{ margin: '2rem' }}>
						{pageData.error}
					</div>
				)}
			</div>
		);
	};

	// All old render functions and handlers removed - pages now use DSL

	return (
		<div className="admin-panel">
			<header className="admin-header">
				<div className="header-content">
					<div className="header-text">
						<h1>Admin Panel</h1>
						<p>System administration and management</p>
					</div>
					<ThemePicker />
				</div>
			</header>

			<div className="admin-content">
				<aside className={`admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
					<button
						className="sidebar-toggle"
						onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
						aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
					>
						{sidebarCollapsed ? '▶' : '◀'}
					</button>
					<nav className="admin-menu">
						{menu.map(section => (
							<div key={section.id} className="menu-section">
								<h3 className="menu-section-title">{section.label}</h3>
								<div className="menu-items">
									{section.items.map(item => (
										<div
											key={item.id}
											className={`menu-item ${selectedPage === item.id ? 'active' : ''}`}
											onClick={() => setSelectedPage(item.id)}
											title={sidebarCollapsed ? item.label : undefined}
										>
											{sidebarCollapsed ? (
												<span className="menu-item-short">{item.label.charAt(0).toUpperCase()}</span>
											) : (
													<span className="menu-item-label">{item.label}</span>
												)}
										</div>
									))}
								</div>
							</div>
						))}
					</nav>
				</aside>

				<main className={`admin-main ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
					{renderContent()}
				</main>
			</div>

			{/* Toast Notifications */}
			<ToastNotification
				toasts={toasts}
				onClose={(id) => setToasts(prev => prev.filter(t => t.id !== id))}
			/>

			{/* Confirmation Dialog */}
			{confirmDialog && <ConfirmDialog {...confirmDialog} />}
		</div>
	);
}
