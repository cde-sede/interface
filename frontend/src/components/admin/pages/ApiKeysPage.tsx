import { useState } from 'react';

interface ApiKey {
	id: number;
	key_preview: string;
	level: number;
	expire: string | null;
	created_at: string;
	last_used: string | null;
}

interface Level {
	value: number;
	label: string;
	description: string;
}

interface ApiKeysPageProps {
	keys?: ApiKey[];
	levels?: Level[];
	title?: string;
	description?: string;
	onRefresh?: () => void;
	onShowToast?: (message: string, type: 'success' | 'error' | 'info') => void;
	onShowConfirm?: (message: string) => Promise<boolean>;
}

export default function ApiKeysPage({
	keys,
	levels,
	title,
	description,
	onRefresh,
	onShowToast,
	onShowConfirm
}: ApiKeysPageProps) {
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [newKeyData, setNewKeyData] = useState<{ key: string; level: number; expire: string | null } | null>(null);
	const [isCreating, setIsCreating] = useState(false);

	const formatDate = (dateString: string | null) => {
		if (!dateString) return 'Never';
		try {
			return new Date(dateString).toLocaleString();
		} catch {
			return dateString;
		}
	};

	const getLevelLabel = (levelValue: number) => {
		const level = levels?.find(l => l.value === levelValue);
		return level?.label || `Level ${levelValue}`;
	};

	const getLevelClass = (levelValue: number) => {
		return levelValue >= 1 ? 'level-admin' : 'level-user';
	};

	const isExpired = (expireDate: string | null) => {
		if (!expireDate) return false;
		try {
			return new Date(expireDate) < new Date();
		} catch {
			return false;
		}
	};

	const handleCreateKey = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		setIsCreating(true);

		const formData = new FormData(e.currentTarget);
		const level = parseInt(formData.get('level') as string);
		const expireInput = formData.get('expire') as string;
		const expire = expireInput ? new Date(expireInput).toISOString() : null;

		const token = localStorage.getItem('auth_token');

		try {
			const res = await fetch('/admin/api-keys', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({ level, expire })
			});

			const data = await res.json();

			if (res.ok) {
				setNewKeyData({ key: data.key, level: data.level, expire: data.expire });
				onShowToast?.('API key created successfully', 'success');
				onRefresh?.();
			} else {
				onShowToast?.(data.error || 'Failed to create API key', 'error');
			}
		} catch (err: any) {
			onShowToast?.(`Error: ${err.message}`, 'error');
		} finally {
			setIsCreating(false);
		}
	};

	const handleDeleteKey = async (keyId: number, keyPreview: string) => {
		const confirmed = await onShowConfirm?.(`Delete API key ${keyPreview}?`);
		if (!confirmed) return;

		const token = localStorage.getItem('auth_token');

		try {
			const res = await fetch(`/admin/api-keys/${keyId}`, {
				method: 'DELETE',
				headers: {
					'Authorization': `Bearer ${token}`
				}
			});

			const data = await res.json();

			if (res.ok) {
				onShowToast?.('API key deleted successfully', 'success');
				onRefresh?.();
			} else {
				onShowToast?.(data.error || 'Failed to delete API key', 'error');
			}
		} catch (err: any) {
			onShowToast?.(`Error: ${err.message}`, 'error');
		}
	};

	const closeCreateModal = () => {
		setShowCreateModal(false);
		setNewKeyData(null);
	};

	return (
		<div className="page-content">
			<div className="page-header">
				<div>
					<h2>{title}</h2>
					{description && <p className="page-description">{description}</p>}
				</div>
				<button
					className="action-button"
					onClick={() => setShowCreateModal(true)}
				>
					Create API Key
				</button>
			</div>

			{keys && keys.length > 0 ? (
				<div className="table-container">
					<table className="data-table">
						<thead>
							<tr>
								<th>ID</th>
								<th>Key Preview</th>
								<th>Level</th>
								<th>Status</th>
								<th>Created</th>
								<th>Last Used</th>
								<th>Expires</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{keys.map((key) => (
								<tr key={key.id}>
									<td className="monospace">{key.id}</td>
									<td className="monospace">{key.key_preview}</td>
									<td>
										<span className={`status-badge ${getLevelClass(key.level)}`}>
											{getLevelLabel(key.level)}
										</span>
									</td>
									<td>
										{isExpired(key.expire) ? (
											<span className="status-badge status-error">Expired</span>
										) : (
												<span className="status-badge status-ready">Active</span>
											)}
									</td>
									<td className="text-muted">{formatDate(key.created_at)}</td>
									<td className="text-muted">{formatDate(key.last_used)}</td>
									<td className="text-muted">
										{key.expire ? formatDate(key.expire) : 'Never'}
									</td>
									<td>
										<button
											className="table-action-button"
											onClick={() => handleDeleteKey(key.id, key.key_preview)}
											title="Delete this API key"
										>
											Delete
										</button>
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			) : (
					<div className="empty-state">
						<p>No API keys found</p>
						<p className="text-muted">Create an API key to get started with programmatic access</p>
					</div>
				)}

			{/* Create API Key Modal */}
			{showCreateModal && (
				<div className="modal-overlay" onClick={closeCreateModal}>
					<div className="modal-content" onClick={(e) => e.stopPropagation()}>
						<div className="modal-header">
							<h3>Create New API Key</h3>
							<button className="modal-close" onClick={closeCreateModal}>×</button>
						</div>

						{newKeyData ? (
							/* Show the newly created key */
							<div className="modal-body">
								<div className="key-created-notice">
									<h4>API Key Created Successfully</h4>
									<p className="warning-text">
										Please copy this API key now. You won't be able to see it again!
									</p>
								</div>

								<div className="form-group">
									<label>API Key</label>
									<div className="key-display">
										<code className="full-key">{newKeyData.key}</code>
										<button
											className="copy-button"
											onClick={() => {
												navigator.clipboard.writeText(newKeyData.key);
												onShowToast?.('API key copied to clipboard', 'success');
											}}
										>
											Copy
										</button>
									</div>
								</div>

								<div className="info-grid">
									<div className="info-item">
										<span className="info-label">Level</span>
										<span className="info-value">{getLevelLabel(newKeyData.level)}</span>
									</div>
									{newKeyData.expire && (
										<div className="info-item">
											<span className="info-label">Expires</span>
											<span className="info-value">{formatDate(newKeyData.expire)}</span>
										</div>
									)}
								</div>

								<div className="form-actions">
									<button
										className="action-button"
										onClick={closeCreateModal}
									>
										Close
									</button>
								</div>
							</div>
						) : (
								/* Show the creation form */
								<div className="modal-body">
									<form onSubmit={handleCreateKey}>
										<div className="form-group">
											<label>Access Level</label>
											<select name="level" required defaultValue="0">
												{levels?.map((level) => (
													<option key={level.value} value={level.value}>
														{level.label} - {level.description}
													</option>
												))}
											</select>
										</div>

										<div className="form-group">
											<label>Expiration Date (Optional)</label>
											<input
												type="datetime-local"
												name="expire"
												min={new Date().toISOString().slice(0, 16)}
											/>
											<p className="field-hint">Leave empty for no expiration</p>
										</div>

										<div className="form-actions">
											<button
												type="button"
												className="action-button secondary"
												onClick={closeCreateModal}
												disabled={isCreating}
											>
												Cancel
											</button>
											<button
												type="submit"
												className="action-button"
												disabled={isCreating}
											>
												{isCreating ? 'Creating...' : 'Create Key'}
											</button>
										</div>
									</form>
								</div>
							)}
					</div>
				</div>
			)}
		</div>
	);
}
