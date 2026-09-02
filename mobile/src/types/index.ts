export interface Vehicle {
  id: number;
  brand: string;
  model: string;
  year: number;
  current_odometer: number;
  fuel_type: string;
  license_plate?: string | null;
}

export interface FuelRecord {
  id: number;
  vehicle_id: number;
  date: string;
  odometer: number;
  liters: number;
  price_per_liter: number;
  total_value: number;
  fuel_type: string;
  station?: string | null;
  notes?: string | null;
  consumption_km_per_l?: number | null;
}

export interface MaintenanceRecord {
  id: number;
  vehicle_id: number;
  date: string;
  odometer: number;
  category: string;
  description: string;
  workshop?: string | null;
  cost: number;
  next_maintenance_km?: number | null;
  next_maintenance_date?: string | null;
  notes?: string | null;
}

export interface ExpenseRecord {
  id: number;
  vehicle_id: number;
  date: string;
  category: string;
  description: string;
  cost: number;
  notes?: string | null;
}

export interface RecentActivity {
  id: number;
  type: 'FUEL' | 'MAINTENANCE' | 'EXPENSE';
  title: string;
  subtitle: string;
  date: string;
  value: number;
  odometer?: number | null;
}

export interface DashboardData {
  month_expenses: number;
  average_consumption?: number | null;
  cost_per_km?: number | null;
  next_maintenance_km_remaining?: number | null;
  next_maintenance_title?: string | null;
  fuel_expense_percentage: number;
  summary_text: string;
  insights: string[];
  recent_activities: RecentActivity[];
}

export interface AiParsedData {
  type: 'fuel' | 'maintenance' | 'expense';
  date?: string | null;
  odometer?: number | null;
  liters?: number | null;
  price_per_liter?: number | null;
  total_cost?: number | null;
  fuel_type?: string | null;
  category?: string | null;
  description?: string | null;
  station?: string | null;
  workshop?: string | null;
}
