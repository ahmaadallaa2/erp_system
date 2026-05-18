import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { useAuthStore } from "../../app/store/auth-store";

type SidebarProps = {
  isOpen: boolean;
};

type IconName =
  | "dashboard"
  | "partners"
  | "inventory"
  | "product"
  | "warehouse"
  | "transaction"
  | "balance"
  | "movement"
  | "sales"
  | "purchase"
  | "accounting"
  | "ai"
  | "logout";

type NavItem = {
  to?: string;
  label: string;
  icon: IconName;
  disabled?: boolean;
  badge?: string;
};

type NavSection = {
  label: string;
  icon: IconName;
  isActive: boolean;
  items: NavItem[];
};

const primary = "#14B8D4";

function Sidebar({ isOpen }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const isCollapsed = !isOpen;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const sections: NavSection[] = [
    {
      label: "عام",
      icon: "dashboard",
      isActive: location.pathname.startsWith("/dashboard"),
      items: [{ to: "/dashboard", label: "لوحة التحكم", icon: "dashboard" }],
    },
    {
      label: "الشركاء",
      icon: "partners",
      isActive: location.pathname.startsWith("/partners"),
      items: [{ to: "/partners", label: "الشركاء", icon: "partners" }],
    },
    {
      label: "المخزون",
      icon: "inventory",
      isActive:
        location.pathname.startsWith("/products") ||
        location.pathname.startsWith("/warehouses") ||
        location.pathname.startsWith("/stock-transactions") ||
        location.pathname.startsWith("/stock-balances") ||
        location.pathname.startsWith("/stock-movements"),
      items: [
        { to: "/products", label: "المنتجات", icon: "product" },
        { to: "/warehouses", label: "المخازن", icon: "warehouse" },
        { to: "/stock-transactions", label: "حركات المخزون", icon: "transaction" },
        { to: "/stock-balances", label: "أرصدة المخزون", icon: "balance" },
        { to: "/stock-movements", label: "تفاصيل الحركة", icon: "movement" },
      ],
    },
    {
      label: "المبيعات",
      icon: "sales",
      isActive: location.pathname.startsWith("/sales-invoices"),
      items: [{ to: "/sales-invoices", label: "فواتير المبيعات", icon: "sales" }],
    },
    {
      label: "المشتريات",
      icon: "purchase",
      isActive: location.pathname.startsWith("/purchase-invoices"),
      items: [{ to: "/purchase-invoices", label: "فواتير المشتريات", icon: "purchase" }],
    },
    {
      label: "المحاسبة",
      icon: "accounting",
      isActive: location.pathname.startsWith("/payments"),
      items: [{ to: "/payments", label: "المدفوعات", icon: "accounting" }],
    },
    {
      label: "AI",
      icon: "ai",
      isActive: location.pathname.startsWith("/ai-assistant"),
      items: [{ to: "/ai-assistant", label: "المساعد الذكي", icon: "ai" }],
    },
  ];

  return (
    <aside className="erp-sidebar-scroll" style={getSidebarStyle(isCollapsed)}>
      <div style={getBrandAreaStyle(isCollapsed)}>
        <div style={brandMarkStyle}>TB</div>
        {!isCollapsed && (
          <div style={brandTextStyle}>
            <h2 style={brandTitleStyle}>TRUST ERP</h2>
            <div style={brandSubtitleStyle}>Business Operations</div>
          </div>
        )}
      </div>

      <nav className="erp-sidebar-menu-scroll" style={navStyle}>
        {sections.map((section) => (
          <SidebarSection
            key={section.label}
            section={section}
            isCollapsed={isCollapsed}
            pathname={location.pathname}
          />
        ))}
      </nav>

      <div style={logoutPanelStyle}>
        <button
          onClick={handleLogout}
          style={getLogoutButtonStyle(isCollapsed)}
          title="تسجيل الخروج"
        >
          <span style={logoutIconBoxStyle}>
            <SidebarIcon name="logout" />
          </span>
          {!isCollapsed && <span>تسجيل الخروج</span>}
        </button>
      </div>
    </aside>
  );
}

function SidebarSection({
  section,
  isCollapsed,
  pathname,
}: {
  section: NavSection;
  isCollapsed: boolean;
  pathname: string;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const hasChildren = section.items.length > 1;

  useEffect(() => {
    if (section.isActive) {
      setIsOpen(true);
    }
  }, [section.isActive]);

  if (!hasChildren) {
    const item = section.items[0];
    return (
      <SidebarLink
        to={item.to}
        label={item.label}
        icon={item.icon}
        isCollapsed={isCollapsed}
        isActive={isRouteActive(pathname, item.to)}
      />
    );
  }

  return (
    <div style={sectionStyle}>
      <button
        className="erp-sidebar-button"
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        style={getSectionButtonStyle(section.isActive, isCollapsed)}
        title={section.label}
      >
        <span style={getIconBoxStyle(section.isActive)}>
          <SidebarIcon name={section.icon} />
        </span>
        {!isCollapsed && <span style={sectionLabelStyle}>{section.label}</span>}
        {!isCollapsed && <span style={chevronStyle}>{isOpen ? "-" : "+"}</span>}
      </button>

      {isOpen && (
        <div className="erp-sidebar-submenu-scroll" style={getSubmenuStyle(isCollapsed)}>
          {section.items.map((item) => (
            <SidebarLink
              key={item.to}
              to={item.to}
              label={item.label}
              icon={item.icon}
              isCollapsed={isCollapsed}
              isActive={isRouteActive(pathname, item.to)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SidebarLink({
  to,
  label,
  icon,
  isCollapsed,
  isActive,
}: NavItem & {
  isCollapsed: boolean;
  isActive: boolean;
}) {
  return (
    <Link
      className="erp-sidebar-link"
      to={to}
      style={getLinkStyle(isActive, isCollapsed)}
      title={label}
    >
      <span style={getIconBoxStyle(isActive)}>
        <SidebarIcon name={icon} />
      </span>
      {!isCollapsed && <span style={linkLabelStyle}>{label}</span>}
    </Link>
  );
}

function SidebarIcon({ name }: { name: IconName }) {
  const commonProps = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "dashboard":
      return (
        <svg {...commonProps}>
          <rect x="3" y="3" width="7" height="8" rx="2" />
          <rect x="14" y="3" width="7" height="5" rx="2" />
          <rect x="14" y="12" width="7" height="9" rx="2" />
          <rect x="3" y="15" width="7" height="6" rx="2" />
        </svg>
      );
    case "partners":
      return (
        <svg {...commonProps}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
          <circle cx="9.5" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      );
    case "inventory":
      return (
        <svg {...commonProps}>
          <path d="m21 8-9-5-9 5 9 5 9-5Z" />
          <path d="M3 8v8l9 5 9-5V8" />
          <path d="M12 13v8" />
        </svg>
      );
    case "product":
      return (
        <svg {...commonProps}>
          <path d="M6 2h12l2 7H4l2-7Z" />
          <path d="M4 9v11h16V9" />
          <path d="M9 14h6" />
        </svg>
      );
    case "warehouse":
      return (
        <svg {...commonProps}>
          <path d="M3 21V8l9-5 9 5v13" />
          <path d="M7 21V11h10v10" />
          <path d="M9 15h6" />
        </svg>
      );
    case "transaction":
      return (
        <svg {...commonProps}>
          <path d="M7 7h11l-3-3" />
          <path d="M17 17H6l3 3" />
          <path d="M18 7 15 10" />
          <path d="M6 17l3-3" />
        </svg>
      );
    case "balance":
      return (
        <svg {...commonProps}>
          <path d="M12 3v18" />
          <path d="M5 7h14" />
          <path d="m6 7-3 6h6L6 7Z" />
          <path d="m18 7-3 6h6l-3-6Z" />
        </svg>
      );
    case "movement":
      return (
        <svg {...commonProps}>
          <path d="M4 17h6" />
          <path d="M4 12h10" />
          <path d="M4 7h16" />
          <path d="m17 14 3 3-3 3" />
        </svg>
      );
    case "sales":
      return (
        <svg {...commonProps}>
          <path d="M6 2h9l5 5v15H6z" />
          <path d="M14 2v6h6" />
          <path d="M9 13h6" />
          <path d="M9 17h4" />
        </svg>
      );
    case "purchase":
      return (
        <svg {...commonProps}>
          <circle cx="9" cy="21" r="1" />
          <circle cx="20" cy="21" r="1" />
          <path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h8.9a2 2 0 0 0 2-1.6L22 6H6" />
        </svg>
      );
    case "accounting":
      return (
        <svg {...commonProps}>
          <rect x="4" y="3" width="16" height="18" rx="2" />
          <path d="M8 8h8" />
          <path d="M8 12h8" />
          <path d="M8 16h4" />
        </svg>
      );
    case "ai":
      return (
        <svg {...commonProps}>
          <path d="M12 3v3" />
          <path d="M12 18v3" />
          <rect x="6" y="6" width="12" height="12" rx="3" />
          <path d="M9 10h.01" />
          <path d="M15 10h.01" />
          <path d="M9 14h6" />
        </svg>
      );
    case "logout":
      return (
        <svg {...commonProps}>
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <path d="m16 17 5-5-5-5" />
          <path d="M21 12H9" />
        </svg>
      );
  }
}

function isRouteActive(pathname: string, to: string) {
  return pathname === to || pathname.startsWith(`${to}/`);
}

function getSidebarStyle(isCollapsed: boolean): React.CSSProperties {
  const width = isCollapsed ? "72px" : "260px";

  return {
    width,
    minWidth: width,
    maxWidth: width,
    height: "calc(100% - 28px)",
    margin: "14px 14px 14px 0",
    minHeight: 0,
    flexShrink: 0,
    display: "flex",
    flexDirection: "column",
    boxSizing: "border-box",
    padding: isCollapsed ? "14px 8px" : "20px 12px 14px",
    overflowY: "hidden",
    overflowX: "hidden",
    background:
      "linear-gradient(180deg, #062B36 0%, #073B4C 50%, #0A4A5C 100%)",
    color: "#f8fafc",
    border: "1px solid rgba(125, 211, 252, 0.18)",
    borderRadius: "24px 0 0 24px",
    boxShadow: "-16px 0 36px rgba(6, 43, 54, 0.24), inset 0 1px 0 rgba(255,255,255,0.08)",
    textAlign: "right",
    transition:
      "width 200ms ease, min-width 200ms ease, max-width 200ms ease, border-radius 200ms ease",
  };
}

function getBrandAreaStyle(isCollapsed: boolean): React.CSSProperties {
  return {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "12px",
    padding: isCollapsed ? "0 0 16px" : "0 6px 18px",
    marginBottom: "18px",
    borderBottom: "1px solid rgba(153, 246, 228, 0.14)",
  };
}

const brandMarkStyle: React.CSSProperties = {
  width: "54px",
  height: "54px",
  borderRadius: "20px",
  background: "linear-gradient(135deg, #14B8D4 0%, #22d3ee 100%)",
  color: "#ffffff",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "17px",
  fontWeight: 900,
  boxShadow: "0 12px 22px rgba(20, 184, 212, 0.22)",
};

const brandTextStyle: React.CSSProperties = {
  textAlign: "center",
  minWidth: 0,
};

const brandTitleStyle: React.CSSProperties = {
  margin: 0,
  color: "#f8fafc",
  fontSize: "21px",
  fontWeight: 900,
  lineHeight: 1.15,
};

const brandSubtitleStyle: React.CSSProperties = {
  marginTop: "6px",
  color: "rgba(204, 251, 241, 0.76)",
  fontSize: "12px",
  fontWeight: 500,
};

const navStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "14px",
  flex: "1 1 0",
  minWidth: 0,
  minHeight: 0,
  overflowY: "auto",
  overflowX: "hidden",
  paddingBottom: "16px",
  overscrollBehavior: "contain",
  WebkitOverflowScrolling: "touch",
};

const sectionStyle: React.CSSProperties = {
  display: "grid",
  gap: "8px",
  overflow: "hidden",
};

function getSectionButtonStyle(isActive: boolean, isCollapsed: boolean): React.CSSProperties {
  return {
    width: "100%",
    minHeight: "50px",
    display: "grid",
    gridTemplateColumns: isCollapsed ? "1fr" : "36px minmax(0, 1fr) auto",
    alignItems: "center",
    gap: "12px",
    padding: isCollapsed ? "7px" : "8px 14px",
    borderRadius: "14px",
    border: `1px solid ${isActive ? "rgba(153, 246, 228, 0.34)" : "transparent"}`,
    borderRight: isActive ? "4px solid #14B8D4" : "4px solid transparent",
    background: isActive
      ? "linear-gradient(90deg, rgba(20,184,212,.18), rgba(20,184,212,.08))"
      : "transparent",
    color: isActive ? "#ecfeff" : "#dbeafe",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: isActive ? 600 : 500,
    textAlign: "right",
    boxShadow: "none",
  };
}

function getLinkStyle(isActive: boolean, isCollapsed: boolean): React.CSSProperties {
  return {
    minHeight: "50px",
    display: "grid",
    gridTemplateColumns: isCollapsed ? "1fr" : "36px minmax(0, 1fr)",
    alignItems: "center",
    gap: "12px",
    padding: isCollapsed ? "7px" : "8px 14px",
    borderRadius: "14px",
    border: `1px solid ${isActive ? "rgba(153, 246, 228, 0.34)" : "transparent"}`,
    borderRight: isActive ? "4px solid #14B8D4" : "4px solid transparent",
    background: isActive
      ? "linear-gradient(90deg, rgba(20,184,212,.18), rgba(20,184,212,.08))"
      : "transparent",
    color: isActive ? "#ecfeff" : "#dbeafe",
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: isActive ? 600 : 500,
    boxShadow: "none",
  };
}

function getIconBoxStyle(isActive: boolean): React.CSSProperties {
  return {
    width: "36px",
    height: "36px",
    borderRadius: "14px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    color: isActive ? primary : "rgba(203, 213, 225, 0.86)",
    background: isActive ? "rgba(236, 254, 255, 0.96)" : "rgba(255, 255, 255, 0.07)",
    flexShrink: 0,
  };
}

const sectionLabelStyle: React.CSSProperties = {
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "normal",
  lineHeight: 1.25,
};

const linkLabelStyle: React.CSSProperties = {
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "normal",
  lineHeight: 1.25,
};

const chevronStyle: React.CSSProperties = {
  color: "#99f6e4",
  fontSize: "14px",
  lineHeight: 1,
};

function getSubmenuStyle(isCollapsed: boolean): React.CSSProperties {
  return {
    display: "grid",
    gap: "8px",
    padding: isCollapsed ? "0" : "0 10px 0 0",
    maxHeight: isCollapsed ? "232px" : "236px",
    overflowY: "auto",
    overflowX: "hidden",
    overscrollBehavior: "contain",
    transition: "max-height 200ms ease",
    WebkitOverflowScrolling: "touch",
  };
}

const logoutPanelStyle: React.CSSProperties = {
  marginTop: "auto",
  paddingTop: "24px",
  borderTop: "1px solid rgba(255,255,255,.08)",
  flexShrink: 0,
  background: "transparent",
};

const logoutIconBoxStyle: React.CSSProperties = {
  width: "36px",
  height: "36px",
  borderRadius: "14px",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#ecfeff",
  background: "rgba(255,255,255,.04)",
  flexShrink: 0,
};

function getLogoutButtonStyle(isCollapsed: boolean): React.CSSProperties {
  return {
    width: "100%",
    minHeight: "50px",
    display: "flex",
    alignItems: "center",
    justifyContent: isCollapsed ? "center" : "flex-start",
    gap: "10px",
    padding: isCollapsed ? "7px" : "8px 14px",
    borderRadius: "16px",
    border: "1px solid rgba(255,255,255,.06)",
    background: "rgba(255,255,255,.03)",
    color: "#ecfeff",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 800,
  };
}

export default Sidebar;
