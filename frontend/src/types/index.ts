// ClawLoom 前端类型定义

export interface World {
  id: string;
  name: string;
  description?: string;
  status: string;
  current_tick: number;
  created_at?: string;
}

export interface Role {
  id: string;
  name: string;
  status: string;
  health: number;
  influence: number;
  location_id?: string;
  card?: RoleCard;
  created_at?: string;
}

export interface RoleCard {
  drives: Drive[];
  memory: {
    public: string[];
    secrets?: string[];
  };
  decision_style: {
    risk_tolerance: string;
  };
}

export interface Drive {
  id: string;
  weight: number;
}

export interface Event {
  id: string;
  tick: number;
  type: string;
  title: string;
  description: string;
  participants: string[];
  outcome?: Record<string, unknown>;
  created_at?: string;
}

export interface Memory {
  id: string;
  tick: number;
  type: string;
  content: string;
  importance: number;
  created_at?: string;
}

export interface WorldState {
  tick: number;
  world_id: string;
  world_name: string;
  world_status: string;
  snapshot?: Record<string, unknown>;
  summary?: string;
  events: Event[];
  roles: Role[];
}

export interface TimelineEntry {
  tick: number;
  summary: string;
  event_count: number;
  event_types: Record<string, number>;
}

export interface TickResult {
  tick: number;
  world_id: string;
  decisions_count: number;
  conflicts_count: number;
  events_count: number;
  summary: string;
  events: Event[];
}

// API 请求类型
export interface CreateWorldRequest {
  name: string;
  description?: string;
  cosmology?: Record<string, unknown>;
  genesis_params?: Record<string, unknown>;
}

export interface CreateRoleRequest {
  name: string;
  card: RoleCard;
  location_id?: string;
}

export interface TickRequest {
  count: number;
}
