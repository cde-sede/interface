import { useState, useEffect } from 'react';
import './Admin.css';
import { ThemePicker } from './ThemePicker';
import {
	BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
	PieChart, Pie, Cell
} from 'recharts';
import { io, Socket } from 'socket.io-client';
import { ToastNotification, ConfirmDialog, LoginForm } from './admin/components';
import type { Toast } from './admin/components';
import { LogsPage, OverviewPage, ApiKeysPage } from './admin/pages';

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
	const [selectedTask, setSelectedTask] = useState<any>(null);
	const [showCreateTask, setShowCreateTask] = useState(false);
	const [editMode, setEditMode] = useState(false);
	const [editedSettings, setEditedSettings] = useState<any>({});
	const [authError, setAuthError] = useState<string | null>(null);
	const [loginError, setLoginError] = useState<string | null>(null);
	const [isLoggingIn, setIsLoggingIn] = useState(false);
	const [toasts, setToasts] = useState<Toast[]>([]);
	const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState | null>(null);

	const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
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
				}
			})
			.catch(err => {
				console.error('Failed to fetch menu:', err);
				setAuthError('Failed to load admin panel. Please try again.');
			});
	}, []);

	useEffect(() => {
		if (!selectedPage || authError) return;

		const token = localStorage.getItem('auth_token');
		if (!token) return;

		setLoading(true);
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
	}, [selectedPage, authError]);

	// Socket.IO connection for real-time updates
	useEffect(() => {
		if (authError) return;

		const token = localStorage.getItem('auth_token');
		if (!token) return;

		const socket: Socket = io({
			auth: { token }
		});

		socket.on('connect', () => {
			console.log('Socket.IO connected');
		});

		socket.on('refresh_page', (data: { page: string }) => {
			console.log('Received refresh_page event:', data);
			if (data.page === selectedPage) {
				// Reload current page data (without showing loading state for seamless updates)
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
					.catch(err => console.error(`Failed to refresh ${selectedPage}:`, err));
			}
		});

		socket.on('disconnect', () => {
			console.log('Socket.IO disconnected');
		});

		return () => {
			socket.disconnect();
		};
	}, [selectedPage, authError]);

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
					setAuthError(null);
					setIsLoggingIn(false);
					window.location.reload();
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

		switch (selectedPage) {
			case 'overview':
				return <OverviewPage title={pageData?.title} stats={pageData?.stats} services={pageData?.services} />;
			case 'services':
				return renderServices();
			case 'tasks':
				return renderTasks();
			case 'settings':
				return renderSettings();
			case 'database':
				return renderDatabase();
			case 'metrics':
				return renderMetrics();
			case 'logs':
				return <LogsPage logs={pageData?.logs} title={pageData?.title} description={pageData?.description} />;
			case 'api-keys':
				return (
					<ApiKeysPage
						keys={pageData?.keys}
						levels={pageData?.levels}
						title={pageData?.title}
						description={pageData?.description}
						onRefresh={() => setSelectedPage('api-keys')}
						onShowToast={showToast}
						onShowConfirm={showConfirm}
					/>
				);
			default:
				return renderGeneric();
		}
	};

	const handleReloadService = async (modulePath: string, serviceName: string) => {
		const token = localStorage.getItem('auth_token');

		const confirmed = await showConfirm(`Reload service "${serviceName}"?`);
		if (!confirmed) return;

		fetch('/admin/reload', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`
			},
			body: JSON.stringify({ target: modulePath })
		})
			.then(res => {
				if (res.status === 401 || res.status === 403) {
					setAuthError('Session expired. Please log in again.');
					return null;
				}
				return res.json();
			})
			.then(data => {
				if (data) {
					showToast(data.message || 'Service reloaded successfully', 'success');
					setSelectedPage('services');
				}
			})
			.catch(err => showToast(`Error: ${err}`, 'error'));
	};

	const renderServices = () => (
		<div className="page-content">
			<div className="page-header">
				<div>
					<h2>{pageData?.title}</h2>
					{pageData?.description && <p className="page-description">{pageData.description}</p>}
				</div>
				{pageData?.actions && (
					<div className="header-actions">
						{pageData.actions.map((action: any) => (
							<button
								key={action.id}
								className="action-button"
								onClick={async () => {
									const token = localStorage.getItem('auth_token');
									const confirmed = await showConfirm('Reload all services? This may cause temporary disruption.');
									if (!confirmed) return;

									fetch(`${action.endpoint}`, {
										method: action.method,
										headers: {
											'Content-Type': 'application/json',
											'Authorization': `Bearer ${token}`
										},
										body: JSON.stringify(action.data)
									})
										.then(res => {
											if (res.status === 401 || res.status === 403) {
												setAuthError('Session expired. Please log in again.');
												return null;
											}
											return res.json();
										})
										.then(data => {
											if (data) {
												showToast(data.message || 'Services reloaded successfully', 'success');
												setSelectedPage('services');
											}
										})
										.catch(err => showToast(`Error: ${err}`, 'error'));
								}}
							>
								{action.label}
							</button>
						))}
					</div>
				)}
			</div>

			<div className="table-container">
				<table className="data-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>Type</th>
							<th>Status</th>
							<th>Actions</th>
						</tr>
					</thead>
					<tbody>
						{pageData?.services?.map((service: any) => (
							<tr key={service.name}>
								<td className="monospace">{service.name}</td>
								<td className="text-muted">{service.type}</td>
								<td>
									<span className={`status-badge ${service.ready ? 'status-ready' : 'status-error'}`}>
										{service.ready ? 'Ready' : service.error || 'Not Ready'}
									</span>
								</td>
								<td>
									<button
										className="table-action-button"
										onClick={() => handleReloadService(service.module_path, service.name)}
										title={`Reload ${service.name}`}
									>
										Reload
									</button>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);

	const handleCreateTask = (taskName: string, params: string) => {
		try {
			const parsedParams = params ? JSON.parse(params) : {};
			const token = localStorage.getItem('auth_token');

			fetch('/admin/tasks', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({ task_name: taskName, params: parsedParams })
			})
				.then(res => {
					if (res.status === 401 || res.status === 403) {
						setAuthError('Session expired. Please log in again.');
						return null;
					}
					return res.json();
				})
				.then(data => {
					if (!data) return;
					if (data.error) {
						showToast(`Error: ${data.error}`, 'error');
					} else {
						showToast(`Task created: ${data.task_id}`, 'success');
						setShowCreateTask(false);
						setSelectedPage('tasks');
					}
				})
				.catch(err => showToast(`Error: ${err}`, 'error'));
		} catch (e) {
			showToast(`Invalid JSON params: ${e}`, 'error');
		}
	};

	const getStatusBadgeClass = (status: string) => {
		switch (status?.toLowerCase()) {
			case 'completed': return 'status-ready';
			case 'running': return 'status-running';
			case 'pending': return 'status-pending';
			case 'failed': return 'status-error';
			case 'timeout': return 'status-error';
			default: return '';
		}
	};

	const formatDate = (timestamp: number) => {
		if (!timestamp) return 'N/A';
		return new Date(timestamp * 1000).toLocaleString();
	};

	const handleRequeueTask = async (taskId: number, taskName: string) => {
		const token = localStorage.getItem('auth_token');

		fetch(`/admin/tasks/${taskId}/requeue`, {
			method: 'POST',
			headers: {
				'Authorization': `Bearer ${token}`
			}
		})
			.then(res => {
				if (res.status === 401 || res.status === 403) {
					setAuthError('Session expired. Please log in again.');
					return null;
				}
				return res.json();
			})
			.then(data => {
				if (!data) return;
				if (data.error) {
					showToast(`Error: ${data.error}`, 'error');
				} else {
					showToast(`Task "${taskName}" requeued successfully`, 'success');
					setSelectedPage('tasks');
				}
			})
			.catch(err => showToast(`Error: ${err}`, 'error'));
	};

	const renderTasks = () => (
		<div className="page-content">
			<div className="page-header">
				<div>
					<h2>{pageData?.title}</h2>
					{pageData?.description && <p className="page-description">{pageData.description}</p>}
				</div>
				<button className="action-button" onClick={() => setShowCreateTask(true)}>
					Create Task
				</button>
			</div>

			{pageData?.status && (
				<div className="content-section">
					<h3>Status</h3>
					<div className="info-grid">
						<div className="info-item">
							<span className="info-label">Workers Enabled</span>
							<span className="info-value">{pageData.status.workers_enabled ? 'Yes' : 'No'}</span>
						</div>
						<div className="info-item">
							<span className="info-label">Worker Count</span>
							<span className="info-value">{pageData.status.worker_count}</span>
						</div>
						<div className="info-item">
							<span className="info-label">System Status</span>
							<span className="info-value">{pageData.status.paused ? 'Paused' : 'Running'}</span>
						</div>
						<div className="info-item">
							<span className="info-label">Running Tasks</span>
							<span className="info-value">{pageData.status.running_tasks}</span>
						</div>
					</div>
				</div>
			)}

			{pageData?.tasks && (
				<div className="content-section">
					<h3>Recent Tasks</h3>
					<div className="table-container">
						<table className="data-table">
							<thead>
								<tr>
									<th>ID</th>
									<th>Name</th>
									<th>Status</th>
									<th>Created</th>
									<th>Started</th>
									<th>Completed</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{pageData.tasks.map((task: any) => (
									<tr key={task.id}>
										<td className="monospace" onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>{task.id}</td>
										<td onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>{task.name}</td>
										<td onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>
											<span className={`status-badge ${getStatusBadgeClass(task.status)}`}>
												{task.status}
											</span>
										</td>
										<td className="text-muted" onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>{formatDate(task.created_at)}</td>
										<td className="text-muted" onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>{formatDate(task.started_at)}</td>
										<td className="text-muted" onClick={() => setSelectedTask(task)} style={{ cursor: 'pointer' }}>{formatDate(task.completed_at)}</td>
										<td>
											{task.status?.toUpperCase() === 'PENDING' && (
												<button
													className="table-action-button"
													onClick={(e) => {
														e.stopPropagation();
														handleRequeueTask(task.id, task.name);
													}}
													title="Requeue this task"
												>
													Requeue
												</button>
											)}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				</div>
			)}

			{pageData?.actions && (
				<div className="content-section">
					<h3>Actions</h3>
					<div className="actions-grid">
						{pageData.actions.map((action: any) => (
							<button
								key={action.id}
								className="action-button"
								onClick={() => {
									const token = localStorage.getItem('auth_token');
									fetch(`${action.endpoint}`, {
										method: action.method,
										headers: {
											'Authorization': `Bearer ${token}`
										}
									})
										.then(res => {
											if (res.status === 401 || res.status === 403) {
												setAuthError('Session expired. Please log in again.');
												return null;
											}
											return res.json();
										})
										.then(data => {
											if (data) {
												showToast(JSON.stringify(data, null, 2), 'info');
												setSelectedPage('tasks');
											}
										})
										.catch(err => showToast(`Error: ${err}`, 'error'));
								}}
							>
								{action.label}
							</button>
						))}
					</div>
				</div>
			)}

			{selectedTask && (
				<div className="modal-overlay" onClick={() => setSelectedTask(null)}>
					<div className="modal-content" onClick={(e) => e.stopPropagation()}>
						<div className="modal-header">
							<h3>Task Details: {selectedTask.name}</h3>
							<button className="modal-close" onClick={() => setSelectedTask(null)}>×</button>
						</div>
						<div className="modal-body">
							<div className="info-grid">
								<div className="info-item">
									<span className="info-label">ID</span>
									<span className="info-value">{selectedTask.id}</span>
								</div>
								<div className="info-item">
									<span className="info-label">Status</span>
									<span className={`status-badge ${getStatusBadgeClass(selectedTask.status)}`}>
										{selectedTask.status}
									</span>
								</div>
								<div className="info-item">
									<span className="info-label">Priority</span>
									<span className="info-value">{selectedTask.priority}</span>
								</div>
								<div className="info-item">
									<span className="info-label">Timeout</span>
									<span className="info-value">{selectedTask.timeout || 'None'}</span>
								</div>
							</div>
							<div className="detail-section">
								<h4>Timestamps</h4>
								<div className="info-grid">
									<div className="info-item">
										<span className="info-label">Created</span>
										<span className="info-value">{formatDate(selectedTask.created_at)}</span>
									</div>
									<div className="info-item">
										<span className="info-label">Started</span>
										<span className="info-value">{formatDate(selectedTask.started_at)}</span>
									</div>
									<div className="info-item">
										<span className="info-label">Completed</span>
										<span className="info-value">{formatDate(selectedTask.completed_at)}</span>
									</div>
								</div>
							</div>
							{selectedTask.params && (
								<div className="detail-section">
									<h4>Parameters</h4>
									<pre className="json-display">
										{JSON.stringify(
											typeof selectedTask.params === 'string'
												? JSON.parse(selectedTask.params)
												: selectedTask.params,
											null,
											2
										)}
									</pre>
								</div>
							)}
							{selectedTask.result && (
								<div className="detail-section">
									<h4>Result</h4>
									<pre className="json-display">
										{JSON.stringify(
											typeof selectedTask.result === 'string'
												? JSON.parse(selectedTask.result)
												: selectedTask.result,
											null,
											2
										)}
									</pre>
								</div>
							)}
							{selectedTask.error && (
								<div className="detail-section">
									<h4>Error</h4>
									<pre className="json-display error-display">{selectedTask.error}</pre>
								</div>
							)}
							{selectedTask.traceback && (
								<div className="detail-section">
									<h4>Traceback</h4>
									<pre className="json-display error-display">{selectedTask.traceback}</pre>
								</div>
							)}
						</div>
					</div>
				</div>
			)}

			{showCreateTask && (
				<div className="modal-overlay" onClick={() => setShowCreateTask(false)}>
					<div className="modal-content" onClick={(e) => e.stopPropagation()}>
						<div className="modal-header">
							<h3>Create New Task</h3>
							<button className="modal-close" onClick={() => setShowCreateTask(false)}>×</button>
						</div>
						<div className="modal-body">
							<form onSubmit={(e) => {
								e.preventDefault();
								const formData = new FormData(e.currentTarget);
								handleCreateTask(
									formData.get('task_name') as string,
									formData.get('params') as string
								);
							}}>
								<div className="form-group">
									<label>Task Name</label>
									<select name="task_name" required>
										<option value="">Select a task...</option>
										{pageData?.registered_tasks?.map((taskName: string) => (
											<option key={taskName} value={taskName}>{taskName}</option>
										))}
									</select>
								</div>
								<div className="form-group">
									<label>Parameters (JSON)</label>
									<textarea
										name="params"
										rows={6}
										placeholder='{"key": "value"}'
										defaultValue="{}"
									/>
								</div>
								<div className="form-actions">
									<button type="button" className="action-button secondary" onClick={() => setShowCreateTask(false)}>
										Cancel
									</button>
									<button type="submit" className="action-button">
										Create Task
									</button>
								</div>
							</form>
						</div>
					</div>
				</div>
			)}
		</div>
	);

	const handleSaveSettings = () => {
		const token = localStorage.getItem('auth_token');

		fetch('/admin/settings', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`
			},
			body: JSON.stringify(editedSettings)
		})
			.then(res => {
				if (res.status === 401 || res.status === 403) {
					setAuthError('Session expired. Please log in again.');
					return null;
				}
				return res.json();
			})
			.then(data => {
				if (!data) return;
				if (data.error) {
					showToast(`Error: ${data.error}`, 'error');
				} else {
					showToast('Settings updated successfully. Restart required for changes to take effect.', 'success');
					setEditMode(false);
					setEditedSettings({});
					setSelectedPage('settings');
				}
			})
			.catch(err => showToast(`Error: ${err}`, 'error'));
	};

	const renderSettingInput = (key: string, setting: any, currentValue: any) => {
		const value = editedSettings[key] !== undefined ? editedSettings[key] : currentValue;

		switch (setting.type) {
			case 'boolean':
				return (
					<select
						value={value?.toString()}
						onChange={(e) => setEditedSettings({ ...editedSettings, [key]: e.target.value === 'true' })}
					>
						<option value="true">true</option>
						<option value="false">false</option>
					</select>
				);
			case 'integer':
				return (
					<input
						type="number"
						value={value}
						onChange={(e) => setEditedSettings({ ...editedSettings, [key]: parseInt(e.target.value) })}
					/>
				);
			case 'string':
				return (
					<input
						type="text"
						value={value}
						onChange={(e) => setEditedSettings({ ...editedSettings, [key]: e.target.value })}
					/>
				);
			default:
				return (
					<textarea
						rows={3}
						value={JSON.stringify(value)}
						onChange={(e) => {
							try {
								setEditedSettings({ ...editedSettings, [key]: JSON.parse(e.target.value) });
							} catch (err) {
								// Invalid JSON, keep as string
							}
						}}
					/>
				);
		}
	};

	const renderSettings = () => (
		<div className="page-content">
			<div className="page-header">
				<div>
					<h2>{pageData?.title}</h2>
					{pageData?.description && <p className="page-description">{pageData.description}</p>}
				</div>
				<div className="header-actions">
					{!editMode ? (
						<button className="action-button" onClick={() => setEditMode(true)}>
							Edit Settings
						</button>
					) : (
						<>
							<button className="action-button secondary" onClick={() => {
								setEditMode(false);
								setEditedSettings({});
							}}>
								Cancel
							</button>
							<button className="action-button" onClick={handleSaveSettings}>
								Save Changes
							</button>
						</>
					)}
				</div>
			</div>

			{pageData?.schema && (
				<div className="settings-list">
					{Object.entries(pageData.schema).map(([key, setting]: [string, any]) => (
						<div key={key} className="setting-item">
							<div className="setting-header">
								<span className="setting-key">{key}</span>
								<span className="setting-type">{setting.type}</span>
							</div>
							<p className="setting-description">{setting.description}</p>
							{editMode ? (
								<div className="setting-edit">
									<label className="value-label">Value:</label>
									{renderSettingInput(key, setting, pageData.current?.[key])}
								</div>
							) : (
								<>
									<div className="setting-value">
										<span className="value-label">Current:</span>
										<code>{JSON.stringify(pageData.current?.[key])}</code>
									</div>
									{setting.default !== undefined && (
										<div className="setting-default">
											<span className="value-label">Default:</span>
											<code>{JSON.stringify(setting.default)}</code>
										</div>
									)}
								</>
							)}
						</div>
					))}
				</div>
			)}
		</div>
	);

	const renderDatabase = () => (
		<div className="page-content">
			<h2>{pageData?.title}</h2>
			{pageData?.description && <p className="page-description">{pageData.description}</p>}

			{pageData?.info && (
				<div className="content-section">
					<h3>Database Information</h3>
					<div className="info-grid">
						<div className="info-item">
							<span className="info-label">Path</span>
							<span className="info-value monospace">{pageData.info.path}</span>
						</div>
						<div className="info-item">
							<span className="info-label">Type</span>
							<span className="info-value">{pageData.info.type}</span>
						</div>
					</div>
				</div>
			)}

			{pageData?.actions && (
				<div className="content-section">
					<h3>Actions</h3>
					<div className="actions-list">
						{pageData.actions.map((action: any) => (
							<div key={action.id} className="action-card">
								<div className="action-info">
									<h4>{action.label}</h4>
									<p>{action.description}</p>
								</div>
								<button className="action-button">Execute</button>
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	);

	const renderMetrics = () => {
		// Prepare chart data
		const topEndpoints = pageData?.endpoints?.slice(0, 10) || [];
		const requestChartData = topEndpoints.map((ep: any) => ({
			name: ep.endpoint.length > 30 ? ep.endpoint.substring(0, 30) + '...' : ep.endpoint,
			requests: ep.request_count,
			errors: ep.error_count
		}));

		const responseTimeChartData = topEndpoints.slice(0, 8).map((ep: any) => ({
			name: ep.endpoint.length > 25 ? ep.endpoint.substring(0, 25) + '...' : ep.endpoint,
			avg: parseFloat(ep.avg_response_time),
			p95: parseFloat(ep.p95_response_time),
			p99: parseFloat(ep.p99_response_time)
		}));

		// Aggregate status codes across all endpoints
		const statusCodeMap: Record<string, number> = {};
		pageData?.endpoints?.forEach((ep: any) => {
			Object.entries(ep.status_codes || {}).forEach(([code, count]: [string, any]) => {
				statusCodeMap[code] = (statusCodeMap[code] || 0) + count;
			});
		});
		const statusCodeChartData = Object.entries(statusCodeMap).map(([code, count]) => ({
			name: `${code}`,
			value: count
		}));

		const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

		return (
			<div className="page-content">
				<h2>{pageData?.title}</h2>
				{pageData?.description && <p className="page-description">{pageData.description}</p>}

				{pageData?.error && (
					<div className="content-section">
						<p className="error-message">{pageData.error}</p>
					</div>
				)}

				{pageData?.overview && (
					<div className="content-section">
						<h3>Overview</h3>
						<div className="stats-grid">
							<div className="stat-card">
								<div className="stat-label">Total Requests</div>
								<div className="stat-value">{pageData.overview.total_requests.toLocaleString()}</div>
							</div>
							<div className="stat-card">
								<div className="stat-label">Total Errors</div>
								<div className="stat-value">{pageData.overview.total_errors.toLocaleString()}</div>
							</div>
							<div className="stat-card">
								<div className="stat-label">Active Requests</div>
								<div className="stat-value">{pageData.overview.active_requests}</div>
							</div>
							<div className="stat-card">
								<div className="stat-label">Uptime</div>
								<div className="stat-value">{pageData.overview.uptime}</div>
							</div>
							<div className="stat-card">
								<div className="stat-label">Error Rate</div>
								<div className="stat-value">{pageData.overview.error_rate}</div>
							</div>
						</div>
					</div>
				)}

				{requestChartData.length > 0 && (
					<div className="content-section">
						<h3>Top Endpoints by Request Count</h3>
						<ResponsiveContainer width="100%" height={300}>
							<BarChart data={requestChartData} layout="vertical" margin={{ left: 150, right: 20, top: 25, bottom: 20 }}>
								<CartesianGrid strokeDasharray="3 3" stroke="var(--theme-card-border)" />
								<XAxis type="number" stroke="var(--theme-main-text-muted)" />
								<YAxis type="category" dataKey="name" stroke="var(--theme-main-text-muted)" width={140} />
								<Tooltip
									contentStyle={{
										backgroundColor: 'var(--theme-card-bg)',
										border: '1px solid var(--theme-card-border)',
										borderRadius: '8px',
										color: 'var(--theme-main-text)'
									}}
								/>
								<Legend />
								<Bar dataKey="requests" fill="#3b82f6" name="Requests" />
								<Bar dataKey="errors" fill="#ef4444" name="Errors" />
							</BarChart>
						</ResponsiveContainer>
					</div>
				)}

				{responseTimeChartData.length > 0 && (
					<div className="content-section">
						<h3>Response Times (ms)</h3>
						<ResponsiveContainer width="100%" height={380}>
							<BarChart data={responseTimeChartData} margin={{ left: 20, right: 20, top: 5, bottom: 100 }}>
								<CartesianGrid strokeDasharray="3 3" stroke="var(--theme-card-border)" />
								<XAxis
									dataKey="name"
									stroke="var(--theme-main-text-muted)"
									angle={-45}
									textAnchor="end"
									interval={0}
									height={100}
									tick={{ fontSize: 12 }}
								/>
								<YAxis stroke="var(--theme-main-text-muted)" />
								<Tooltip
									contentStyle={{
										backgroundColor: 'var(--theme-card-bg)',
										border: '1px solid var(--theme-card-border)',
										borderRadius: '8px',
										color: 'var(--theme-main-text)'
									}}
								/>
								<Legend wrapperStyle={{ paddingTop: '10px' }} />
								<Bar dataKey="avg" fill="#10b981" name="Average" />
								<Bar dataKey="p95" fill="#f59e0b" name="P95" />
								<Bar dataKey="p99" fill="#ef4444" name="P99" />
							</BarChart>
						</ResponsiveContainer>
					</div>
				)}

				{statusCodeChartData.length > 0 && (
					<div className="content-section">
						<h3>Status Code Distribution</h3>
						<ResponsiveContainer width="100%" height={300}>
							<PieChart>
								<Pie
									data={statusCodeChartData}
									dataKey="value"
									nameKey="name"
									cx="50%"
									cy="50%"
									outerRadius={100}
									label={(entry) => `${entry.name}: ${entry.value}`}
								>
									{statusCodeChartData.map((_entry, index) => (
										<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
									))}
								</Pie>
								<Tooltip
									contentStyle={{
										backgroundColor: 'var(--theme-card-bg)',
										border: '1px solid var(--theme-card-border)',
										borderRadius: '8px',
										color: 'var(--theme-main-text)'
									}}
								/>
							</PieChart>
						</ResponsiveContainer>
					</div>
				)}

				{pageData?.endpoints && pageData.endpoints.length > 0 && (
					<div className="content-section">
						<h3>Endpoints Details</h3>
						<div className="table-container">
							<table className="data-table">
								<thead>
									<tr>
										<th>Endpoint</th>
										<th>Requests</th>
										<th>Errors</th>
										<th>Error Rate</th>
										<th>Avg Time</th>
										<th>P95 Time</th>
										<th>P99 Time</th>
									</tr>
								</thead>
								<tbody>
									{pageData.endpoints.map((endpoint: any, idx: number) => (
										<tr key={idx}>
											<td className="monospace">{endpoint.endpoint}</td>
											<td>{endpoint.request_count.toLocaleString()}</td>
											<td>{endpoint.error_count}</td>
											<td>
												<span className={endpoint.error_count > 0 ? 'text-error' : 'text-success'}>
													{endpoint.error_rate}
												</span>
											</td>
											<td className="text-muted">{endpoint.avg_response_time}</td>
											<td className="text-muted">{endpoint.p95_response_time}</td>
											<td className="text-muted">{endpoint.p99_response_time}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				)}

				{pageData?.error_types && Object.keys(pageData.error_types).length > 0 && (
					<div className="content-section">
						<h3>Error Types</h3>
						<div className="table-container">
							<table className="data-table">
								<thead>
									<tr>
										<th>Endpoint</th>
										<th>Error Type</th>
										<th>Count</th>
									</tr>
								</thead>
								<tbody>
									{Object.entries(pageData.error_types).map(([endpoint, errors]: [string, any]) =>
										Object.entries(errors).map(([errorType, count]: [string, any]) => (
											<tr key={`${endpoint}-${errorType}`}>
												<td className="monospace">{endpoint}</td>
												<td className="text-error">{errorType}</td>
												<td>{count}</td>
											</tr>
										))
									)}
								</tbody>
							</table>
						</div>
					</div>
				)}
			</div>
		);
	};

	const renderGeneric = () => (
		<div className="page-content">
			<h2>{pageData?.title || selectedPage}</h2>
			{pageData?.description && <p className="page-description">{pageData.description}</p>}
			<pre className="json-display">{JSON.stringify(pageData, null, 2)}</pre>
		</div>
	);

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
				<aside className="admin-sidebar">
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
										>
											<span className="menu-item-label">{item.label}</span>
										</div>
									))}
								</div>
							</div>
						))}
					</nav>
				</aside>

				<main className="admin-main">
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
