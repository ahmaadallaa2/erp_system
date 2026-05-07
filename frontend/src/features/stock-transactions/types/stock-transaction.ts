import type { StockTransactionItem } from "./stock-transaction-item";

export type StockTransaction = {
  id: string;
  company: string;
  code: string;
  transaction_type: string;
  source_warehouse: string | null;
  destination_warehouse: string | null;
  date: string;
  status: string;
  reference: string | null;
  notes: string | null;
  items: StockTransactionItem[];
  created_at: string;
  updated_at: string;
};