export interface Questions {
  data: Question[]
  count: number
}

export interface Question {
  text: any
  is_correct: any
  prompt: string
  media_storage_path: null | string
  media_content_type: null | string
  explanation: string
  id: string
  tags: Tag[]
  answerChoices: AnswerChoice[]
  deleted_at: null
}

export interface AnswerChoice {
  id: string
  text: string
  is_correct: boolean
}

export interface Tag {
  name: string
}
