import { createFileRoute } from '@tanstack/react-router'
import { useAppForm } from '../../hooks/questionForm';
import { Alert, Autocomplete, Button, TextField } from '@mui/material';
import { useState, useEffect, useMemo } from 'react';
import { getQuestions, searchMembers, createAdminExam } from '../../api';
import type { Member, Question, Tag } from '../../types';
import { useQuery } from '@tanstack/react-query';
import type { GridApi, ColDef } from 'ag-grid-community';
import { AgGridReact } from 'ag-grid-react';
import { AxiosError } from 'axios';

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
}

function RouteComponent() {
    const [memberOptions, setMemberOptions] = useState<Member[]>([]);
    const [searchValue, setSearchValue] = useState('');
    const [loading, setLoading] = useState(false);
    const [gridApi, setGridApi] = useState<GridApi<GridRow>>();
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
        } as ExamFormValues,
        onSubmit: async ({ value }) => {
            const member_uuids = value.members.map((m) => m.uuid)
            try {
                await createAdminExam({
                    member_uuids,
                    question_ids: value.questionIds,
                });
                setSuccessMsg('Exams created successfully!');
                gridApi?.deselectAll();
                form.reset();
            } catch (err) {
                if (err instanceof AxiosError)
                    setErrorMsg(err?.message || 'Failed to create exams.');
            }
        },
    })

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1>Create a new exam</h1>
            {successMsg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => { setSuccessMsg(null) }}>{successMsg}</Alert>}
            {errorMsg && <Alert severity="error" sx={{ mb: 2 }} onClose={() => { setErrorMsg(null) }}>{errorMsg}</Alert>}
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
                    children={({ handleChange }) => (
                        <div style={{ marginBottom: 24 }}>
                            <label style={{ fontWeight: 600, marginBottom: 8, display: 'block' }}>Select Questions</label>
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
                                />
                            )}
                        />)
                    }} />
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
            </form>
        </div>
    )
}
