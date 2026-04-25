import type { Questions, Question, Tag, Member, AdminCreateExamRequest, Exam } from './types'
import axios, { AxiosError } from 'axios'

export interface CreateQuestionRequest {
  prompt: string
  media_content_type?: string | null
  explanation?: string
  tags: Tag[]
  answerChoices: { text: string; is_correct: boolean }[]
}

export interface UpdateQuestionRequest {
  prompt: string
  media_content_type?: string | null
  explanation?: string
  tags: Tag[]
  answerChoices: { text: string; is_correct: boolean }[]
}

const LOCAL_API_URL = 'http://localhost:8000/api/v1'
const isLocalFrontend =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

const envApiUrl = (import.meta.env.VITE_API_URL ?? '').trim()
const resolvedApiUrl = isLocalFrontend ? LOCAL_API_URL : envApiUrl

if (!resolvedApiUrl) {
  throw new Error('VITE_API_URL must be set for non-local environments')
}

if (!/^https?:\/\//i.test(resolvedApiUrl)) {
  throw new Error('VITE_API_URL must include http:// or https://')
}

const API_URL = resolvedApiUrl.replace(/\/$/, '')

export const getAuthorizedUser = async (userEmail: string | undefined) => {
  return axios.get(`${API_URL}/ghost/users/${userEmail}`)
}

export const searchMembers = async (search: string): Promise<Member[]> => {
  return (await axios.get(`${API_URL}/ghost/members?search=${search}`)).data
}

export const getQuestions = async (): Promise<Questions> => {
  return (await axios.get(`${API_URL}/questions/`)).data
}

export const getQuestion = async (questionId: string): Promise<Question> => {
  return (await axios.get(`${API_URL}/questions/${questionId}`)).data
}

export const getTags = async (): Promise<Tag[]> => {
  return (await axios.get(`${API_URL}/tags/`)).data
}

export const createQuestion = async (data: CreateQuestionRequest, contentType?: string): Promise<Question & { upload_url?: string }> => {
  try {
    const res = await axios.post(`${API_URL}/questions/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
      params: contentType ? { content_type: contentType } : undefined,
    });
    return res.data;
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to create question');
    } else {
      throw new Error('Unable to create question')
    }
  }
}

export const updateQuestion = async (
  id: string,
  data: UpdateQuestionRequest,
  contentType?: string,
): Promise<Question & { upload_url?: string }> => {
  try {
    const res = await axios.put(`${API_URL}/questions/${id}`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
      params: contentType ? { content_type: contentType } : undefined,
    });
    return res.data;
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to update question');
    } else {
      throw new Error('Unable to update question')
    }
  }
}


export const getSignedUploadUrl = async (questionId: string, contentType: string) => {
  try {
    const res = await axios.post(`${API_URL}/media/upload-url`, null, {
      params: {
        question_id: questionId,
        content_type: contentType,
      },
    });
    return res.data;
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to get upload URL');
    } else {
      throw new Error('Unable to get upload URL')
    }
  }
}

export const getSignedDownloadUrl = async (questionId: string) => {
  try {
    const res = await axios.get(`${API_URL}/media/download-url`, {
      params: {
        question_id: questionId,
      },
    });
    return res.data;
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to get download URL');
    } else {
      throw new Error('Unable to get download URL')
    }
  }
}

export const createAdminExam = async (data: AdminCreateExamRequest): Promise<Exam[]> => {
    try {
    const res = await axios.post(`${API_URL}/exams/admin`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return res.data;
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to create admin exam');
    } else {
      throw new Error('Unable to create admin exam')
    }
  }
}

