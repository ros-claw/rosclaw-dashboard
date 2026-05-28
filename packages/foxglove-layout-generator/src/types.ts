export interface FoxgloveLayout {
  layout: {
    direction: 'row' | 'column';
    first: FoxglovePanel | FoxgloveLayout;
    second: FoxglovePanel | FoxgloveLayout;
    splitPercentage: number;
  };
}

export interface FoxglovePanel {
  url: string;
  topic?: string;
  topics?: string[];
}

export interface FoxgloveLayoutConfig {
  robot_id: string;
  display_name: string;
  panels: PanelConfig[];
}

export interface PanelConfig {
  type: 'Image' | '3D' | 'Plot' | 'RawMessages' | 'StateTransitions' | 'DiagnosticSummary' | 'Teleop';
  topic?: string;
  topics?: string[];
  title?: string;
}
