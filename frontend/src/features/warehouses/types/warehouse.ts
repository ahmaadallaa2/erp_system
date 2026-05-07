export type Warehouse = {
  id: string;
  company: string;
  name: string;
  code: string;
  warehouse_type: string;
  branch: string;
  keeper: string | null;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};