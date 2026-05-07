import { api } from "../axios";
import { API_ENDPOINTS } from "../endpoints";

type LoginPayload = {
  email: string;
  password: string;
};

export async function login(payload: LoginPayload) {
  const response = await api.post(API_ENDPOINTS.auth.login, payload);
  return response.data;
}