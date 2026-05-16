export type Payment = {
  id: string;
  voucher_number: string;
  partner: string;
  payment_type: "inbound" | "outbound";
  payment_method: "cash" | "bank";
  account: string;
  amount: string;
  date: string;
  status: "draft" | "posted" | "cancelled";
  reference: string;
  notes: string;
};

export type CreatePaymentPayload = {
  partner: string;
  payment_type: "inbound" | "outbound";
  payment_method: "cash" | "bank";
  account: string;
  amount: string;
  date: string;
  reference?: string;
  notes?: string;
};
