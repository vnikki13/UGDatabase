export const ACCEPTED_MEDIA_FILE_TYPES = [
    'image/png',
    'image/jpeg',
    'image/jpg',
    'video/mp4',
    'video/quicktime',
    'video/x-quicktime',
    '.mov',
    'application/pdf',
]

export const inferContentTypeFromFileName = (fileName: string): string | undefined => {
    const normalized = fileName.toLowerCase()
    if (normalized.endsWith('.mov')) return 'video/quicktime'
    if (normalized.endsWith('.mp4')) return 'video/mp4'
    if (normalized.endsWith('.pdf')) return 'application/pdf'
    if (normalized.endsWith('.png')) return 'image/png'
    if (normalized.endsWith('.jpg') || normalized.endsWith('.jpeg')) return 'image/jpeg'
    return undefined
}

export const getFileContentType = (file: File): string | undefined => {
    return file.type || inferContentTypeFromFileName(file.name)
}

export const isVideoContentType = (contentType?: string | null): boolean => {
    return Boolean(contentType?.startsWith('video/'))
}

export const isVideoFile = (file: File): boolean => {
    return isVideoContentType(getFileContentType(file))
}