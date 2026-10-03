export type UserRole =
  | "system_admin"
  | "company_admin"
  | "branch_manager"
  | "employee";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  job_title?: string | null;
  user_type: UserRole;
  company_id: string | null;
  branch_id: string | null;
};

export type AuthContextParty = {
  id: string;
  name: string;
};

export type AuthContext = {
  user: AuthUser;
  company: AuthContextParty | null;
  branch: AuthContextParty | null;
};
