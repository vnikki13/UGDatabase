import { useQuery, useQueryClient } from '@tanstack/react-query';
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { getQuestion, getSignedDownloadUrl, getTags, updateQuestion } from '../../api';
import type { AnswerChoice, Question, Tag } from '../../types';
import { useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { FormControl, InputLabel, Select, OutlinedInput, MenuItem, Checkbox, ListItemText, TextField, Button, Box, CircularProgress, FormHelperText } from '@mui/material';
import { useAppForm } from '../../hooks/questionForm';
import { FilePond, registerPlugin } from 'react-filepond'
import FilePondPluginFileValidateType from 'filepond-plugin-file-validate-type'
import type { FilePondFile } from 'filepond'
import 'filepond/dist/filepond.min.css'
import { FormActionFooter } from '../../components/FormActionFooter';

registerPlugin(FilePondPluginFileValidateType)

export const Route = createFileRoute('/_auth/question/$questionId')({
    component: RouteComponent,
})

type AnswerChoiceFormValues = {
    text: string
    is_correct: boolean
}

type QuestionFormValues = {
    prompt: string
    mediaContentType?: string
    explanation?: string
    tags: Tag[]
    answerChoices: AnswerChoiceFormValues[]
}

const toQuestionFormValues = (question: Question): QuestionFormValues => ({
    prompt: question.prompt || '',
    mediaContentType: question.media_content_type || '',
    explanation: question.explanation || '',
    tags: question.tags || [],
    answerChoices: (question.answerChoices || []).map((answerChoice: AnswerChoice) => ({
        text: answerChoice.text,
        is_correct: answerChoice.is_correct,
    })),
})

function RouteComponent() {
    const { questionId } = Route.useParams();

    const { data, isLoading, error } = useQuery({
        queryKey: ['question', questionId],
        queryFn: () => getQuestion(questionId),
    });

    const { data: tagOptions = [] } = useQuery({
        queryKey: ['tags'],
        queryFn: getTags,
    });

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div>Error loading question</div>;
    if (!data) return <div>Question not found</div>;

    return <QuestionEditForm key={data.id} question={data} questionId={questionId} tagOptions={tagOptions} />
}

function QuestionEditForm({
    question,
    questionId,
    tagOptions,
}: {
    question: Question
    questionId: string
    tagOptions: Tag[]
}) {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [updateError, setUpdateError] = useState<string | null>(null);
    const [updateSuccess, setUpdateSuccess] = useState<boolean>(false);
    const [files, setFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const [deleteMedia, setDeleteMedia] = useState(false);
    const [isImageLoading, setIsImageLoading] = useState(false);

    const { data: downloadUrlData, isLoading: isDownloadUrlLoading } = useQuery({
        queryKey: ['media-download-url', questionId],
        queryFn: () => getSignedDownloadUrl(questionId),
        enabled: !!question.media_content_type,
    });

    useEffect(() => {
        const shouldLoadImage = Boolean(
            downloadUrlData?.download_url && downloadUrlData?.content_type?.startsWith('image/')
        );
        setIsImageLoading(shouldLoadImage);
    }, [downloadUrlData?.download_url, downloadUrlData?.content_type]);

    const uploadFileToGCS = async (file: File, uploadUrl: string): Promise<void> => {
        try {
            const response = await fetch(uploadUrl, {
                method: 'PUT',
                body: file,
                headers: {
                    'Content-Type': file.type,
                },
            });

            if (!response.ok) {
                const errorBody = await response.text()
                throw new Error(`Failed to upload file (${response.status}): ${errorBody || response.statusText}`)
            }
        } catch (err) {
            throw new Error(err instanceof Error ? err.message : 'Failed to upload file to storage')
        }
    }

    const form = useAppForm({
        defaultValues: toQuestionFormValues(question),
        onSubmit: async ({ value }) => {
            setUpdateError(null)
            setUpdateSuccess(false)
            setIsUploading(true)
            try {
                const hasReplacementFile = files.length > 0
                const replacementFile = hasReplacementFile ? files[0] : null
                const mediaContentType = deleteMedia
                    ? null
                    : hasReplacementFile
                        ? replacementFile?.type || null
                        : (value.mediaContentType || null)

                const updatedQuestion = await updateQuestion(questionId, {
                    prompt: value.prompt,
                    media_content_type: mediaContentType,
                    explanation: value.explanation,
                    tags: value.tags,
                    answerChoices: value.answerChoices,
                }, replacementFile?.type);

                if (replacementFile) {
                    if (!updatedQuestion.upload_url) {
                        throw new Error('Missing upload URL for updated question media')
                    }
                    await uploadFileToGCS(replacementFile, updatedQuestion.upload_url)
                }

                setUpdateSuccess(true)
                // Invalidate the download URL query to refetch the new media
                await queryClient.invalidateQueries({ queryKey: ['media-download-url', questionId] });
                await queryClient.invalidateQueries({ queryKey: ['media-download-url', updatedQuestion.id] });
                // Invalidate the question query to update form values
                await queryClient.invalidateQueries({ queryKey: ['question', questionId] });
                await queryClient.invalidateQueries({ queryKey: ['question', updatedQuestion.id] });
                setDeleteMedia(false);

                if (updatedQuestion.id !== questionId) {
                    await navigate({
                        to: '/question/$questionId',
                        params: { questionId: updatedQuestion.id },
                        replace: true,
                    });
                } else {
                    // Only clear local preview when staying on the same route.
                    // When versioning returns a new question ID, keep preview visible
                    // until navigation completes to avoid flashing old media.
                    setFiles([])
                }
            } catch (err) {
                if (err instanceof AxiosError) {
                    setUpdateError(err?.message || 'Failed to update question');
                } else if (err instanceof Error) {
                    setUpdateError(err.message)
                } else {
                    setUpdateError('Failed to update question')
                }
            } finally {
                setIsUploading(false)
            }
        },
    })

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1>Update a question</h1>
            <form
                style={{ display: 'flex', flexDirection: 'column' }}
                onSubmit={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    form.handleSubmit()
                }}
                onReset={() => {
                    setUpdateError(null)
                    setUpdateSuccess(false)
                    setFiles([])
                    setDeleteMedia(false)
                    form.reset()
                }}
                autoComplete='off'
                noValidate
            >
                <div>
                    <form.AppField
                        name='prompt'
                        validators={{
                            onChange: ({ value }) => !value?.trim() ? 'Prompt is required' : undefined,
                            onSubmit: ({ value }) => !value?.trim() ? 'Prompt is required' : undefined,
                        }}
                        children={(field) => (
                            <field.TextField label='Prompt' />
                        )}
                    />
                    <form.AppField
                        name='explanation'
                        validators={{
                            onChange: ({ value }) => !value?.trim() ? 'Explanation is required' : undefined,
                            onSubmit: ({ value }) => !value?.trim() ? 'Explanation is required' : undefined,
                        }}
                        children={(field) => (
                            <field.TextField label='Explanation' />
                        )}
                    />
                    <Box sx={{ my: 2 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>Media (Optional)</label>
                        {files.length > 0 ? (
                            <Box sx={{ marginBottom: 2, padding: 2, backgroundColor: '#f0f7ff', borderRadius: 1, border: '1px solid #b3d9ff' }}>
                                <div style={{ marginBottom: 8, fontSize: 14, color: '#0066cc', fontWeight: 500 }}>New media preview:</div>
                                {files[0].type.startsWith('image/') ? (
                                    <img
                                        src={URL.createObjectURL(files[0])}
                                        alt="New media preview"
                                        style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }}
                                    />
                                ) : files[0].type === 'video/mp4' ? (
                                    <video
                                        src={URL.createObjectURL(files[0])}
                                        controls
                                        style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }}
                                    />
                                ) : files[0].type === 'application/pdf' ? (
                                    <iframe
                                        src={URL.createObjectURL(files[0])}
                                        style={{ width: '100%', height: 400, borderRadius: 4 }}
                                    />
                                ) : (
                                    <div style={{ fontSize: 14, color: '#666' }}>
                                        File: {files[0].name}
                                    </div>
                                )}
                            </Box>
                        ) : question.media_content_type ? (
                            <Box sx={{ marginBottom: 2, padding: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                                {deleteMedia ? (
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ fontSize: 14, color: '#d32f2f', fontWeight: 500 }}>Media will be deleted on submit</div>
                                        <Button
                                            type="button"
                                            size="small"
                                            variant="outlined"
                                            onClick={() => setDeleteMedia(false)}
                                        >
                                            Cancel Delete
                                        </Button>
                                    </Box>
                                ) : (
                                    <>
                                        <div style={{ marginBottom: 8, fontSize: 14, color: '#666', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span>Current media:</span>
                                            <Button
                                                type="button"
                                                size="small"
                                                color="error"
                                                variant="outlined"
                                                onClick={() => setDeleteMedia(true)}
                                            >
                                                Delete Media
                                            </Button>
                                        </div>
                                    </>
                                )}
                                {!deleteMedia && (
                                    <>
                                        {isDownloadUrlLoading && (
                                            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                                                <CircularProgress size={24} />
                                            </Box>
                                        )}
                                        {!isDownloadUrlLoading && downloadUrlData?.content_type?.startsWith('image/') ? (
                                            <Box sx={{ position: 'relative', display: 'inline-flex', minHeight: 40 }}>
                                                {isImageLoading && (
                                                    <Box
                                                        sx={{
                                                            position: 'absolute',
                                                            top: 0,
                                                            right: 0,
                                                            bottom: 0,
                                                            left: 0,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            backgroundColor: 'rgba(255, 255, 255, 0.65)',
                                                            borderRadius: 1,
                                                            zIndex: 1,
                                                        }}
                                                    >
                                                        <CircularProgress size={28} />
                                                    </Box>
                                                )}
                                                <img
                                                    src={downloadUrlData?.download_url}
                                                    alt="Question media"
                                                    onLoad={() => setIsImageLoading(false)}
                                                    onError={() => setIsImageLoading(false)}
                                                    style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }}
                                                />
                                            </Box>
                                        ) : !isDownloadUrlLoading && downloadUrlData?.content_type === 'video/mp4' ? (
                                            <video
                                                src={downloadUrlData?.download_url}
                                                controls
                                                style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }}
                                            />
                                        ) : !isDownloadUrlLoading && downloadUrlData?.content_type === 'application/pdf' ? (
                                            <iframe
                                                src={downloadUrlData?.download_url}
                                                style={{ width: '100%', height: 400, borderRadius: 4 }}
                                            />
                                        ) : !isDownloadUrlLoading && downloadUrlData?.download_url ? (
                                            <a href={downloadUrlData?.download_url} target="_blank" rel="noopener noreferrer">
                                                View file
                                            </a>
                                        ) : null}
                                    </>
                                )}
                            </Box>
                        ) : null}
                        <FilePond
                            files={files}
                            onupdatefiles={(fileItems: FilePondFile[]) => {
                                setFiles(fileItems.map((fileItem) => fileItem.file as File))
                            }}
                            allowMultiple={false}
                            maxFiles={1}
                            acceptedFileTypes={['image/png', 'image/jpeg', 'image/jpg', 'video/mp4', 'application/pdf']}
                            labelIdle='Drag and drop a replacement media file or <span class="filepond--label-action">browse</span>'
                            credits={false}
                        />
                    </Box>
                    <form.Field
                        name="tags"
                        mode="array"
                        validators={{
                            onChange: ({ value }) => value.length === 0 ? 'Select at least one tag' : undefined,
                            onSubmit: ({ value }) => value.length === 0 ? 'Select at least one tag' : undefined,
                        }}
                        children={({ state, handleChange }) => {
                            const selectedTagNames = (state.value || []).map((t: Tag) => t.name);
                            const tagError = state.meta.errors.length > 0
                                ? String(state.meta.errors[0])
                                : undefined;
                            return (
                                <FormControl sx={{ m: 1, width: 300 }} error={!!tagError}>
                                    <InputLabel id="demo-multiple-name-label" required>Tags</InputLabel>
                                    <Select
                                        multiple
                                        value={selectedTagNames}
                                        onChange={(e) => {
                                            const value = typeof e.target.value === 'string'
                                                ? e.target.value.split(',')
                                                : e.target.value;
                                            handleChange(value.map((name) => ({ name })))
                                        }}
                                        input={<OutlinedInput label="Tags" />}
                                        renderValue={(selected) => (selected as string[]).join(', ')}
                                        required
                                    >
                                        {tagOptions.map((tag: Tag) => (
                                            <MenuItem key={tag.name} value={tag.name}>
                                                <Checkbox checked={selectedTagNames.indexOf(tag.name) > -1} />
                                                <ListItemText primary={tag.name} />
                                            </MenuItem>
                                        ))}
                                    </Select>
                                    {tagError && <FormHelperText>{tagError}</FormHelperText>}
                                </FormControl>
                            );
                        }}
                    />
                </div>
                <form.Field
                    name="answerChoices"
                    validators={{
                        onChange: ({ value }) => {
                            if (value.some((c) => !c.text?.trim())) return 'All answer choices must have text'
                            if (!value.some((c) => c.is_correct)) return 'Select a correct answer'
                            return undefined
                        },
                        onSubmit: ({ value }) => {
                            if (value.some((c) => !c.text?.trim())) return 'All answer choices must have text'
                            if (!value.some((c) => c.is_correct)) return 'Select a correct answer'
                            return undefined
                        },
                    }}
                    children={({ state, handleChange }) => {
                        const answerChoices = state.value.length === 4
                            ? state.value
                            : Array.from({ length: 4 }, (_, i) => state.value[i] || { text: '', is_correct: false });

                        const handleTextChange = (idx: number, text: string) => {
                            const updated = answerChoices.map((c, i) => i === idx ? { ...c, text } : c);
                            handleChange(updated);
                        };
                        const handleRadioChange = (idx: number) => {
                            const updated = answerChoices.map((c, i) => ({ ...c, is_correct: i === idx }));
                            handleChange(updated);
                        };
                        const choicesError = state.meta.errors.length > 0
                            ? String(state.meta.errors[0])
                            : undefined;
                        return (
                            <FormControl component="fieldset" sx={{ m: 1, width: { xs: '100%', sm: 400 } }} error={!!choicesError}>
                                <label style={{ marginBottom: 8 }}>Answer Choices</label>
                                {answerChoices.map((choice, idx) => (
                                    <Box
                                        key={idx}
                                        sx={{
                                            display: 'flex',
                                            flexDirection: { xs: 'column', sm: 'row' },
                                            alignItems: { xs: 'flex-start', sm: 'center' },
                                            marginBottom: 1.5,
                                            gap: { xs: 0.5, sm: 0 },
                                        }}
                                    >
                                        <TextField
                                            label={`Choice ${idx + 1}`}
                                            variant="outlined"
                                            value={choice.text}
                                            onChange={(e) => handleTextChange(idx, e.target.value)}
                                            multiline
                                            required
                                            sx={{ flex: 1, width: '100%', marginRight: { sm: 2 } }}
                                        />
                                        <Box
                                            component="label"
                                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: { xs: 0, sm: 1 }, cursor: 'pointer', userSelect: 'none', WebkitTapHighlightColor: 'transparent' }}
                                        >
                                            <input
                                                type="radio"
                                                name="correctAnswer"
                                                checked={choice.is_correct}
                                                onChange={() => handleRadioChange(idx)}
                                                required
                                            />
                                            Correct
                                        </Box>
                                    </Box>
                                ))}
                                {choicesError && <FormHelperText>{choicesError}</FormHelperText>}
                            </FormControl>
                        );
                    }}
                />
                <div>
                    <form.Subscribe
                        selector={(state) => [state.canSubmit, state.isSubmitting]}
                        children={([canSubmit, isSubmitting]) => (
                            <FormActionFooter
                                canSubmit={canSubmit}
                                isSubmitting={isSubmitting}
                                isBusy={isUploading}
                                submitLabel="Submit"
                                busyLabel="Uploading..."
                                successMessage={updateSuccess ? 'Question updated successfully!' : null}
                                errorMessage={updateError}
                                onCloseSuccess={() => { setUpdateSuccess(false) }}
                                onCloseError={() => { setUpdateError(null) }}
                                disableReset={isUploading || isSubmitting}
                                disableSubmit={isUploading || isSubmitting}
                            />
                        )}
                    />
                </div>
            </form >
        </div>
    )
}
