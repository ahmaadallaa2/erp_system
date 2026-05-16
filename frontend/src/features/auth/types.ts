export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  job_title?: string;
  user_type: string;
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
