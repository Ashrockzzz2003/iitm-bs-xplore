export interface Source {
  title: string;
  uri: string;
}

export interface GroundingMetadata {
  search_entry_point?: {
    rendered_content: string;
  };
  grounding_chunks?: any[];
}

export interface FunctionCall {
  name: string;
  args: Record<string, any>;
  id?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  timestamp: number;
  sources?: Source[];
  isThinking?: boolean;
  functionCalls?: FunctionCall[];
}

export interface Developer {
  name: string;
  rollNumber: string;
  email: string;
}

// ADK Specific Types

export interface ADKPart {
  text?: string;
  functionCall?: {
    name: string;
    args: Record<string, any>;
    id?: string;
  };
  functionResponse?: any; 
}

export interface ADKContent {
  parts: ADKPart[];
  role: string;
}

export interface ADKEvent {
  id?: string;
  timestamp?: string;
  author?: string;
  content?: ADKContent;
  type?: string; 
}
