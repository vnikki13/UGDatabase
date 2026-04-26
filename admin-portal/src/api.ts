import type { Questions, Question, TagWithId, Member, AdminCreateExamRequest, Exam, AuditEvent, ExamListResponse } from './types'
import axios, { AxiosError } from 'axios'

type QuestionTagRef = {
  id: string
}

export interface CreateQuestionRequest {
  prompt: string
  media_content_type?: string | null
  explanation?: string
  tags: QuestionTagRef[]
  answerChoices: { text: string; is_correct: boolean }[]
}

export interface UpdateQuestionRequest {
  prompt: string
  media_content_type?: string | null
  explanation?: string
  tags: QuestionTagRef[]
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

export const getTags = async (): Promise<TagWithId[]> => {
  return (await axios.get(`${API_URL}/tags/`)).data
}

export const getTagById = async (tagId: string): Promise<TagWithId> => {
  return (await axios.get(`${API_URL}/tags/${tagId}`)).data
}

function actorHeaders(actorEmail?: string | null): Record<string, string> {
  if (!actorEmail) {
    return {}
  }
  return { 'x-admin-email': actorEmail }
}

export const createTag = async (name: string, actorEmail?: string | null): Promise<TagWithId> => {
  try {
    return (
      await axios.post(
        `${API_URL}/tags/`,
        { name },
        { headers: { 'Content-Type': 'application/json', ...actorHeaders(actorEmail) } },
      )
    ).data
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to create tag')
    }
    throw new Error('Unable to create tag')
  }
}

export const updateTag = async (tagId: string, name: string, actorEmail?: string | null): Promise<TagWithId> => {
  try {
    return (
      await axios.put(
        `${API_URL}/tags/${tagId}`,
        { name },
        { headers: { 'Content-Type': 'application/json', ...actorHeaders(actorEmail) } },
      )
    ).data
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to update tag')
    }
    throw new Error('Unable to update tag')
  }
}

export const deleteTag = async (tagId: string, actorEmail?: string | null): Promise<void> => {
  try {
    await axios.delete(`${API_URL}/tags/${tagId}`, { headers: actorHeaders(actorEmail) })
  } catch (err: unknown) {
    if (err instanceof AxiosError) {
      throw new Error(err?.response?.data?.detail || 'Failed to delete tag')
    }
    throw new Error('Unable to delete tag')
  }
}

export const createQuestion = async (
  data: CreateQuestionRequest,
  contentType?: string,
  actorEmail?: string | null,
): Promise<Question & { upload_url?: string }> => {
  try {
    const res = await axios.post(`${API_URL}/questions/`, data, {
      headers: {
        'Content-Type': 'application/json',
        ...actorHeaders(actorEmail),
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
  actorEmail?: string | null,
): Promise<Question & { upload_url?: string }> => {
  try {
    const res = await axios.put(`${API_URL}/questions/${id}`, data, {
      headers: {
        'Content-Type': 'application/json',
        ...actorHeaders(actorEmail),
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


export const getSignedUploadUrl = async (
  questionId: string,
  contentType: string,
  actorEmail?: string | null,
) => {
  try {
    const res = await axios.post(`${API_URL}/media/upload-url`, null, {
      headers: actorHeaders(actorEmail),
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

export const createAdminExam = async (data: AdminCreateExamRequest, actorEmail?: string | null): Promise<Exam[]> => {
    try {
    const res = await axios.post(`${API_URL}/exams/admin`, data, {
      headers: {
        'Content-Type': 'application/json',
        ...actorHeaders(actorEmail),
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

export const getAdminExams = async (): Promise<ExamListResponse> => {
  return (await axios.get(`${API_URL}/exams/admin`)).data
}

export const getAuditHistory = async (
  entityType: string,
  entityId: string,
  limit = 50,
): Promise<AuditEvent[]> => {
  return (
    await axios.get(`${API_URL}/audit-events/`, {
      params: { entity_type: entityType, entity_id: entityId, limit },
    })
  ).data
}

