import { useFieldContext } from "../../hooks/questionForm"
import { FormControl, TextField as Text } from "@mui/material"


export function TextField({ label, isRequired = true }: { label: string, isRequired?: boolean }) {
    const field = useFieldContext<string>()
    const errorMessage = field.state.meta.errors.length > 0
        ? String(field.state.meta.errors[0])
        : undefined
    return (
        <FormControl sx={{ m: 1, width: 300 }}>
            <Text
                label={label}
                variant="outlined"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                multiline
                required={isRequired}
                error={!!errorMessage}
                helperText={errorMessage}
            />
        </FormControl>
    )
}