import { createFileRoute } from '@tanstack/react-router'
import { useAppForm } from '../../hooks/questionForm';
import { Autocomplete, Checkbox, FormControlLabel, TextField } from '@mui/material';
import { useState, useEffect, useMemo, useRef } from 'react';
import { getQuestions, searchMembers, createAdminExam } from '../../api';
import type { Member, Question, Tag } from '../../types';
import { useQuery } from '@tanstack/react-query';
import type { GridApi, ColDef } from 'ag-grid-community';
import { AgGridReact } from 'ag-grid-react';
import { AxiosError } from 'axios';
import { FormActionFooter } from '../../components/FormActionFooter';
import { useAuth } from '../../auth';

interface GridRow {
    id: string
    prompt: string;
    explanation: string;
    tags: string;
}

export const Route = createFileRoute('/_auth/exam/')({
    component: RouteComponent,
})

type ExamFormValues = {
    questionIds: string[]
    members: Member[]
    tutor: boolean
}

function RouteComponent() {
    const { user } = useAuth();
    const [memberOptions, setMemberOptions] = useState<Member[]>([]);
    const [searchValue, setSearchValue] = useState('');
    const [loading, setLoading] = useState(false);
    const [gridApi, setGridApi] = useState<GridApi<GridRow>>();
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const isClearingSelectionRef = useRef(false);

    const { data: questions } = useQuery({
        queryKey: ['questions'],
        queryFn: getQuestions,
    });

    const rowData = useMemo(() => {
        if (!questions?.data) return [];
        return questions.data.map((q: Question) => ({
            ...q,
            tags: Array.isArray(q.tags) ? q.tags.map((t: Tag) => t.name).join(', ') : q.tags,
        }));
    }, [questions]);

    const colDefs: ColDef<GridRow>[] = [
        { field: 'prompt' as const, headerName: 'Prompt', flex: 2, },
        { field: 'tags' as const, headerName: 'Tags', flex: 1 },
        { field: 'explanation' as const, headerName: 'Explanation', flex: 1 },
    ];

    const handleSearch = async (value: string) => {
        setLoading(true);
        try {
            const members = await searchMembers(value)
            setMemberOptions(members);
        } catch (e) {
            console.log(e)
            setMemberOptions([]);
        }
        setLoading(false);
    };

    useEffect(() => {
        if (searchValue.length > 1) {
            const timeout = setTimeout(() => handleSearch(searchValue), 300);
            return () => clearTimeout(timeout);
        }
    }, [searchValue]);

    const form = useAppForm({
        defaultValues: {
            questionIds: [],
            members: [],
            tutor: false,
        } as ExamFormValues,
        onSubmit: async ({ value }) => {
            const member_uuids = value.members.map((m) => m.uuid)
            try {
                await createAdminExam({
                    member_uuids,
                    question_ids: value.questionIds,
                    tutor: value.tutor,
                }, user?.email);
                setSuccessMsg('Exam created successfully!');
                setErrorMsg(null);
                // Explicitly clear UI/form selections, but ignore the programmatic grid
                // selection change so validation stays quiet until next user interaction.
                isClearingSelectionRef.current = true;
                gridApi?.deselectAll();
                form.reset();
                setSearchValue('');
                setMemberOptions([]);
            } catch (err) {
                if (err instanceof AxiosError)
                    setErrorMsg(err?.message || 'Failed to create exam.');
            }
        },
    })

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1>Create a new exam</h1>
            <form
                style={{ display: 'flex', flexDirection: 'column' }}
                onSubmit={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    form.handleSubmit()
                }}
                onReset={() => {
                    form.reset()
                    setSuccessMsg(null)
                    setErrorMsg(null)
                }}
                autoComplete='off'
            >
                <form.Field
                    name='questionIds'
                    validators={{ onChange: ({ value }) => value.length === 0 ? 'Select at least one question' : undefined }}
                    children={({ handleChange, state }) => (
                        <div style={{ marginBottom: 24 }}>
                            <label style={{ fontWeight: 600, marginBottom: 8, display: 'block' }}>
                                Select Questions
                                {state.meta.isTouched && state.meta.errors.length > 0 && (
                                    <span style={{ color: '#d32f2f', fontWeight: 400, marginLeft: 8, fontSize: 14 }}>
                                        {state.meta.errors[0]}
                                    </span>
                                )}
                            </label>
                            <div style={{ width: '100%', height: 500 }}>
                                <AgGridReact
                                    rowData={rowData}
                                    columnDefs={colDefs}
                                    defaultColDef={{
                                        filter: true,
                                        flex: 1,
                                        wrapText: true,
                                        autoHeight: true,
                                        cellStyle: {
                                            'wordBreak': 'normal',
                                            'lineHeight': 'unset',
                                            'padding': '10px'
                                        },
                                        minWidth: 100
                                    }}
                                    rowSelection={{
                                        mode: "multiRow",
                                    }}
                                    selectionColumnDef={{
                                        sortable: true,
                                        width: 80,
                                        suppressHeaderMenuButton: false,
                                    }}
                                    onGridReady={(params) => {
                                        setGridApi(params.api);
                                    }}
                                    onSelectionChanged={() => {
                                        if (isClearingSelectionRef.current) {
                                            isClearingSelectionRef.current = false;
                                            return;
                                        }
                                        const selectedData = gridApi?.getSelectedRows();
                                        const selectedIds = selectedData?.map((row) => row.id) ?? [];
                                        handleChange(selectedIds);
                                    }}
                                />
                            </div>
                        </div>
                    )}
                />
                <form.Field
                    name='members'
                    mode='array'
                    validators={{ onChange: ({ value }) => value.length === 0 ? 'Select at least one member' : undefined }}
                    children={({ state, handleChange }) => {
                        return (<Autocomplete
                            multiple
                            options={memberOptions}
                            getOptionLabel={(option) => option.email || option.name || ''}
                            filterOptions={(x) => x} // disable built-in filtering
                            loading={loading}
                            value={state.value}
                            noOptionsText={'No members found'}
                            onInputChange={(_, value) => setSearchValue(value)}
                            onChange={(_, value) => {
                                handleChange(value)
                            }}
                            renderInput={(params) => (
                                <TextField
                                    {...params}
                                    variant="outlined"
                                    label="Search Members"
                                    error={state.meta.isTouched && state.meta.errors.length > 0}
                                    helperText={state.meta.isTouched ? state.meta.errors[0] : undefined}
                                />
                            )}
                        />)
                    }} />
                <form.Field
                    name='tutor'
                    children={({ state, handleChange }) => (
                        <FormControlLabel
                            control={(
                                <Checkbox
                                    checked={state.value}
                                    onChange={(_, checked) => handleChange(checked)}
                                />
                            )}
                            label='Show correct answer and explanation after each answer submission?'
                        />
                    )}
                />
                <form.Subscribe
                    selector={(state) => [state.canSubmit, state.isSubmitting]}
                    children={([canSubmit, isSubmitting]) => (
                        <FormActionFooter
                            canSubmit={canSubmit}
                            isSubmitting={isSubmitting}
                            submitLabel="Submit"
                            successMessage={successMsg}
                            errorMessage={errorMsg}
                            onCloseSuccess={() => { setSuccessMsg(null) }}
                            onCloseError={() => { setErrorMsg(null) }}
                        />
                    )}
                />
            </form>
        </div>
    )
}
