export interface Questions {
  data: Question[]
  count: number
}

export interface Question {
  prompt: string
  media_content_type: null | string
  explanation: string
  id: string
  tags: QuestionTag[]
  answerChoices: AnswerChoice[]
}

export interface AnswerChoice {
  id: string
  text: string
  is_correct: boolean
}

export interface Tag {
  name: string
}

export interface QuestionTag {
  id: string
  name: string
  deleted_at: string | null
}

export interface TagWithId {
  id: string
  name: string
  created_at: string
  updated_at: string | null
  deleted_at: string | null
}

export interface AuditEvent {
  id: string
  occurred_at: string
  request_id: string | null
  actor_email: string | null
  actor_source: string
  action: string
  entity_type: string
  entity_id: string | null
  before_json: Record<string, unknown> | null
  after_json: Record<string, unknown> | null
  metadata_json: Record<string, unknown> | null
}

export interface AdminCreateExamRequest {
  member_uuids: string[]
  question_ids: string[]
}

export interface Exam {
  exam_id: string
  member_id: string
  started_at: string | null
  question_count: number
  tags: Tag[] | null
  filters: string[]
  questions: Question[]
}

export interface ExamSummary {
  id: string
  member_id: string
  started_at: string | null
  updated_at: string | null
  completed_at: string | null
  score: number | null
  question_count: number
  tags: Tag[] | null
  filters: string[] | null
}

export interface ExamListResponse {
  exams: ExamSummary[]
  count: number
}

export interface Member {
  id: string;
  uuid: string;
  email: string;
  name: string;
  note: null;
  geolocation: null | string;
  subscribed: boolean;
  created_at: string;
  updated_at: string;
  labels: Labels[] | unknown[];
  subscriptions: Subscriptions[] | unknown[];
  avatar_image: string;
  comped: boolean;
  email_count: number;
  email_opened_count: number;
  email_open_rate: null;
  status: string;
  last_seen_at: null | string;
  unsubscribe_url: string;
  can_comment: boolean;
  commenting: Commenting;
  email_suppression: EmailSuppression;
  newsletters: Newsletters[] | unknown[];
}

export interface Newsletters {
  id: string;
  name: string;
  description: string;
  status: string;
}

export interface EmailSuppression {
  suppressed: boolean;
  info: null;
}

export interface Commenting {
  disabled: boolean;
  disabled_reason: null;
  disabled_until: null;
}

export interface Subscriptions {
  id: string;
  customer: Customer;
  plan: Plan;
  status: string;
  start_date: string;
  default_payment_card_last4: null;
  cancel_at_period_end: boolean;
  cancellation_reason: null;
  current_period_end: string;
  trial_start_at: null;
  trial_end_at: null;
  discount_start: null;
  discount_end: null;
  price: Price;
  tier: Tier2;
  offer: null;
  offer_redemptions: unknown[];
  next_payment: NextPayment;
}

export interface NextPayment {
  original_amount: number;
  amount: number;
  interval: string;
  currency: string;
  discount?: null;
}

export interface Tier2 {
  id: string;
  name: string;
  slug: string;
  monthly_price_id: string;
  yearly_price_id: string;
  description: string;
  created_at: string;
  updated_at: string;
  type: string;
  active: boolean;
  welcome_page_url: string;
  visibility: string;
  trial_days: number;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  expiry_at?: null;
}

export interface Price {
  id: string;
  price_id: string;
  nickname: string;
  amount: number;
  interval: string;
  type: string;
  currency: string;
  tier: Tier;
}

export interface Tier {
  id: string;
  name: string;
  tier_id: string;
}

export interface Plan {
  id: string;
  nickname: string;
  amount: number;
  interval: string;
  currency: string;
}

export interface Customer {
  id: string;
  name?: null;
  email: string;
}

export interface Labels {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}
