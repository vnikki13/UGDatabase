import { AgGridReact, type CustomCellRendererProps } from 'ag-grid-react';
import { useMemo } from 'react';
import type { ColDef } from 'ag-grid-community';
import { useQuery } from '@tanstack/react-query';
import { getTags } from '../api';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from '@tanstack/react-router';
import type { TagWithId } from '../types';

interface GridRow {
    id: string;
    name: string;
    created_at: string;
    updated_at: string | null;
    edit: string;
}

export function Tags() {
    const navigate = useNavigate();
    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));

    const { data } = useQuery<TagWithId[]>({
        queryKey: ['tags'],
        queryFn: getTags,
    });

    const rowData: GridRow[] = useMemo(
        () => (data ?? []).map((t) => ({ id: t.id, name: t.name, created_at: t.created_at, updated_at: t.updated_at, edit: '' })),
        [data],
    );

    const tagCount = data?.length ?? 0;

    const colDefs: ColDef<GridRow>[] = useMemo(() => [
        {
            field: 'id',
            hide: isSmallScreen,
            flex: 1,
        },
        {
            field: 'name',
            flex: isSmallScreen ? 2 : 1,
            minWidth: 120,
        },
        {
            field: 'created_at',
            headerName: 'Created At',
            hide: isSmallScreen,
            flex: 1,
            minWidth: 160,
        },
        {
            field: 'updated_at',
            headerName: 'Updated At',
            hide: isSmallScreen,
            flex: 1,
            minWidth: 160,
        },
        {
            field: 'edit',
            headerName: 'Edit',
            cellRenderer: (params: CustomCellRendererProps) => (
                <Button
                    variant="outlined"
                    size="small"
                    onClick={() => navigate({ to: `/tag/${params.data.id}`, params: { tagId: params.data.id } })}
                >
                    Edit
                </Button>
            ),
            width: isSmallScreen ? 90 : 100,
            minWidth: isSmallScreen ? 90 : 100,
            maxWidth: 110,
            pinned: isSmallScreen ? undefined : 'right',
            sortable: false,
            filter: false,
        },
    ], [isSmallScreen, navigate]);

    return (
        <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1.5, flexWrap: 'wrap' }}>
                <Typography variant="h4" component="h1">Tags ({tagCount})</Typography>
                <Button variant="contained" onClick={() => navigate({ to: '/tag' })}>
                    Add Tag
                </Button>
            </Box>
            <Box sx={{ height: { xs: '65vh', md: 400 }, minHeight: 300, width: '100%' }}>
                <AgGridReact
                    columnDefs={colDefs}
                    rowData={rowData}
                    defaultColDef={{
                        filter: true,
                        flex: 1,
                        wrapText: true,
                        autoHeight: true,
                        cellStyle: {
                            wordBreak: 'normal',
                            lineHeight: 'unset',
                            padding: isSmallScreen ? '8px' : '10px',
                        },
                        minWidth: isSmallScreen ? 90 : 100,
                        resizable: true,
                    }}
                    enableCellTextSelection={true}
                    ensureDomOrder={true}
                    rowHeight={isSmallScreen ? 52 : 44}
                />
            </Box>
        </>
    );
}
