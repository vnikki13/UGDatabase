import { AgGridReact } from 'ag-grid-react';
import { useMemo } from 'react';
import type { ColDef, SpanRowsParams } from 'ag-grid-community';
import { useQuery } from '@tanstack/react-query';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from '@tanstack/react-router';
import { getAdminExams } from '../api';
import type { ExamSummary, Tag } from '../types';


interface GridRow {
    id: string;
    member_id: string;
    question_count: number;
    tags: string;
    filters: string;
    started_at: string;
    updated_at: string;
    completed_at: string;
}

const customSpanFunc = ({ nodeA, nodeB }: SpanRowsParams) => {
    return nodeA?.data.id === nodeB?.data.id;
};

export function Exams() {
    const navigate = useNavigate();
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));

    const { data: examList } = useQuery({
        queryKey: ['admin-exams'],
        queryFn: getAdminExams,
    });

    const examCount = examList?.count ?? 0;

    const colDefs: ColDef<GridRow>[] = useMemo(() => {
        const columns: ColDef<GridRow>[] = [
            {
                field: 'id',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
                minWidth: 220,
            },
            {
                field: 'member_id',
                headerName: 'Member',
                spanRows: customSpanFunc,
                flex: isSmallScreen ? 1.5 : 1,
                minWidth: isSmallScreen ? 180 : 160,
            },
            {
                field: 'question_count',
                headerName: 'Questions',
                spanRows: customSpanFunc,
                width: isSmallScreen ? 110 : 120,
                minWidth: isSmallScreen ? 110 : 120,
                maxWidth: isSmallScreen ? 110 : 120,
            },
            {
                field: 'tags',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: 'filters',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: 'started_at',
                headerName: 'Started',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: 'updated_at',
                headerName: 'Updated',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            },
            {
                field: 'completed_at',
                headerName: 'Completed',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            }
        ];

        return columns;
    }, [isSmallScreen]);

    const rowData = useMemo(() => {
        if (!examList?.exams) {
            return [];
        }

        return examList.exams.map((exam: ExamSummary) => ({
            id: exam.id,
            member_id: exam.member_id,
            question_count: exam.question_count,
            tags: Array.isArray(exam.tags) ? exam.tags.map((tag: Tag) => tag.name).join(', ') : '',
            filters: exam.filters?.join(', ') ?? '',
            started_at: exam.started_at ?? 'Not started',
            updated_at: exam.updated_at ?? 'Never',
            completed_at: exam.completed_at ?? 'Not completed',
        }));
    }, [examList]);


    return (
        <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1.5, flexWrap: 'wrap' }}>
                <Typography variant="h4" component="h1">Admin Exams ({examCount})</Typography>
                <Button variant="contained" onClick={() => navigate({ to: '/exam' })}>
                    Add Admin Exam
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