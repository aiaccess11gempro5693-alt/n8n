export interface NavItem {
  label: string;
  id: string;
}

export interface RealityItem {
  num: string;
  icon: string;
  title: string;
  description: string;
  note?: string;
}

export interface PainItem {
  icon: string;
  title: string;
  description: string;
  note?: string;
}

export interface Figure {
  value: number;
  suffix: string;
  label: string;
}

export interface SegmentItem {
  icon: string;
  tag: string;
  title: string;
  task: string;
  solution: string;
  offer: string;
}

export interface ChartBar {
  label: string;
  value: number;
  type: string;
}

export interface CaseItem {
  tag: string;
  title: string;
  metric: string;
  before: number;
  after: number;
  delta: string;
}

export interface SiteContent {
  siteName: string;
  meta: { title: string; description: string; ogType: string };
  nav: NavItem[];
  hero: {
    title: string;
    subtitle: string;
    statement: string;
    cta: string;
    badges: string[];
  };
  reality: { title: string; items: RealityItem[] };
  pain: { title: string; items: PainItem[] };
  amplify: {
    title: string;
    figures: Figure[];
    flow: { title: string; steps: string[]; hub: string; result: string };
    comparison: { leftTitle: string; rightTitle: string; rows: string[][] };
    conclusion: string;
  };
  solution: {
    title: string;
    steps: string[];
    loopNote: string;
    description: string;
  };
  segments: { title: string; items: SegmentItem[] };
  trust: {
    title: string;
    quote: string;
    quoteSource: string;
    chart: {
      title: string;
      bars: ChartBar[];
      legend: { type: string; label: string }[];
    };
    conclusion: string;
    statsTitle: string;
    stats: { value: number; suffix: string; label: string }[];
    residency: string;
    note: string;
  };
  cases: { title: string; intro: string; items: CaseItem[]; disclaimer: string };
  economy: {
    title: string;
    leftTitle: string;
    rightTitle: string;
    rows: string[][];
    conclusion: string;
  };
  faq: { title: string; items: { q: string; a: string }[] };
  finalCta: {
    title: string;
    listTitle: string;
    list: string[];
    formTitle: string;
    fields: { name: string; company: string; contact: string };
    cta: string;
    note: string;
    successTitle: string;
    successText: string;
  };
  footer: {
    title: string;
    email: string;
    phone: string;
    telegram: string;
    sites: string[];
    copyright: string;
  };
}
