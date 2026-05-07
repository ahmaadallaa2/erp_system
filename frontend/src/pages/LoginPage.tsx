import { useState } from "react";
import { useNavigate } from "react-router";
import toast from "react-hot-toast";
import { useAuthStore } from "../app/store/auth-store";
import { login } from "../lib/api/auth/login";

function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((state) => state.setTokens);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");

      const data = await login({ email, password });
      setTokens(data.access, data.refresh);

      if (rememberMe) {
        // placeholder for future behavior if needed
      }

      toast.success("Logged in successfully.");
      navigate("/dashboard");
    } catch (err) {
      console.error("Login error:", err);
      setError("بيانات الدخول غير صحيحة");
      toast.error("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Outfit:wght@300;400;600;800&display=swap');

        html, body, #root {
          width: 100%;
          height: 100%;
          min-height: 100%;
          margin: 0;
          padding: 0;
          overflow: hidden;
          background: #050b14;
        }

        :root {
          --bg-deep: #050b14;
          --bg-panel: #0f172a;
          --primary: #00e5ff;
          --primary-dim: rgba(0, 229, 255, 0.1);
          --text-main: #ffffff;
          --text-muted: #94a3b8;
          --border-color: rgba(255, 255, 255, 0.08);
          --danger-bg: rgba(255, 77, 77, 0.1);
          --danger-text: #ff6b6b;
          --danger-border: rgba(255, 77, 77, 0.2);
        }

        * {
          box-sizing: border-box;
        }

        .tb-login-page,
        .tb-login-page * {
          font-family: 'Outfit', 'Cairo', sans-serif;
        }

        .tb-login-page {
          background-color: var(--bg-deep);
          color: var(--text-main);
          width: 100vw;
          height: 100dvh;
          min-height: 100dvh;
          display: flex;
          justify-content: center;
          align-items: center;
          overflow: hidden;
          position: relative;
          padding: 0;
        }

        .tb-grid-bg {
          position: absolute;
          width: 200%;
          height: 200%;
          background-image:
            linear-gradient(var(--border-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--border-color) 1px, transparent 1px);
          background-size: 40px 40px;
          opacity: 0.15;
          transform: perspective(500px) rotateX(60deg);
          animation: tbGridMove 20s linear infinite;
          z-index: 0;
          top: -50%;
          left: -50%;
        }

        @keyframes tbGridMove {
          0% {
            transform: perspective(500px) rotateX(60deg) translateY(0);
          }
          100% {
            transform: perspective(500px) rotateX(60deg) translateY(40px);
          }
        }

        .tb-login-card {
          width: min(1000px, calc(100vw - 48px));
          height: min(600px, calc(100dvh - 48px));
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(15px);
          -webkit-backdrop-filter: blur(15px);
          border: 1px solid var(--border-color);
          border-radius: 20px;
          display: flex;
          position: relative;
          z-index: 10;
          box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
          overflow: hidden;
        }

        .tb-login-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--primary), transparent);
          opacity: 0.8;
          z-index: 3;
        }

        .tb-visual-side {
          flex: 1.2;
          background: linear-gradient(135deg, rgba(0, 229, 255, 0.05), transparent);
          position: relative;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          border-right: 1px solid var(--border-color);
          overflow: hidden;
        }

        .tb-visual-content {
          z-index: 2;
          text-align: center;
          padding: 40px;
        }

        .tb-visual-content h1 {
          font-size: 42px;
          font-weight: 800;
          letter-spacing: -1px;
          margin-bottom: 15px;
          color: #fff;
        }

        .tb-highlight {
          color: var(--primary);
        }

        .tb-visual-content p {
          color: var(--text-muted);
          font-size: 16px;
          line-height: 1.6;
          max-width: 350px;
          margin: 0 auto;
        }

        .tb-tech-circle {
          position: absolute;
          width: 400px;
          height: 400px;
          border: 1px solid var(--border-color);
          border-radius: 50%;
          display: flex;
          justify-content: center;
          align-items: center;
          animation: tbSpin 30s linear infinite;
        }

        .tb-tech-circle::after {
          content: '';
          position: absolute;
          width: 350px;
          height: 350px;
          border: 1px dashed var(--primary);
          opacity: 0.2;
          border-radius: 50%;
        }

        @keyframes tbSpin {
          100% {
            transform: rotate(360deg);
          }
        }

        .tb-form-side {
          flex: 1;
          padding: 50px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          position: relative;
        }

        .tb-brand-logo {
          font-size: 20px;
          font-weight: 700;
          color: var(--primary);
          letter-spacing: 2px;
          margin-bottom: 40px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .tb-brand-logo-icon {
          width: 18px;
          height: 18px;
          border-radius: 4px;
          background: var(--primary);
          box-shadow: 0 0 18px rgba(0, 229, 255, 0.35);
          display: inline-block;
        }

        .tb-form-header h2 {
          font-size: 28px;
          margin-bottom: 5px;
        }

        .tb-form-header p {
          color: var(--text-muted);
          font-size: 14px;
          margin-bottom: 30px;
        }

        .tb-error-box {
          background: var(--danger-bg);
          color: var(--danger-text);
          padding: 12px;
          border-radius: 6px;
          font-size: 13px;
          margin-bottom: 20px;
          text-align: center;
          border: 1px solid var(--danger-border);
        }

        .tb-input-group {
          position: relative;
          margin-bottom: 20px;
        }

        .tb-input-group input {
          width: 100%;
          padding: 16px 20px 16px 48px;
          background: var(--bg-deep);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: #fff;
          font-size: 15px;
          outline: none;
          transition: 0.3s;
        }

        .tb-input-group input::placeholder {
          color: #7b8aa3;
        }

        .tb-input-group svg {
          position: absolute;
          left: 16px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
          width: 18px;
          height: 18px;
          transition: 0.3s;
          pointer-events: none;
        }

        .tb-input-group input:focus {
          border-color: var(--primary);
          box-shadow: 0 0 15px var(--primary-dim);
        }

        .tb-input-group input:focus + svg {
          color: var(--primary);
        }

        .tb-options-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 30px;
          font-size: 13px;
          color: var(--text-muted);
          align-items: center;
          gap: 16px;
        }

        .tb-remember {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }

        .tb-remember input {
          accent-color: var(--primary);
        }

        .tb-forgot {
          color: var(--primary);
          text-decoration: none;
          cursor: pointer;
        }

        .tb-btn-login {
          width: 100%;
          padding: 16px;
          background: var(--primary);
          color: #050b14;
          font-weight: 700;
          font-size: 16px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: 0.3s;
          text-transform: uppercase;
          letter-spacing: 1px;
          box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
        }

        .tb-btn-login:hover:not(:disabled) {
          background: #fff;
          box-shadow: 0 0 30px rgba(0, 229, 255, 0.4);
          transform: translateY(-2px);
        }

        .tb-btn-login:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .tb-dots {
          margin-top: 30px;
          display: flex;
          gap: 10px;
          justify-content: center;
        }

        .tb-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: rgba(255,255,255,0.2);
        }

        .tb-dot-active {
          background: var(--primary);
        }

        @media (max-width: 960px) {
          .tb-login-page {
            align-items: stretch;
            padding: 0;
          }

          .tb-grid-bg {
            opacity: 0.1;
          }

          .tb-login-card {
            width: 100%;
            height: 100dvh;
            min-height: 100dvh;
            border: none;
            border-radius: 0;
            background: transparent;
            flex-direction: column;
            box-shadow: none;
          }

          .tb-login-card::before {
            display: none;
          }

          .tb-visual-side {
            display: none;
          }

          .tb-form-side {
            padding: 30px;
            justify-content: center;
            min-height: 100dvh;
            background: linear-gradient(
              180deg,
              rgba(5, 11, 20, 0) 0%,
              rgba(5, 11, 20, 1) 100%
            );
          }

          .tb-brand-logo {
            justify-content: center;
            font-size: 28px;
            margin-bottom: 50px;
            text-shadow: 0 0 20px var(--primary-dim);
          }

          .tb-form-header {
            text-align: center;
          }

          .tb-input-group input {
            background: rgba(255,255,255,0.03);
            padding: 18px 20px 18px 50px;
            font-size: 16px;
          }

          .tb-btn-login {
            margin-top: 20px;
            padding: 18px;
          }
        }

        input:-webkit-autofill,
        input:-webkit-autofill:hover,
        input:-webkit-autofill:focus {
          -webkit-box-shadow: 0 0 0 30px var(--bg-deep) inset !important;
          -webkit-text-fill-color: white !important;
          transition: background-color 5000s ease-in-out 0s;
        }
      `}</style>

      <div className="tb-login-page">
        <div className="tb-grid-bg" />

        <div className="tb-login-card">
          <div className="tb-form-side">
            <div className="tb-brand-logo">
              <span className="tb-brand-logo-icon" />
              BUILD&TRUST
            </div>

            <div className="tb-form-header">
              <h2>Welcome Back</h2>
              <p>Please log in to continue to your dashboard.</p>
            </div>

            <form onSubmit={handleSubmit}>
              {error && <div className="tb-error-box">{error}</div>}

              <div className="tb-input-group">
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16v16H4z" stroke="none" />
                  <path d="M4 7l8 6 8-6" />
                  <rect x="3" y="5" width="18" height="14" rx="2" ry="2" />
                </svg>
              </div>

              <div className="tb-input-group">
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="5" y="11" width="14" height="10" rx="2" />
                  <path d="M8 11V8a4 4 0 1 1 8 0v3" />
                </svg>
              </div>

              <div className="tb-options-row">
                <label className="tb-remember">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>

                <a className="tb-forgot">Forgot Password?</a>
              </div>

              <button type="submit" className="tb-btn-login" disabled={loading}>
                {loading ? "Logging In..." : "Login Access"}
              </button>
            </form>
          </div>

          <div className="tb-visual-side">
            <div className="tb-tech-circle" />

            <div className="tb-visual-content">
              <h1>
                BUILD <span className="tb-highlight">&</span> TRUST
              </h1>
              <p>Enterprise Resource Planning</p>

              <div className="tb-dots">
                <span className="tb-dot tb-dot-active" />
                <span className="tb-dot" />
                <span className="tb-dot" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default LoginPage;