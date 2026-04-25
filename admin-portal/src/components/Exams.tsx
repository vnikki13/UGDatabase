import { AgGridReact } from 'ag-grid-react';
import { useMemo } from 'react';
import type { ColDef, SpanRowsParams } from 'ag-grid-community';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from '@tanstack/react-router';


interface GridRow {
    id: string;
}

const customSpanFunc = ({ nodeA, nodeB }: SpanRowsParams) => {
    return nodeA?.data.id === nodeB?.data.id;
};

export function Exams() {
    const navigate = useNavigate();
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));

    const colDefs: ColDef<GridRow>[] = useMemo(() => {
        const columns: ColDef<GridRow>[] = [
            {
                field: 'id',
                spanRows: customSpanFunc,
                hide: isSmallScreen,
            }
        ];

        return columns;
    }, [isSmallScreen]);


    return (
        <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1.5, flexWrap: 'wrap' }}>
                <Typography variant="h4" component="h1">Admin Exams</Typography>
                <Button variant="contained" onClick={() => navigate({ to: '/exam' })}>
                    Add Admin Exam
                </Button>
            </Box>
            <Box sx={{ height: { xs: '65vh', md: 500 }, minHeight: 420, width: '100%' }}>
                <AgGridReact
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