import axios from 'axios';
import { Platform } from 'react-native';
import { 
  Vehicle, 
  FuelRecord, 
  MaintenanceRecord, 
  ExpenseRecord, 
  DashboardData, 
  AiParsedData 
} from '../types';

// O backend FastAPI roda na porta 8000
// No emulador Android, 10.0.2.2 mapeia para o localhost da máquina host
const BASE_URL = Platform.OS === 'android' 
  ? 'http://10.0.2.2:8000/api/v1' 
  : 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Veículo
  getCurrentVehicle: async (): Promise<Vehicle | null> => {
    try {
      const resp = await apiClient.get<Vehicle>('/vehicles/current');
      return resp.data;
    } catch {
      return null;
    }
  },

  createVehicle: async (data: Omit<Vehicle, 'id'>): Promise<Vehicle> => {
    const resp = await apiClient.post<Vehicle>('/vehicles', data);
    return resp.data;
  },

  updateVehicle: async (id: number, data: Partial<Vehicle>): Promise<Vehicle> => {
    const resp = await apiClient.put<Vehicle>(`/vehicles/${id}`, data);
    return resp.data;
  },

  // Dashboard
  getDashboard: async (vehicleId: number): Promise<DashboardData> => {
    const resp = await apiClient.get<DashboardData>(`/dashboard?vehicle_id=${vehicleId}`);
    return resp.data;
  },

  // Abastecimentos
  getFuelRecords: async (vehicleId: number): Promise<FuelRecord[]> => {
    const resp = await apiClient.get<FuelRecord[]>(`/fuel?vehicle_id=${vehicleId}`);
    return resp.data;
  },

  createFuelRecord: async (data: any): Promise<FuelRecord> => {
    const resp = await apiClient.post<FuelRecord>('/fuel', data);
    return resp.data;
  },

  deleteFuelRecord: async (id: number): Promise<void> => {
    await apiClient.delete(`/fuel/${id}`);
  },

  // Manutenção
  getMaintenanceRecords: async (vehicleId: number): Promise<MaintenanceRecord[]> => {
    const resp = await apiClient.get<MaintenanceRecord[]>(`/maintenance?vehicle_id=${vehicleId}`);
    return resp.data;
  },

  createMaintenanceRecord: async (data: any): Promise<MaintenanceRecord> => {
    const resp = await apiClient.post<MaintenanceRecord>('/maintenance', data);
    return resp.data;
  },

  deleteMaintenanceRecord: async (id: number): Promise<void> => {
    await apiClient.delete(`/maintenance/${id}`);
  },

  // Despesas
  getExpenseRecords: async (vehicleId: number): Promise<ExpenseRecord[]> => {
    const resp = await apiClient.get<ExpenseRecord[]>(`/expenses?vehicle_id=${vehicleId}`);
    return resp.data;
  },

  createExpenseRecord: async (data: any): Promise<ExpenseRecord> => {
    const resp = await apiClient.post<ExpenseRecord>('/expenses', data);
    return resp.data;
  },

  deleteExpenseRecord: async (id: number): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`);
  },

  // Gemini AI (Exclusivamente no backend)
  parseNaturalLanguageText: async (text: string): Promise<AiParsedData> => {
    const resp = await apiClient.post<AiParsedData>('/ai/parse-text', { text });
    return resp.data;
  },

  parseReceipt: async (receiptText?: string, imageBase64?: string): Promise<AiParsedData> => {
    const resp = await apiClient.post<AiParsedData>('/ai/parse-receipt', {
      receipt_text: receiptText,
      image_base64: imageBase64,
    });
    return resp.data;
  },
};
