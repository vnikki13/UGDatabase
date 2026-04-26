
import { createFileRoute } from '@tanstack/react-router'
import { createQuestion, getTags } from '../../api'
import { type Tag } from '../../types'
import { useState, useRef } from 'react'
import { AxiosError } from 'axios'
import { useAppForm } from '../../hooks/questionForm'
import { FormControl, TextField, InputLabel, Select, OutlinedInput, MenuItem, Checkbox, ListItemText, Box, FormHelperText } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { FilePond, registerPlugin } from 'react-filepond'
import FilePondPluginFileValidateType from 'filepond-plugin-file-validate-type'
import 'filepond/dist/filepond.min.css'
import type { FilePondFile } from 'filepond'
import { FormActionFooter } from '../../components/FormActionFooter'
import { useAuth } from '../../auth'

registerPlugin(FilePondPluginFileValidateType)

export const Route = createFileRoute('/_auth/question/')({
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

function RouteComponent() {
    const { user } = useAuth()
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
    const [files, setFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const createdQuestionIdRef = useRef<string | null>(null);

    const { data: tagOptions = [] } = useQuery({
        queryKey: ['tags'],
        queryFn: getTags,
    });

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
                const errorBody = await response.text();
                throw new Error(`Failed to upload file (${response.status}): ${errorBody || response.statusText}`);
            }
        } catch (err) {
            throw new Error(err instanceof Error ? err.message : 'Failed to upload file to storage');
        }
    };

    const form = useAppForm({
        defaultValues: {
            prompt: '',
            mediaContentType: '',
            explanation: '',
            tags: [],
            answerChoices: [],
        } as QuestionFormValues,
        onSubmit: async ({ value }) => {
            setSubmitError(null);
            setSubmitSuccess(false);
            setIsUploading(true);

            try {
                const file = files.length > 0 ? files[0] : null;
                const payload = {
                    prompt: value.prompt,
                    media_content_type: null,
                    explanation: value.explanation,
                    tags: value.tags,
                    answerChoices: value.answerChoices,
                };
                const createdQuestion = await createQuestion(payload, file?.type, user?.email);
                createdQuestionIdRef.current = createdQuestion.id;

                // Upload file directly to the signed URL returned with the question
                if (file && createdQuestion.upload_url) {
                    await uploadFileToGCS(file, createdQuestion.upload_url);
                }

                setSubmitSuccess(true);
                form.reset();
                setFiles([]);
            } catch (err: unknown) {
                if (err instanceof AxiosError) {
                    setSubmitError(err?.message || 'Failed to create question');
                } else if (err instanceof Error) {
                    setSubmitError(err.message);
                } else {
                    setSubmitError('Failed to create question');
                }
            } finally {
                setIsUploading(false);
            }
        },
    })

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1>Add a new question</h1>
            <form
                style={{ display: 'flex', flexDirection: 'column' }}
                onSubmit={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    form.handleSubmit()
                }}
                onReset={() => {
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
                        {files.length > 0 && (
                            <Box sx={{ marginBottom: 2, padding: 2, backgroundColor: '#f0f7ff', borderRadius: 1, border: '1px solid #b3d9ff' }}>
                                <div style={{ marginBottom: 8, fontSize: 14, color: '#0066cc', fontWeight: 500 }}>Media preview:</div>
                                {files[0].type.startsWith('image/') ? (
                                    <img
                                        src={URL.createObjectURL(files[0])}
                                        alt="Media preview"
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
                        )}
                        <FilePond
                            files={files}
                            onupdatefiles={(fileItems: FilePondFile[]) => {
                                setFiles(fileItems.map((fileItem) => fileItem.file as File));
                            }}
                            maxFiles={1}
                            acceptedFileTypes={['image/png', 'image/jpeg', 'image/jpg', 'video/mp4', 'application/pdf']}
                            labelIdle='Drag and drop your media file or <span class="filepond--label-action">browse</span>'
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
                                successMessage={submitSuccess ? 'Question created successfully!' : null}
                                errorMessage={submitError}
                                onCloseSuccess={() => { setSubmitSuccess(false) }}
                                onCloseError={() => { setSubmitError(null) }}
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
