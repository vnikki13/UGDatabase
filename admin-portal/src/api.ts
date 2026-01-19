import axios from 'axios'
import type { Questions } from './types'

const API_URL = import.meta.env.VITE_API_URL

export const getAuthorizedUser = async (userEmail: string | undefined) => {
  return axios.get(`${API_URL}/ghost/users/${userEmail}`)
}

export const getQuestions = async (): Promise<Questions> => {
  return (await fetch(`${API_URL}/questions/`)).json()
}
