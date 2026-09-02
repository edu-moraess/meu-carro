import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MetricCard } from '../components/MetricCard';
import { ActivityItem } from '../components/ActivityItem';
import { Vehicle, DashboardData } from '../types';

interface HomeScreenProps {
  vehicle: Vehicle;
  dashboard: DashboardData | null;
  refreshing: boolean;
  onRefresh: () => void;
  onSelectTab: (tab: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  vehicle,
  dashboard,
  refreshing,
  onRefresh,
  onSelectTab,
}) => {
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#38BDF8" />
      }
    >
      {/* Top Card: Meu Carro */}
      <View style={styles.vehicleCard}>
        <View style={styles.vehicleIconBox}>
          <Ionicons name="car-sport" size={26} color="#38BDF8" />
        </View>
        <View style={styles.vehicleDetails}>
          <Text style={styles.vehicleLabel}>Meu carro</Text>
          <Text style={styles.vehicleName}>
            {vehicle.brand} {vehicle.model} {vehicle.year}
          </Text>
          <Text style={styles.vehicleOdo}>
            {vehicle.current_odometer.toLocaleString('pt-BR')} km
          </Text>
        </View>
      </View>

      {/* 4 Cards de Métricas */}
      <View style={styles.metricsGrid}>
        <View style={styles.metricsRow}>
          <MetricCard
            title="Gastos este mês"
            value={`R$ ${(dashboard?.month_expenses || 0).toFixed(2).replace('.', ',')}`}
            subtitle="Combustível e serviços"
            icon="wallet-outline"
            accentColor="#38BDF8"
            onPress={() => onSelectTab('Expenses')}
          />
          <View style={styles.spacing} />
          <MetricCard
            title="Consumo médio"
            value={
              dashboard?.average_consumption
                ? `${dashboard.average_consumption.toFixed(1).replace('.', ',')} km/L`
                : '--'
            }
            subtitle={dashboard?.average_consumption ? 'Cálculo real' : 'Dados insuficientes'}
            icon="speedometer-outline"
            accentColor="#34D399"
            onPress={() => onSelectTab('Fuel')}
          />
        </View>

        <View style={styles.metricsRow}>
          <MetricCard
            title="Custo por km"
            value={
              dashboard?.cost_per_km
                ? `R$ ${dashboard.cost_per_km.toFixed(2).replace('.', ',')}`
                : '--'
            }
            subtitle="Gasto médio rodado"
            icon="trending-up-outline"
            accentColor="#A78BFA"
          />
          <View style={styles.spacing} />
          <MetricCard
            title="Próxima manutenção"
            value={
              dashboard?.next_maintenance_km_remaining
                ? `${dashboard.next_maintenance_km_remaining.toLocaleString('pt-BR')} km`
                : '--'
            }
            subtitle={dashboard?.next_maintenance_title || 'Sem agendamentos'}
            icon="construct-outline"
            accentColor="#FBBF24"
            onPress={() => onSelectTab('Maintenance')}
          />
        </View>
      </View>

      {/* Seção Resumo */}
      <View style={styles.summaryCard}>
        <View style={styles.sectionHeaderRow}>
          <Ionicons name="stats-chart" size={18} color="#38BDF8" />
          <Text style={styles.sectionTitle}>Resumo do Mês</Text>
        </View>
        <Text style={styles.summaryText}>
          {dashboard?.summary_text ||
            'Você gastou R$ 0,00 este mês. Comece registrando seus gastos.'}
        </Text>
      </View>

      {/* Seção Insights */}
      {dashboard?.insights && dashboard.insights.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Ionicons name="bulb-outline" size={18} color="#A78BFA" />
            <Text style={styles.sectionTitle}>Insights Inteligentes</Text>
          </View>
          {dashboard.insights.map((insight, index) => (
            <View key={index} style={styles.insightItem}>
              <Ionicons name="sparkles" size={16} color="#A78BFA" style={{ marginRight: 8 }} />
              <Text style={styles.insightText}>{insight}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Seção Últimas Atividades */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Ionicons name="time-outline" size={18} color="#F8FAFC" />
          <Text style={styles.sectionTitle}>Últimas atividades</Text>
        </View>
        {dashboard?.recent_activities && dashboard.recent_activities.length > 0 ? (
          dashboard.recent_activities.map((act) => (
            <ActivityItem key={`${act.type}_${act.id}`} activity={act} />
          ))
        ) : (
          <Text style={styles.emptyText}>Nenhuma atividade recente registrada.</Text>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  vehicleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 18,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  vehicleIconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  vehicleDetails: {
    flex: 1,
  },
  vehicleLabel: {
    fontSize: 12,
    color: '#94A3B8',
  },
  vehicleName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#F8FAFC',
  },
  vehicleOdo: {
    fontSize: 14,
    fontWeight: '600',
    color: '#38BDF8',
    marginTop: 2,
  },
  metricsGrid: {
    marginBottom: 16,
  },
  metricsRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  spacing: {
    width: 10,
  },
  summaryCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#F8FAFC',
    marginLeft: 6,
  },
  summaryText: {
    fontSize: 14,
    color: '#CBD5E1',
    lineHeight: 20,
  },
  section: {
    marginBottom: 16,
  },
  insightItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 12,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: 'rgba(167, 139, 250, 0.2)',
  },
  insightText: {
    flex: 1,
    fontSize: 13,
    color: '#E2E8F0',
    lineHeight: 18,
  },
  emptyText: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginVertical: 12,
  },
});
