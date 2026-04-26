import { AgGridReact, type CustomCellRendererProps } from 'ag-grid-react';
import { useMemo } from 'react';
import type { Question, Tag, AnswerChoice } from '../types';
import type { ColDef, SpanRowsParams } from 'ag-grid-community';
import { useQuery } from '@tanstack/react-query';
import { getQuestions } from '../api';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
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
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));

    const colDefs: ColDef<GridRow>[] = useMemo(() => {
        const columns: ColDef<GridRow>[] = [
            {
                field: 'id',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: "prompt",
                spanRows: customSpanFunc,
                flex: isSmallScreen ? 2 : 1,
                minWidth: isSmallScreen ? 180 : 120,
            },
            {
                field: "media_content_type",
                headerName: 'Media Content Type',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: "explanation",
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: "tags",
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: "answerText",
                headerName: "Answer Choice",
                flex: isSmallScreen ? 1.5 : 1,
                minWidth: isSmallScreen ? 160 : 120,
            },
            {
                field: "isCorrect",
                headerName: "Correct",
                cellRenderer: (params: CustomCellRendererProps) => params.value ? '✅' : '❌',
                width: isSmallScreen ? 90 : 110,
                minWidth: isSmallScreen ? 90 : 110,
                maxWidth: isSmallScreen ? 90 : 110,
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
                width: isSmallScreen ? 90 : 100,
                minWidth: isSmallScreen ? 90 : 100,
                pinned: isSmallScreen ? undefined : 'right',
                spanRows: customSpanFunc,
            },
        ];

        return columns;
    }, [isSmallScreen, navigate]);

    const { data: questions } = useQuery({
        queryKey: ['questions'],
        queryFn: async () => getQuestions(),
    })

    const questionCount = questions?.count ?? 0

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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1.5, flexWrap: 'wrap' }}>
                <Typography variant="h4" component="h1">
                    Questions ({questionCount})
                </Typography>
                <Button variant="contained" onClick={() => navigate({ to: '/question' })}>
                    Add Question
                </Button>
            </Box>
            <Box sx={{ height: { xs: '65vh', md: 500 }, minHeight: 420, width: '100%' }}>
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
                            'padding': isSmallScreen ? '8px' : '10px'
                        },
                        minWidth: isSmallScreen ? 90 : 100,
                        resizable: true,
                    }}
                    enableCellSpan={true}
                    enableCellTextSelection={true}
                    ensureDomOrder={true}
                    rowHeight={isSmallScreen ? 52 : 44}
                />
            </Box>
        </>
    )
}