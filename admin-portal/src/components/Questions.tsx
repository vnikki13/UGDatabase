import { AgGridReact, type CustomCellRendererProps } from 'ag-grid-react'; // React Data Grid Component
import { useMemo } from 'react';
import type { Question, Tag, AnswerChoice } from '../types';
import type { ColDef, SpanRowsParams } from 'ag-grid-community';
import { useQuery } from '@tanstack/react-query';
import { getQuestions } from '../api';

interface GridRow {
    id: string;
    prompt: string;
    media_storage_path: string | null;
    media_content_type: string | null;
    explanation: string;
    tags: string;
    answerText: string;
    isCorrect: boolean;
    rowIndex: number;
}

const customSpanFunc = ({ nodeA, nodeB }: SpanRowsParams) => {
    return nodeA?.data.id === nodeB?.data.id;
};

export function Questions() {
    const colDefs = useMemo<ColDef<GridRow>[]>(() => [
        {
            field: 'id',
            spanRows: customSpanFunc,
        },
        {
            field: "prompt",
            spanRows: customSpanFunc,
        },
        {
            field: "media_storage_path",
            headerName: 'Media Storage Path',
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
    ], []);

    const { data: questions} = useQuery({
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
                    media_storage_path: question.media_storage_path,
                    media_content_type: question.media_content_type,
                    explanation: question.explanation,
                    tags,
                    answerText: choice.text,
                    isCorrect: choice.is_correct,
                    rowIndex: index
                });
            });
        });

        return flattenedRows;
    }, [questions]);

    return (
        <>
            <h3>Questions</h3>
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
                        minWidth: 200
                        
                    }}
                    enableCellSpan={true}
                />
            </div>
        </>
    )
}