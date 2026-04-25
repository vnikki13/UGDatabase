import { AgGridReact, type CustomCellRendererProps } from 'ag-grid-react';
import { useMemo } from 'react';
import type { Question, Tag, AnswerChoice } from '../types';
import type { ColDef, SpanRowsParams } from 'ag-grid-community';
import { useQuery } from '@tanstack/react-query';
import { getQuestions } from '../api';
import Button from '@mui/material/Button';
import { useNavigate } from '@tanstack/react-router';


interface GridRow {
    id: string;
    prompt: string;
    media_content_type: string | null;
    explanation: string;
    tags: string;
    answerText: string;
    isCorrect: boolean;
    rowIndex: number;
    edit: string;
}

const customSpanFunc = ({ nodeA, nodeB }: SpanRowsParams) => {
    return nodeA?.data.id === nodeB?.data.id;
};

export function Questions() {
    const navigate = useNavigate();
    const colDefs: ColDef<GridRow>[] = [
        {
            field: 'id',
            spanRows: customSpanFunc,
        },
        {
            field: "prompt",
            spanRows: customSpanFunc,
        },
        {
            field: "media_content_type",
            headerName: 'Media Content Type',
            spanRows: customSpanFunc,
        },
        {
            field: "explanation",
            spanRows: customSpanFunc,
        },
        {
            field: "tags",
            spanRows: customSpanFunc,
        },
        {
            field: "answerText",
            headerName: "Answer Choice Text"
        },
        {
            field: "isCorrect",
            headerName: "Is Correct",
            cellRenderer: (params: CustomCellRendererProps) => params.value ? '✅' : '❌'
        },
        {
            field: 'edit',
            headerName: 'Edit',
            cellRenderer: (params: CustomCellRendererProps) => (
                <Button
                    variant="outlined"
                    size="small"
                    onClick={() => (
                        navigate({
                            to: `/question/${params.data.id}`,
                            params: { questionId: params.data.id }
                        })
                    )}
                >
                    Edit
                </Button>
            ),
            width: 100,
            pinned: 'right',
            spanRows: customSpanFunc,
        },
    ];

    const { data: questions } = useQuery({
        queryKey: ['questions'],
        queryFn: async () => getQuestions(),
    })

    // Transform data to flatten answer choices into rows
    const rowData = useMemo(() => {
        if (!questions?.data) return [];

        const flattenedRows: GridRow[] = [];

        questions.data.forEach((question: Question) => {
            const answerChoices = question.answerChoices || [];
            const tags = Array.isArray(question.tags)
                ? question.tags.map((tag: Tag) => tag.name || tag).join(', ')
                : question.tags;

            // Create a row for each answer choice
            answerChoices.forEach((choice: AnswerChoice, index: number) => {
                flattenedRows.push({
                    id: question.id,
                    prompt: question.prompt,
                    media_content_type: question.media_content_type,
                    explanation: question.explanation,
                    tags,
                    answerText: choice.text,
                    isCorrect: choice.is_correct,
                    rowIndex: index,
                    edit: '',
                });
            });
        });

        return flattenedRows;
    }, [questions]);

    return (
        <>
            <h1 style={{ justifySelf: 'center' }}>Questions</h1>
            <div style={{ height: 500 }}>
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
                    enableCellSpan={true}
                    enableCellTextSelection={true}
                    ensureDomOrder={true}
                />
            </div>
        </>
    )
}