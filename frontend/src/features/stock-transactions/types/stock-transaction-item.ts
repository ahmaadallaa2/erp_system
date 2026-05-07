export type StockTransactionItem = {
  id: string;
  transaction: string;
  product: string;
  quantity: string;
  unit_cost: string;
  note: string | null;
  created_at: string;
  updated_at: string;
};