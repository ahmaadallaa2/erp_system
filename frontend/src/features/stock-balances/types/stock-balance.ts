export type StockBalance = {
  id: string;
  company: string;
  product: string;
  warehouse: string;
  quantity: string;
  reserved_quantity: string;
  available_quantity: string;
  location: string | null;
  reorder_point: string;
  created_at: string;
  updated_at: string;
};