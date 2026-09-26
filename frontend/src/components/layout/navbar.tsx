import { theme } from "../../styles/theme";
import { useAuthStore } from "../../app/store/auth-store";

type NavbarProps = {
  onToggleSidebar: () => void;
};

function Navbar({ onToggleSidebar }: NavbarProps) {
  const authContext = useAuthStore((state) => state.authContext);
  const isContextLoading = useAuthStore((state) => state.isContextLoading);
  const companyName = isContextLoading ? "..." : authContext?.company?.name || "-";
  const branchName = isContextLoading ? "..." : authContext?.branch?.name || "-";
  const user = authContext?.user;
  const userName = isContextLoading ? "..." : user?.full_name || "مستخدم";
  const userRole = isContextLoading ? "..." : user?.job_title || user?.user_type || "مستخدم النظام";
  const avatarInitials = isContextLoading ? "..." : getInitials(user?.full_name);

  return (
    <header className="erp-topbar" style={navbarStyle}>
      <div style={rightClusterStyle}>
        <button
          className="erp-navbar-button"
          onClick={onToggleSidebar}
          style={toggleButtonStyle}
          title="فتح وإغلاق القائمة"
        >
          <span style={hamburgerLineStyle} />
          <span style={hamburgerLineStyle} />
          <span style={hamburgerLineStyle} />
        </button>

        <div style={pageAreaStyle}>
          <div style={breadcrumbStyle}>
            <strong>لوحة التحكم</strong>
            <span style={breadcrumbDividerStyle}>/</span>
            <span>النظام</span>
          </div>
          <strong style={pageTitleStyle}>لوحة التحكم</strong>
        </div>
      </div>

      <div className="erp-topbar-search" style={searchBoxStyle}>
        <SearchIcon />
        <span style={searchTextStyle}>بحث في النظام...</span>
      </div>

      <div className="erp-topbar-left" style={leftClusterStyle}>
        <div className="erp-topbar-context" style={contextAreaStyle}>
          <span style={contextPillStyle}>الشركة: {companyName}</span>
          <span style={contextPillStyle}>الفرع: {branchName}</span>
        </div>

        <div className="erp-topbar-user" style={userAreaStyle}>
          <div style={avatarStyle}>{avatarInitials}</div>
          <div className="erp-topbar-user-copy" style={userCopyStyle}>
            <strong style={userNameStyle}>{userName}</strong>
            <span style={userRoleStyle}>{userRole}</span>
          </div>
          <UserChevronIcon />
          <span style={notificationStyle}>●</span>
        </div>
      </div>
    </header>
  );
}

function UserChevronIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={userChevronStyle}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={searchIconStyle}
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function getInitials(fullName?: string) {
  if (!fullName?.trim()) return "U";

  const parts = fullName.trim().split(/\s+/);
  const first = parts[0]?.[0] || "";
  const second = parts[1]?.[0] || "";
  const initials = `${first}${second}`.toUpperCase();

  return initials || "U";
}

const navbarStyle: React.CSSProperties = {
  direction: "rtl",
  background:
    "linear-gradient(135deg, rgba(255,255,255,0.96), rgba(236,254,255,0.48))",
  border: "1px solid rgba(226, 232, 240, 0.78)",
  height: "72px",
  minHeight: "72px",
  padding: "0 18px",
  display: "grid",
  gridTemplateColumns: "minmax(210px, auto) minmax(0, 1fr) minmax(320px, auto)",
  alignItems: "center",
  gap: "16px",
  width: "100%",
  maxWidth: "100%",
  minWidth: 0,
  flexShrink: 0,
  overflow: "hidden",
  boxSizing: "border-box",
  position: "sticky",
  top: 0,
  zIndex: 5,
  borderRadius: "20px",
  boxShadow: "0 4px 20px rgba(0,0,0,.04)",
  backdropFilter: "blur(20px) saturate(145%)",
};

const rightClusterStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "14px",
  minWidth: 0,
  justifyContent: "flex-start",
};

const leftClusterStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "14px",
  minWidth: 0,
  justifyContent: "flex-end",
};

const toggleButtonStyle: React.CSSProperties = {
  width: "42px",
  height: "42px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  color: "#0891B2",
  borderRadius: "15px",
  cursor: "pointer",
  flexShrink: 0,
  display: "inline-flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  gap: "4px",
  boxShadow: "0 10px 22px rgba(15, 23, 42, 0.06)",
};

const hamburgerLineStyle: React.CSSProperties = {
  width: "16px",
  height: "2px",
  borderRadius: "999px",
  background: "currentColor",
};

const pageAreaStyle: React.CSSProperties = {
  display: "grid",
  gap: "4px",
  minWidth: 0,
};

const breadcrumbStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  color: "#64748b",
  fontSize: "12px",
  whiteSpace: "nowrap",
};

const breadcrumbDividerStyle: React.CSSProperties = {
  color: "#cbd5e1",
};

const pageTitleStyle: React.CSSProperties = {
  color: "#020617",
  fontSize: "15px",
  fontWeight: 900,
  whiteSpace: "nowrap",
};

const searchBoxStyle: React.CSSProperties = {
  height: "44px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
  width: "420px",
  maxWidth: "35%",
  justifySelf: "center",
  padding: "0 16px",
  borderRadius: "999px",
  border: "1px solid rgba(148, 163, 184, 0.24)",
  background: "rgba(248, 250, 252, 0.76)",
  color: "#64748b",
};

const searchIconStyle: React.CSSProperties = {
  color: "#64748b",
  flexShrink: 0,
};

const searchTextStyle: React.CSSProperties = {
  fontSize: "13px",
  color: "#64748b",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

const contextAreaStyle: React.CSSProperties = {
  display: "flex",
  gap: "8px",
  alignItems: "center",
  minWidth: 0,
};

const contextPillStyle: React.CSSProperties = {
  maxWidth: "180px",
  padding: "8px 12px",
  borderRadius: "999px",
  background: "#f1f5f9",
  color: "#334155",
  border: "1px solid rgba(148, 163, 184, 0.22)",
  fontSize: "12px",
  fontWeight: 700,
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const userAreaStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  minWidth: 0,
  justifyContent: "flex-end",
  padding: "5px 8px 5px 6px",
  borderRadius: "18px",
  border: "1px solid transparent",
  cursor: "pointer",
};

const avatarStyle: React.CSSProperties = {
  width: "44px",
  height: "44px",
  borderRadius: "16px",
  background: "linear-gradient(135deg, #14B8D4 0%, #67E8F9 100%)",
  color: "#ffffff",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "14px",
  fontWeight: 900,
  flexShrink: 0,
  boxShadow: "0 12px 22px rgba(20, 184, 212, 0.24)",
};

const userCopyStyle: React.CSSProperties = {
  display: "grid",
  gap: "4px",
  minWidth: 0,
};

const userNameStyle: React.CSSProperties = {
  color: "#020617",
  fontSize: "13px",
  fontWeight: 700,
  whiteSpace: "nowrap",
};

const userRoleStyle: React.CSSProperties = {
  color: "#94a3b8",
  fontSize: "11px",
  fontWeight: 500,
  whiteSpace: "nowrap",
};

const userChevronStyle: React.CSSProperties = {
  color: "#94a3b8",
  flexShrink: 0,
};

const notificationStyle: React.CSSProperties = {
  color: "#ef4444",
  fontSize: "11px",
  lineHeight: 1,
};

export default Navbar;
