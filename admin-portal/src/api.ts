import type { Questions, Tag } from './types'
import axios, { AxiosError } from 'axios'

export interface CreateQuestionRequest {
  prompt: string
  media_storage_path?: string | null
  media_content_type?: string | null
  explanation?: string
  tags: Tag[]
  answerChoices: { text: string; is_correct: boolean }[]
}

const API_URL = import.meta.env.VITE_API_URL

export const getAuthorizedUser = async (userEmail: string | undefined) => {
  return axios.get(`${API_URL}/ghost/users/${userEmail}`)
}

export const getQuestions = async (): Promise<Questions> => {
  return (await axios.get(`${API_URL}/questions/`)).data
}

export const getTags = async (): Promise<Tag[]> => {
  return (await axios.get(`${API_URL}/tags/`)).data
}

export const createQuestion = async (data: CreateQuestionRequest): Promise<Questions> => {
  try {
    const res = await axios.post(`${API_URL}/questions/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
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

