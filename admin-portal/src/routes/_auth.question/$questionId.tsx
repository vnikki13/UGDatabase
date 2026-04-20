import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router'
import { getQuestion, getTags, updateQuestion } from '../../api';
import type { AnswerChoice, Tag } from '../../types';
import { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import { FormControl, InputLabel, Select, OutlinedInput, MenuItem, Checkbox, ListItemText, TextField, Button } from '@mui/material';
import { useAppForm } from '../../hooks/questionForm';

export const Route = createFileRoute('/_auth/question/$questionId')({
    component: RouteComponent,
})

type AnswerChoiceFormValues = {
    text: string
    is_correct: boolean
}

type QuestionFormValues = {
    prompt: string
    mediaStoragePath?: string
    mediaContentType?: string
    explanation?: string
    tags: Tag[]
    answerChoices: AnswerChoiceFormValues[]
}

function RouteComponent() {
    const { questionId } = Route.useParams();

    const [updateError, setUpdateError] = useState<string | null>(null);
    const [updateSuccess, setUpdateSuccess] = useState<boolean>(false);

    const { data, isLoading, error } = useQuery({
        queryKey: ['question', questionId],
        queryFn: () => getQuestion(questionId),
    });

    const { data: tagOptions = [] } = useQuery({
        queryKey: ['tags'],
        queryFn: getTags,
    });

    const form = useAppForm({
        defaultValues: {
            prompt: '',
            mediaStoragePath: '',
            mediaContentType: '',
            explanation: '',
            tags: [],
            answerChoices: [],
        } as QuestionFormValues,
        onSubmit: async ({ value }) => {
            setUpdateError(null)
            setUpdateSuccess(false)
            try {
                await updateQuestion(questionId, {
                    prompt: value.prompt,
                    media_storage_path: value.mediaStoragePath || '',
                    media_content_type: value.mediaContentType || '',
                    explanation: value.explanation,
                    tags: value.tags,
                    answerChoices: value.answerChoices,
                });
                setUpdateSuccess(true)
            } catch (err) {
                if (err instanceof AxiosError) {
                    setUpdateError(err?.message || 'Failed to create question');
                }
            }
        },
    })

    useEffect(() => {
        if (data) {
            form.reset({
                prompt: data.prompt || '',
                mediaStoragePath: data.media_storage_path || '',
                mediaContentType: data.media_content_type || '',
                explanation: data.explanation || '',
                tags: data.tags || [],
                answerChoices: (data.answerChoices || []).map((a: AnswerChoice) => ({
                    text: a.text,
                    is_correct: a.is_correct,
                })),
            });
        }
    }, [data]);

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div>Error loading question</div>;

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
                    form.reset()
                }}
                autoComplete='off'
            >
                <div>
                    <form.AppField
                        name='prompt'
                        children={(field) => (
                            <field.TextField label='Prompt' />
                        )}
                    />
                    <form.AppField
                        name='explanation'
                        children={(field) => (
                            <field.TextField label='Explanation' />
                        )}
                    />
                    <form.AppField
                        name='mediaStoragePath'
                        children={(field) => (
                            <field.TextField label='Media Storage Path' isRequired={false} />
                        )}
                    />
                    <form.AppField
                        name='mediaContentType'
                        children={(field) => (
                            <field.TextField label='Media Content Type' isRequired={false} />
                        )}
                    />
                    <form.Field
                        name="tags"
                        mode="array"
                        children={({ state, handleChange }) => {
                            const selectedTagNames = (state.value || []).map((t: Tag) => t.name);
                            return (
                                <FormControl sx={{ m: 1, width: 300 }}>
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
                                </FormControl>
                            );
                        }}
                    />
                </div>
                <form.Field
                    name="answerChoices"
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
                        return (
                            <FormControl component="fieldset" sx={{ m: 1, width: 400 }}>
                                <label style={{ marginBottom: 8 }}>Answer Choices</label>
                                {answerChoices.map((choice, idx) => (
                                    <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                                        <TextField
                                            label={`Choice ${idx + 1}`}
                                            variant="outlined"
                                            value={choice.text}
                                            onChange={(e) => handleTextChange(idx, e.target.value)}
                                            multiline
                                            required
                                            sx={{ flex: 1, marginRight: 2 }}
                                        />
                                        <input
                                            type="radio"
                                            name="correctAnswer"
                                            checked={choice.is_correct}
                                            onChange={() => handleRadioChange(idx)}
                                            required
                                            style={{ marginLeft: 8 }}
                                        />
                                        <span style={{ marginLeft: 4 }}>Correct</span>
                                    </div>
                                ))}
                            </FormControl>
                        );
                    }}
                />
                <div style={{ alignSelf: 'center', marginTop: 24 }}>
                    {updateError && (
                        <div style={{ color: 'red', marginBottom: 8 }}>{updateError}</div>
                    )}
                    {updateSuccess && (
                        <div style={{ color: 'green', marginBottom: 8 }}>Question created successfully!</div>
                    )}
                    <form.Subscribe
                        selector={(state) => [state.canSubmit, state.isSubmitting]}
                        children={([canSubmit, isSubmitting]) => (
                            <div>
                                <Button type='reset' variant='outlined'>
                                    Reset
                                </Button>
                                <Button
                                    style={{ margin: 10 }}
                                    type='submit'
                                    variant='contained'
                                    disabled={!canSubmit}
                                    loading={isSubmitting}
                                >
                                    Submit
                                </Button>
                            </div>
                        )}
                    />
                </div>
            </form >
        </div>
    )
}
