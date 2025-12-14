interface LoginFormProps {
	authError: string;
	loginError: string | null;
	isLoggingIn: boolean;
	onLogin: (username: string, password: string) => void;
}

export default function LoginForm({ authError, loginError, isLoggingIn, onLogin }: LoginFormProps) {
	const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		const formData = new FormData(e.currentTarget);
		const username = formData.get('username') as string;
		const password = formData.get('password') as string;
		onLogin(username, password);
	};

	return (
		<div className="auth-error-state">
			<div className="login-container">
				<h2>Admin Login</h2>
				<p className="login-description">
					{authError === 'Authentication required. Please log in.'
						? 'Please log in to access the admin panel'
						: authError}
				</p>

				<form onSubmit={handleSubmit} className="login-form">
					<div className="form-group">
						<label htmlFor="username">Username</label>
						<input
							type="text"
							id="username"
							name="username"
							required
							autoFocus
							disabled={isLoggingIn}
						/>
					</div>

					<div className="form-group">
						<label htmlFor="password">Password</label>
						<input
							type="password"
							id="password"
							name="password"
							required
							disabled={isLoggingIn}
						/>
					</div>

					{loginError && (
						<div className="login-error">
							{loginError}
						</div>
					)}

					<button
						type="submit"
						className="action-button login-button"
						disabled={isLoggingIn}
					>
						{isLoggingIn ? 'Logging in...' : 'Login'}
					</button>
				</form>
			</div>
		</div>
	);
}
