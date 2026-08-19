export interface NavItem {
  label: string;
  id: string;
}

export interface CommentItem {
  author: string;
  target: string;
  text: string;
}

export interface CardItem {
  title: string;
  text: string;
}

export interface StatItem {
  value: string;
  label: string;
}

export interface SegmentItem {
  level: string;
  text: string;
}

export interface CaseBlock {
  label: string;
  text: string;
}

export interface ContactItem {
  label: string;
  value: string;
  href: string;
}

export interface CompareBlock {
  left: string;
  right: string;
  params: string[];
}

export interface Section {
  id: string;
  num: string;
  kicker?: string;
  title: string;
  lead?: string[];
  listTitle?: string;
  list?: string[];
  flow?: string[];
  cards?: CardItem[];
  stats?: StatItem[];
  segments?: SegmentItem[];
  compare?: CompareBlock;
  caseBlocks?: CaseBlock[];
  contacts?: ContactItem[];
  logos?: string[];
  note?: string;
  offer?: string;
  conclusion?: string;
  comments?: CommentItem[];
}

export interface SiteContent {
  siteName: string;
  brand: {
    first: string;
    second: string;
  };
  ui: {
    menuLabel: string;
    commentLabel: string;
    logoPlaceholder: string;
  };
  meta: {

    title: string;
    description: string;
    ogType: string;
  };
  nav: NavItem[];
  hero: {
    brand: string;
    title: string;
    subtitle: string;
    note: string;
    cta: string;
  };
  sections: Section[];
  footer: {
    title: string;
    email: string;
    phone: string;
    sites: string[];
    copyright: string;
  };
}
