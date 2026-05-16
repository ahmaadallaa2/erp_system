import { api } from "../../../lib/api/axios";
import { API_ENDPOINTS } from "../../../lib/api/endpoints";
import type { CreatePaymentPayload, Payment } from "../types/payment";

export async function getPayments() {
  const response = await api.get<Payment[]>(API_ENDPOINTS.accounting.payments);
  return response.data;
}

export async function createPayment(payload: CreatePaymentPayload) {
  const response = await api.post<Payment>(
    API_ENDPOINTS.accounting.payments,
    payload
  );
  return response.data;
}

export async function postPayment(id: string) {
  const response = await api.post<Payment>(
    `${API_ENDPOINTS.accounting.payments}${id}/post/`,
    {}
  );
  return response.data;
}
