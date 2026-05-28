export interface MCAPIndexResult {
  id: string;
  robot_id: string;
  path: string;
  start_time: number | null;
  end_time: number | null;
  duration_sec: number | null;
  size_bytes: number;
  topics: MCAPTopicInfo[];
  schemas: MCAPSchemaInfo[];
  segments: MCAPSegment[];
}

export interface MCAPTopicInfo {
  topic: string;
  schema_name: string;
  message_count: number;
  avg_hz: number | null;
  first_timestamp: number | null;
  last_timestamp: number | null;
}

export interface MCAPSchemaInfo {
  id: number;
  name: string;
  encoding: string;
  data: string;
}

export interface MCAPSegment {
  id: string;
  type: 'failure' | 'skill' | 'task' | 'manual';
  label: string;
  start_time: number;
  end_time: number;
  related_skill: string | null;
  related_body_part: string | null;
  metadata: Record<string, unknown>;
}

export interface TopicStats {
  topic: string;
  message_count: number;
  avg_hz: number | null;
  dropped_frames: number | null;
}
