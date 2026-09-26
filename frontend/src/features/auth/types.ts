<<<<<<< HEAD
export type UserRole =
  | "admin"
  | "manager"
  | "accountant"
  | "inventory_manager"
  | "cashier";

export type Permission = string;

=======
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b
export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  job_title?: string;
  user_type: string;
  company_id: string | null;
  branch_id: string | null;
<<<<<<< HEAD
  role: UserRole;
  permissions?: Permission[];
=======
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b
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
