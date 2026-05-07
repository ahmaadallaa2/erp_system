export type PurchaseInvoiceItem = {
  id: string;
  invoice: string;
  product: string;
  quantity: string;
  unit_price: string;
  line_total: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};