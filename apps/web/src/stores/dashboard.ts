import { create } from 'zustand';

interface DashboardState {
  selectedRobotId: string | null;
  setSelectedRobotId: (id: string | null) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  selectedRobotId: null,
  setSelectedRobotId: (id) => set({ selectedRobotId: id }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
